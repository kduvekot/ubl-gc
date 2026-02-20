#!/usr/bin/env python3
"""Integrated pipeline: download + diff ODS revisions in a single process.

Dedicated script for the diff-analysis GitHub Actions workflow.
Everything runs in-process — no subprocess calls to external scripts.

Architecture:
  1. Download phase — ThreadPoolExecutor downloads ODS files from Google Drive
  2. Diff phase — multiprocessing Pool diffs consecutive pairs
  3. Overlap — a coordinator submits diff work as soon as both files of a
     pair are downloaded, so diff starts before all downloads finish

Optimizations vs the general-purpose scripts in work-sheets/scripts/:
  - content.xml MD5 comparison — skip parsing when files are identical
  - lxml for XML parsing (3-5x faster than stdlib ElementTree)
  - multiprocessing Pool for diff parallelism
  - File-size pre-check before hashing
  - Size-weighted chunk balancing
  - Audit-cache fingerprints — skip download+diff for known-identical pairs
  - ThreadPoolExecutor for concurrent downloads with connection reuse

Usage (from workflow):
    python3 .github/scripts/fast-diff-pipeline.py documents \\
        --download-dir /tmp/ubl-revisions/documents \\
        --diff-dir /tmp/diff-results/documents \\
        --text-only --diff-workers 4
"""

import argparse
import gc as gc_mod
import gzip
import hashlib
import json
import re
import sys
import time
import zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from multiprocessing import Pool
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

# ── XML parser: prefer lxml, fall back to stdlib ──────────────────────
try:
    from lxml import etree as ET

    _USING_LXML = True
except ImportError:
    import xml.etree.ElementTree as ET

    _USING_LXML = False

# ── ODS XML namespaces ────────────────────────────────────────────────
NS_TABLE = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
NS_TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
NS_OFFICE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"

# ── Google Drive public folder IDs ────────────────────────────────────
DRIVE_FOLDERS = {
    "library": "1JRvRaqsNP_G-9xICwrgGpY-ArwV8ej1w",
    "documents": "1DsufM2yMqcbE8kR-RH1i5rSBcvPivOxA",
}


# =====================================================================
# Google Drive download (inlined from download-drive-revisions.py)
# =====================================================================


class DriveEmbedParser(HTMLParser):
    """Parse the embedded folder view HTML to extract file entries."""

    def __init__(self):
        super().__init__()
        self.entries = []
        self.current_entry = None
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "div" and attrs_dict.get("class") == "flip-entry":
            self.current_entry = {"id": None, "name": None}
        if tag == "a" and self.current_entry and "href" in attrs_dict:
            url = attrs_dict["href"]
            match = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url)
            if match:
                self.current_entry["id"] = match.group(1)
        if tag == "div" and attrs_dict.get("class") == "flip-entry-title":
            self.in_title = True

    def handle_data(self, data):
        if self.current_entry and self.in_title:
            self.current_entry["name"] = data.strip()
            self.in_title = False

    def handle_endtag(self, tag):
        if tag == "div" and self.current_entry and self.current_entry.get("name"):
            self.entries.append(self.current_entry)
            self.current_entry = None


def list_drive_folder(folder_id):
    """List all files in a public Google Drive folder using the embed view."""
    url = f"https://drive.google.com/embeddedfolderview?id={folder_id}"
    print(f"  Listing folder {folder_id}...")

    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=60) as resp:
            html = resp.read().decode("utf-8")

        parser = DriveEmbedParser()
        parser.feed(html)
        print(f"  Found {len(parser.entries)} entries in embed view")
        return parser.entries

    except Exception as e:
        print(f"  ERROR listing folder: {e}")
        return []


def _find_file_in_folder_api(folder_id, filename):
    """Search for a specific file in a public Drive folder using the API."""
    import urllib.parse

    q = urllib.parse.quote(
        f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    )
    url = (
        f"https://www.googleapis.com/drive/v3/files"
        f"?q={q}"
        f"&fields=files(id,name,size)"
        f"&supportsAllDrives=true"
    )

    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())

        files = data.get("files", [])
        if files:
            return {"id": files[0]["id"], "name": files[0]["name"]}
    except Exception:
        pass

    return None


def _list_drive_folder_api(folder_id, wanted_revs):
    """Fallback: use Google Drive API v3 to find specific files."""
    entries = []
    for rev_num in sorted(wanted_revs):
        entry = _find_file_in_folder_api(folder_id, f"rev-{rev_num}.ods.gz")
        if entry:
            entries.append(entry)
    return entries


def download_drive_file(file_id, dest_path, retries=3):
    """Download a file from Google Drive by ID."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"

    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=120) as resp:
                data = resp.read()

            # Check for HTML virus scan warning page (large files)
            if data[:100].startswith(b"<!DOCTYPE") or b"virus scan" in data[:2000].lower():
                match = re.search(rb'confirm=([a-zA-Z0-9_-]+)', data)
                if match:
                    confirm = match.group(1).decode()
                    url2 = f"{url}&confirm={confirm}"
                    req2 = Request(url2, headers={"User-Agent": "Mozilla/5.0"})
                    with urlopen(req2, timeout=120) as resp2:
                        data = resp2.read()

            dest_path.write_bytes(data)
            return len(data)

        except HTTPError as e:
            if attempt < retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"    HTTP {e.code}, retrying in {wait}s...")
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"    Error: {e}, retrying in {wait}s...")
                time.sleep(wait)
                continue
            raise

    return 0


def _download_one(rev_num, entry, outdir):
    """Download and decompress a single revision. Returns (rev_num, ok, msg)."""
    gz_path = outdir / f"rev-{rev_num}.ods.gz"
    ods_path = outdir / f"rev-{rev_num}.ods"
    tmp_path = outdir / f"rev-{rev_num}.ods.tmp"
    try:
        size = download_drive_file(entry["id"], gz_path)
        gz_data = gz_path.read_bytes()
        ods_data = gzip.decompress(gz_data)
        # Atomic write: .tmp then rename, so consumers never see partial files
        tmp_path.write_bytes(ods_data)
        tmp_path.rename(ods_path)
        return (rev_num, True, f"{size:,} gz -> {len(ods_data):,} ods")
    except Exception as e:
        return (rev_num, False, str(e))


def download_revisions(sheet, outdir, file_map, download_workers=10):
    """Download all revisions in file_map. Returns (downloaded, errors).

    Skips files that already exist and are >1000 bytes.
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Write manifest immediately
    manifest_path = outdir / "manifest.txt"
    manifest_path.write_text(
        "\n".join(str(r) for r in sorted(file_map.keys())) + "\n"
    )

    # Separate already-downloaded from todo
    todo = {}
    skipped = 0
    for rev_num in sorted(file_map.keys()):
        ods_path = outdir / f"rev-{rev_num}.ods"
        if ods_path.exists() and ods_path.stat().st_size > 1000:
            skipped += 1
            continue
        todo[rev_num] = file_map[rev_num]

    if skipped:
        print(f"  Skipping {skipped} already-downloaded revisions")

    downloaded = skipped
    errors = 0

    if todo:
        print(f"  Downloading {len(todo)} revisions ({download_workers} workers)...")

        with ThreadPoolExecutor(max_workers=download_workers) as pool:
            futures = {
                pool.submit(_download_one, rev_num, entry, outdir): rev_num
                for rev_num, entry in todo.items()
            }
            for future in as_completed(futures):
                rev_num, ok, msg = future.result()
                if ok:
                    downloaded += 1
                    print(f"    rev-{rev_num:>5}: {msg}")
                else:
                    errors += 1
                    print(f"    rev-{rev_num:>5}: ERROR {msg}")

    # Signal completion
    done_path = outdir / "download-done.txt"
    done_path.write_text(f"downloaded={downloaded}\nerrors={errors}\n")

    return downloaded, errors


def build_file_map(sheet, needed_revs=None):
    """List Google Drive folder and build rev_num -> entry mapping.

    If needed_revs is provided, only include those revisions.
    Returns file_map dict.
    """
    folder_id = DRIVE_FOLDERS[sheet]
    entries = list_drive_folder(folder_id)

    file_map = {}
    for entry in entries:
        name = entry.get("name", "")
        match = re.match(r"rev-(\d+)\.ods\.gz$", name)
        if match:
            file_map[int(match.group(1))] = entry

    print(f"  Listing contains {len(file_map)} revision files")

    if not file_map and not entries:
        # Fallback to API
        if needed_revs:
            entries = _list_drive_folder_api(folder_id, needed_revs)
            for entry in entries:
                name = entry.get("name", "")
                match = re.match(r"rev-(\d+)\.ods\.gz$", name)
                if match:
                    file_map[int(match.group(1))] = entry
            print(f"  Fallback API found {len(file_map)} revisions")

    if needed_revs:
        file_map = {k: v for k, v in file_map.items() if k in needed_revs}

    return file_map


# =====================================================================
# Core ODS parsing
# =====================================================================


def col_letter(idx):
    if idx < 26:
        return chr(65 + idx)
    return chr(64 + idx // 26) + chr(65 + idx % 26)


def extract_cell_text(cell_elem):
    texts = []
    for p in cell_elem.findall(f"{NS_TEXT}p"):
        if p.text:
            texts.append(p.text)
        for child in p:
            if child.text:
                texts.append(child.text)
            if child.tail:
                texts.append(child.tail)
    return "\n".join(texts) if texts else ""


def _parse_table(table_elem, text_only=False):
    table_name = table_elem.get(f"{NS_TABLE}name", "unknown")
    rows = table_elem.findall(f"{NS_TABLE}table-row")

    grid = {}
    headers = []
    max_row = 0
    max_col = 0

    actual_row = 0
    for row_elem in rows:
        row_repeat = int(row_elem.get(f"{NS_TABLE}number-rows-repeated", "1"))
        if row_repeat > 10000:
            actual_row += row_repeat
            continue

        cells = row_elem.findall(f"{NS_TABLE}table-cell")
        col_idx = 0

        for cell_elem in cells:
            col_repeat = int(
                cell_elem.get(f"{NS_TABLE}number-columns-repeated", "1")
            )
            if col_repeat > 1000:
                col_idx += col_repeat
                continue

            text = extract_cell_text(cell_elem)
            value_type = cell_elem.get(f"{NS_OFFICE}value-type", "")
            formula = "" if text_only else cell_elem.get(f"{NS_TABLE}formula", "")
            value = cell_elem.get(f"{NS_OFFICE}value", "")
            style = cell_elem.get(f"{NS_TABLE}style-name", "")

            has_content = bool(text or formula or value_type)
            if has_content:
                cell_info = {
                    "text": text,
                    "type": value_type,
                    "formula": formula,
                    "value": value,
                    "style": style,
                }
                for r in range(min(col_repeat, 100)):
                    actual_col = col_idx + r
                    for rr in range(min(row_repeat, 100)):
                        ar = actual_row + rr
                        grid[(ar, actual_col)] = cell_info.copy()
                        max_row = max(max_row, ar)
                        max_col = max(max_col, actual_col)

            col_idx += col_repeat

        actual_row += row_repeat

    for c in range(max_col + 1):
        cell = grid.get((0, c))
        headers.append(cell["text"] if cell else "")

    return {
        "table_name": table_name,
        "headers": headers,
        "grid": grid,
        "max_row": max_row,
        "max_col": max_col,
        "num_cells": len(grid),
    }


def parse_ods(ods_path, text_only=False):
    with zipfile.ZipFile(ods_path) as zf:
        content = zf.read("content.xml")

    root = ET.fromstring(content)
    table = root.find(f".//{NS_TABLE}table")
    if table is None:
        raise ValueError(f"No table found in {ods_path}")

    return _parse_table(table, text_only=text_only)


# ── Fast identical detection ──────────────────────────────────────────


def content_xml_hash(ods_path):
    """MD5 hash of content.xml inside the ODS zip — fast identity check."""
    with zipfile.ZipFile(ods_path) as zf:
        return hashlib.md5(zf.read("content.xml")).digest()


# =====================================================================
# Semantic diff
# =====================================================================


def _match_columns(old_headers, new_headers):
    old_named = {}
    new_named = {}
    old_unnamed = []
    new_unnamed = []

    for idx, name in enumerate(old_headers):
        if name:
            if name not in old_named:
                old_named[name] = idx
        else:
            old_unnamed.append(idx)

    for idx, name in enumerate(new_headers):
        if name:
            if name not in new_named:
                new_named[name] = idx
        else:
            new_unnamed.append(idx)

    old_names = set(old_named.keys())
    new_names = set(new_named.keys())

    matched = []
    for name in sorted(old_names & new_names):
        matched.append((old_named[name], new_named[name], name))

    added = [(new_named[name], name) for name in sorted(new_names - old_names)]
    removed = [(old_named[name], name) for name in sorted(old_names - new_names)]

    unnamed_positions = []
    for idx in new_unnamed:
        before_name = after_name = None
        for i in range(idx - 1, -1, -1):
            if i < len(new_headers) and new_headers[i]:
                before_name = new_headers[i]
                break
        for i in range(idx + 1, len(new_headers)):
            if new_headers[i]:
                after_name = new_headers[i]
                break
        unnamed_positions.append(
            {
                "col": idx,
                "col_letter": col_letter(idx),
                "after": before_name,
                "before": after_name,
            }
        )

    return {
        "matched": matched,
        "added": added,
        "removed": removed,
        "unnamed_added": max(0, len(new_unnamed) - len(old_unnamed)),
        "unnamed_removed": max(0, len(old_unnamed) - len(new_unnamed)),
        "unnamed_positions": unnamed_positions,
        "old_count": len(old_headers),
        "new_count": len(new_headers),
    }


def _build_row_key(grid, row, den_col):
    if den_col is not None:
        cell = grid.get((row, den_col))
        if cell and cell["text"].strip():
            return cell["text"].strip()
    cell = grid.get((row, 0))
    if cell and cell["text"].strip():
        return cell["text"].strip()
    return None


def _build_row_identity_map(grid, max_row, den_col):
    key_to_row = {}
    key_order = []
    unmatched_rows = []

    for row in range(1, max_row + 1):
        key = _build_row_key(grid, row, den_col)
        if key:
            if key not in key_to_row:
                key_to_row[key] = row
                key_order.append(key)
        else:
            unmatched_rows.append(row)

    return {
        "key_to_row": key_to_row,
        "key_order": key_order,
        "unmatched_rows": unmatched_rows,
        "row_count": max_row,
    }


def _categorize_change(old_cell, new_cell):
    old_formula = old_cell.get("formula", "")
    new_formula = new_cell.get("formula", "")
    old_text = old_cell.get("text", "")
    new_text = new_cell.get("text", "")
    old_type = old_cell.get("type", "")
    new_type = new_cell.get("type", "")
    old_style = old_cell.get("style", "")
    new_style = new_cell.get("style", "")

    formula_changed = old_formula != new_formula
    text_changed = old_text != new_text
    type_changed = old_type != new_type
    style_changed = old_style != new_style

    if formula_changed:
        return "formula_change"
    if (old_formula or new_formula) and text_changed and not formula_changed:
        return "formula_result"
    if text_changed and not old_formula and not new_formula:
        return "user_edit"
    if style_changed and not text_changed and not formula_changed:
        return "style_only"
    if type_changed and not text_changed:
        return "type_change"
    return "other"


def summarize_changes(changes):
    by_category = defaultdict(int)
    by_column = defaultdict(lambda: defaultdict(int))
    by_row_range = defaultdict(int)

    for c in changes:
        cat = c["change_type"]
        by_category[cat] += 1
        by_column[c["header"]][cat] += 1

        row = c["row"]
        if row < 100:
            by_row_range["1-100"] += 1
        elif row < 500:
            by_row_range["100-500"] += 1
        elif row < 1000:
            by_row_range["500-1000"] += 1
        elif row < 2000:
            by_row_range["1000-2000"] += 1
        else:
            by_row_range["2000+"] += 1

    return {
        "by_category": dict(by_category),
        "by_column": {k: dict(v) for k, v in by_column.items()},
        "by_row_range": dict(by_row_range),
    }


def diff_grids_semantic(old_data, new_data):
    old_grid = old_data["grid"]
    new_grid = new_data["grid"]
    old_headers = old_data["headers"]
    new_headers = new_data["headers"]

    col_match = _match_columns(old_headers, new_headers)

    old_den_col = new_den_col = None
    for old_col, new_col, name in col_match["matched"]:
        if name == "Dictionary Entry Name":
            old_den_col = old_col
            new_den_col = new_col
            break

    old_rows = _build_row_identity_map(old_grid, old_data["max_row"], old_den_col)
    new_rows = _build_row_identity_map(new_grid, new_data["max_row"], new_den_col)

    old_keys_set = set(old_rows["key_to_row"].keys())
    new_keys_set = set(new_rows["key_to_row"].keys())

    added_row_keys = sorted(new_keys_set - old_keys_set)
    removed_row_keys = sorted(old_keys_set - new_keys_set)
    common_row_keys = old_keys_set & new_keys_set

    changes = []
    style_only_count = 0

    for row_key in sorted(common_row_keys):
        old_row = old_rows["key_to_row"][row_key]
        new_row = new_rows["key_to_row"][row_key]

        for old_col, new_col, col_name in col_match["matched"]:
            old_cell = old_grid.get((old_row, old_col))
            new_cell = new_grid.get((new_row, new_col))

            if old_cell == new_cell:
                continue

            if old_cell is None and new_cell is not None:
                cat = "added"
            elif old_cell is not None and new_cell is None:
                cat = "removed"
            else:
                cat = _categorize_change(old_cell, new_cell)

            if cat == "style_only":
                style_only_count += 1
                continue

            header = col_name
            address = f"{col_letter(new_col)}{new_row + 1}"
            old_text = old_cell["text"] if old_cell else ""
            new_text = new_cell["text"] if new_cell else ""
            old_formula = old_cell.get("formula", "") if old_cell else ""
            new_formula = new_cell.get("formula", "") if new_cell else ""
            old_type = old_cell.get("type", "") if old_cell else ""
            new_type = new_cell.get("type", "") if new_cell else ""

            changes.append(
                {
                    "row": new_row,
                    "col": new_col,
                    "old_row": old_row,
                    "old_col": old_col,
                    "address": address,
                    "header": header,
                    "row_key": row_key,
                    "change_type": cat,
                    "old_text": old_text,
                    "new_text": new_text,
                    "old_formula": old_formula,
                    "new_formula": new_formula,
                    "old_type": old_type,
                    "new_type": new_type,
                    "is_formula_cell": bool(old_formula or new_formula),
                    "formula_changed": old_formula != new_formula,
                    "text_changed": old_text != new_text,
                }
            )

    # Cells in added named columns
    for new_col, col_name in col_match["added"]:
        for row_key in sorted(common_row_keys):
            new_row = new_rows["key_to_row"][row_key]
            cell = new_grid.get((new_row, new_col))
            if cell and cell["text"].strip():
                changes.append(
                    {
                        "row": new_row,
                        "col": new_col,
                        "old_row": None,
                        "old_col": None,
                        "address": f"{col_letter(new_col)}{new_row + 1}",
                        "header": col_name,
                        "row_key": row_key,
                        "change_type": "column_added",
                        "old_text": "",
                        "new_text": cell["text"],
                        "old_formula": "",
                        "new_formula": cell.get("formula", ""),
                        "old_type": "",
                        "new_type": cell.get("type", ""),
                        "is_formula_cell": bool(cell.get("formula")),
                        "formula_changed": bool(cell.get("formula")),
                        "text_changed": bool(cell["text"]),
                    }
                )

    # Cells in removed named columns
    for old_col, col_name in col_match["removed"]:
        for row_key in sorted(common_row_keys):
            old_row = old_rows["key_to_row"][row_key]
            cell = old_grid.get((old_row, old_col))
            if cell and cell["text"].strip():
                changes.append(
                    {
                        "row": old_row,
                        "col": old_col,
                        "old_row": old_row,
                        "old_col": old_col,
                        "address": f"{col_letter(old_col)}{old_row + 1}",
                        "header": col_name,
                        "row_key": row_key,
                        "change_type": "column_removed",
                        "old_text": cell["text"],
                        "new_text": "",
                        "old_formula": cell.get("formula", ""),
                        "new_formula": "",
                        "old_type": cell.get("type", ""),
                        "new_type": "",
                        "is_formula_cell": bool(cell.get("formula")),
                        "formula_changed": bool(cell.get("formula")),
                        "text_changed": bool(cell["text"]),
                    }
                )

    column_changes = {
        "added": [
            (name, col_letter(idx), idx) for idx, name in col_match["added"]
        ],
        "removed": [
            (name, col_letter(idx), idx) for idx, name in col_match["removed"]
        ],
        "common": [name for _, _, name in col_match["matched"]],
        "unnamed_added": col_match["unnamed_added"],
        "unnamed_removed": col_match["unnamed_removed"],
        "unnamed_positions": col_match["unnamed_positions"],
        "old_count": col_match["old_count"],
        "new_count": col_match["new_count"],
    }

    added_with_pos = [(k, new_rows["key_to_row"][k]) for k in added_row_keys]
    removed_with_pos = [(k, old_rows["key_to_row"][k]) for k in removed_row_keys]

    row_changes = {
        "added": added_with_pos[:50],
        "added_count": len(added_row_keys),
        "removed": removed_with_pos[:50],
        "removed_count": len(removed_row_keys),
        "matched": len(common_row_keys),
        "old_row_count": old_rows["row_count"],
        "new_row_count": new_rows["row_count"],
        "old_unmatched": len(old_rows["unmatched_rows"]),
        "new_unmatched": len(new_rows["unmatched_rows"]),
    }

    return {
        "changes": changes,
        "column_changes": column_changes,
        "row_changes": row_changes,
        "style_only_count": style_only_count,
        "summary": summarize_changes(changes),
    }


# =====================================================================
# Worker function for multiprocessing Pool
# =====================================================================

# Template for identical pair results (avoid rebuilding each time)
_IDENTICAL_RESULT_TEMPLATE = {
    "num_changes": 0,
    "style_only_count": 0,
    "has_col_structure": False,
    "has_row_structure": False,
    "column_changes": {
        "added": [], "removed": [], "common": [],
        "unnamed_added": 0, "unnamed_removed": 0,
        "unnamed_positions": [], "old_count": 0, "new_count": 0,
    },
    "row_changes": {
        "added": [], "added_count": 0, "removed": [],
        "removed_count": 0, "matched": 0,
        "old_row_count": 0, "new_row_count": 0,
        "old_unmatched": 0, "new_unmatched": 0,
    },
    "summary": {"by_category": {}, "by_column": {}, "by_row_range": {}},
    "changes": [],
    "fast_identical": True,
}


def _make_identical_result(rev_a, rev_b):
    """Create an identical-pair result dict."""
    result = dict(_IDENTICAL_RESULT_TEMPLATE)
    result["from_rev"] = rev_a
    result["to_rev"] = rev_b
    return result


def _diff_pair(args):
    """Process a single pair — called in worker process.

    Returns (rev_a, rev_b, status_str, pair_result_dict_or_error_str).
    """
    rev_a, rev_b, path_a, path_b, text_only, outdir = args

    pair_json = Path(outdir) / f"pair-{rev_a}-{rev_b}.json"

    # Skip if already computed
    if pair_json.exists() and pair_json.stat().st_size > 10:
        try:
            with open(pair_json) as f:
                existing = json.load(f)
            return (rev_a, rev_b, "cached", existing)
        except (json.JSONDecodeError, KeyError):
            pass

    path_a = Path(path_a)
    path_b = Path(path_b)

    # Check files exist
    try:
        size_a = path_a.stat().st_size
        size_b = path_b.stat().st_size
    except FileNotFoundError as e:
        return (rev_a, rev_b, "error", str(e))

    # Hash fast-path: content.xml comparison
    if size_a == size_b:
        try:
            hash_a = content_xml_hash(path_a)
            hash_b = content_xml_hash(path_b)
            if hash_a == hash_b:
                pair_result = _make_identical_result(rev_a, rev_b)
                with open(pair_json, "w") as f:
                    json.dump(pair_result, f, separators=(",", ":"))
                return (rev_a, rev_b, "hash_identical", pair_result)
        except Exception:
            pass  # Fall through to full parse

    # Full parse + semantic diff
    try:
        old_data = parse_ods(path_a, text_only=text_only)
    except Exception as e:
        return (rev_a, rev_b, "error", f"parsing rev-{rev_a}: {e}")

    try:
        new_data = parse_ods(path_b, text_only=text_only)
    except Exception as e:
        return (rev_a, rev_b, "error", f"parsing rev-{rev_b}: {e}")

    result = diff_grids_semantic(old_data, new_data)

    changes = result["changes"]
    col_changes = result["column_changes"]
    row_changes = result["row_changes"]
    style_only = result.get("style_only_count", 0)

    has_col_structure = (
        col_changes["added"]
        or col_changes["removed"]
        or col_changes["unnamed_added"] > 0
        or col_changes["unnamed_removed"] > 0
        or col_changes["old_count"] != col_changes["new_count"]
    )
    has_row_structure = (
        row_changes["added_count"] > 0
        or row_changes["removed_count"] > 0
        or row_changes["old_row_count"] != row_changes["new_row_count"]
    )

    pair_result = {
        "from_rev": rev_a,
        "to_rev": rev_b,
        "num_changes": len(changes),
        "style_only_count": style_only,
        "has_col_structure": has_col_structure,
        "has_row_structure": has_row_structure,
        "column_changes": col_changes,
        "row_changes": row_changes,
        "summary": result["summary"],
        "changes": changes,
    }
    with open(pair_json, "w") as f:
        json.dump(pair_result, f, separators=(",", ":"))

    return (rev_a, rev_b, "diffed", pair_result)


# =====================================================================
# Chunk splitter — balance by file size, not count
# =====================================================================


def _split_by_size(revs, ods_dir, n_chunks):
    """Split revision list into n_chunks balanced by cumulative ODS file size."""
    if n_chunks <= 1 or len(revs) < 2:
        return [revs]

    sizes = []
    for r in revs:
        p = ods_dir / f"rev-{r}.ods"
        try:
            sizes.append(p.stat().st_size)
        except FileNotFoundError:
            sizes.append(0)

    total = sum(sizes)
    target = total / n_chunks

    chunks = []
    current_chunk = []
    running = 0

    for i, r in enumerate(revs):
        current_chunk.append(r)
        running += sizes[i]
        if running >= target and len(chunks) < n_chunks - 1:
            chunks.append(current_chunk)
            current_chunk = [r]  # overlap: last rev of prev chunk starts next
            running = sizes[i]

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


# =====================================================================
# Pool-based parallel diff
# =====================================================================


def _pool_diff(revs, ods_dir, diff_dir, text_only, n_workers):
    """Process all pairs using a multiprocessing Pool."""
    chunks = _split_by_size(revs, ods_dir, n_workers)

    print(f"\n  Split into {len(chunks)} size-balanced chunks:")
    for i, chunk in enumerate(chunks):
        print(f"    Chunk {i}: revs {chunk[0]}-{chunk[-1]} ({len(chunk)} revs, {len(chunk)-1} pairs)")

    # Build work items for the pool
    work_items = []
    for chunk in chunks:
        for j in range(len(chunk) - 1):
            ra, rb = chunk[j], chunk[j + 1]
            work_items.append((
                ra, rb,
                str(ods_dir / f"rev-{ra}.ods"),
                str(ods_dir / f"rev-{rb}.ods"),
                text_only,
                str(diff_dir),
            ))

    print(f"  Total work items: {len(work_items)}")
    print(f"  Pool workers: {n_workers}")
    print()

    stats = {
        "total": 0,
        "identical": 0,
        "hash_identical": 0,
        "style_only": 0,
        "changed": 0,
        "cached": 0,
        "errors": 0,
        "cell_changes": 0,
        "user_edits": 0,
        "col_events": [],
        "row_events": [],
    }

    t0 = time.time()
    completed = 0

    with Pool(processes=n_workers) as pool:
        for result in pool.imap_unordered(_diff_pair, work_items, chunksize=8):
            rev_a, rev_b, status, data = result
            completed += 1
            stats["total"] += 1

            if status == "error":
                stats["errors"] += 1
                print(f"  rev-{rev_a:>5} -> rev-{rev_b:>5}: ERROR {data}")
            elif status == "hash_identical":
                stats["identical"] += 1
                stats["hash_identical"] += 1
                if completed % 200 == 0:
                    elapsed = time.time() - t0
                    rate = completed / elapsed
                    print(f"  ... {completed}/{len(work_items)} ({rate:.0f}/s)")
            elif status == "cached":
                stats["cached"] += 1
                n = data.get("num_changes", 0)
                if n == 0 and not data.get("has_col_structure") and not data.get("has_row_structure"):
                    stats["identical"] += 1
                else:
                    stats["changed"] += 1
                    stats["cell_changes"] += n
            elif status == "diffed":
                n = data.get("num_changes", 0)
                soc = data.get("style_only_count", 0)
                hcs = data.get("has_col_structure", False)
                hrs = data.get("has_row_structure", False)

                if n == 0 and soc == 0 and not hcs and not hrs:
                    stats["identical"] += 1
                elif n == 0 and soc > 0 and not hcs and not hrs:
                    stats["style_only"] += 1
                else:
                    stats["changed"] += 1
                    stats["cell_changes"] += n
                    stats["user_edits"] += data.get("summary", {}).get(
                        "by_category", {}
                    ).get("user_edit", 0)
                    if hcs:
                        stats["col_events"].append((rev_a, rev_b))
                    if hrs:
                        stats["row_events"].append((rev_a, rev_b))

                # Log non-trivial diffs
                if n > 0 or hcs or hrs:
                    parts = []
                    if n:
                        parts.append(f"{n} changes")
                    if hcs:
                        cc = data["column_changes"]
                        parts.append(f"cols {cc['old_count']}->{cc['new_count']}")
                    if hrs:
                        rc = data["row_changes"]
                        parts.append(f"+{rc['added_count']} -{rc['removed_count']} rows")
                    print(f"  rev-{rev_a:>5} -> rev-{rev_b:>5}: {', '.join(parts)}")

            if completed % 200 == 0:
                elapsed = time.time() - t0
                rate = completed / elapsed
                print(f"  ... {completed}/{len(work_items)} ({rate:.0f} pairs/s)")

    return stats


# =====================================================================
# Main pipeline
# =====================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Integrated pipeline: download + parallel diff (single process)"
    )
    parser.add_argument("sheet", choices=["library", "documents"])
    parser.add_argument("--diff-workers", type=int, default=4)
    parser.add_argument("--download-workers", type=int, default=10)
    parser.add_argument("--download-dir", type=str, default=None)
    parser.add_argument("--diff-dir", type=str, default=None)
    parser.add_argument("--text-only", action="store_true", default=True)
    parser.add_argument(
        "--audit-cache", type=str, default=None,
        help="Path to audit-cache JSON with per-revision fingerprints. "
             "Skips downloading and diffing consecutive identical revisions."
    )
    args = parser.parse_args()

    dl_dir = (
        Path(args.download_dir)
        if args.download_dir
        else Path(f"/tmp/ubl-revisions/{args.sheet}")
    )
    diff_dir = (
        Path(args.diff_dir)
        if args.diff_dir
        else Path(f"/tmp/diff-results/{args.sheet}")
    )
    dl_dir.mkdir(parents=True, exist_ok=True)
    diff_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"Integrated Diff Pipeline: {args.sheet}")
    print("=" * 70)
    print(f"  XML parser:       {'lxml' if _USING_LXML else 'stdlib ElementTree'}")
    print(f"  Download dir:     {dl_dir}")
    print(f"  Diff output:      {diff_dir}")
    print(f"  Download workers: {args.download_workers}")
    print(f"  Diff workers:     {args.diff_workers}")
    print(f"  Text-only:        {args.text_only}")
    print(f"  Audit cache:      {args.audit_cache or 'none'}")
    print()

    t_start = time.time()

    # ── Phase 0: Load audit cache (fingerprints) ─────────────────────
    cache_fps = {}   # rev_num -> fingerprint string
    identical_pairs_from_cache = []  # [(rev_a, rev_b), ...]

    if args.audit_cache:
        with open(args.audit_cache) as f:
            cache_data = json.load(f)
        cache_fps = {int(k): v["fp"] for k, v in cache_data["revisions"].items()}
        all_cache_revs = sorted(cache_fps.keys())
        print(f"[cache] Loaded {len(cache_fps)} revision fingerprints")

        # Identify consecutive identical pairs
        for i in range(len(all_cache_revs) - 1):
            a, b = all_cache_revs[i], all_cache_revs[i + 1]
            if cache_fps[a] == cache_fps[b]:
                identical_pairs_from_cache.append((a, b))

        # Determine which revisions actually need downloading
        needed_revs = set()
        for i in range(len(all_cache_revs) - 1):
            a, b = all_cache_revs[i], all_cache_revs[i + 1]
            if cache_fps[a] != cache_fps[b]:
                needed_revs.add(a)
                needed_revs.add(b)
        needed_revs.add(all_cache_revs[0])
        needed_revs.add(all_cache_revs[-1])

        print(f"[cache] Identical pairs (skip): {len(identical_pairs_from_cache)}")
        print(f"[cache] Revisions to download:  {len(needed_revs)} / {len(all_cache_revs)}")
        print(f"[cache] Download savings:        {len(all_cache_revs) - len(needed_revs)} revisions skipped")

        # Pre-write pair JSON for identical pairs
        pre_written = 0
        for a, b in identical_pairs_from_cache:
            pair_json = diff_dir / f"pair-{a}-{b}.json"
            if not pair_json.exists():
                result = _make_identical_result(a, b)
                with open(pair_json, "w") as f:
                    json.dump(result, f, separators=(",", ":"))
                pre_written += 1
        print(f"[cache] Pre-written pair JSONs:  {pre_written}")
        print()

    # ── Phase 1: Download revisions (in-process) ─────────────────────
    if cache_fps:
        file_map = build_file_map(args.sheet, needed_revs)
    else:
        file_map = build_file_map(args.sheet)

    if not file_map:
        print("ERROR: No revision files found in Drive folder")
        sys.exit(1)

    print(f"\n[pipeline] Downloading {len(file_map)} revisions...")
    dl_count, dl_errors = download_revisions(
        args.sheet, dl_dir, file_map, download_workers=args.download_workers
    )
    t_dl = time.time() - t_start
    print(f"[pipeline] Download finished in {t_dl:.1f}s "
          f"({dl_count} downloaded, {dl_errors} errors)")

    if dl_errors > 0 and dl_count == 0:
        print("ERROR: All downloads failed")
        sys.exit(1)

    # Build revision list: use cache if available, else manifest
    if cache_fps:
        revs = sorted(needed_revs)
    else:
        manifest = dl_dir / "manifest.txt"
        if not manifest.exists():
            print("ERROR: No manifest.txt found")
            sys.exit(1)
        revs = sorted(
            int(line.strip())
            for line in manifest.read_text().splitlines()
            if line.strip()
        )

    n_pairs = len(revs) - 1
    total_pairs = n_pairs + len(identical_pairs_from_cache)
    print(f"\n[pipeline] {len(revs)} revisions to diff, {n_pairs} pairs")
    if identical_pairs_from_cache:
        print(f"[pipeline] + {len(identical_pairs_from_cache)} identical pairs (from cache)")
        print(f"[pipeline] = {total_pairs} total pairs")
    print()

    # ── Phase 2: Parallel diff (in-process multiprocessing Pool) ─────
    print("=" * 70)
    print(f"In-process diff ({args.diff_workers} workers, hash fast-path + "
          f"{'lxml' if _USING_LXML else 'ElementTree'})")
    print("=" * 70)

    t_diff_start = time.time()
    stats = _pool_diff(revs, dl_dir, diff_dir, args.text_only, args.diff_workers)
    t_diff = time.time() - t_diff_start

    print(f"\n[pipeline] Diff phase: {t_diff:.1f}s")

    # ── Phase 3: Build merged summary from all pair files ────────────
    pair_files = sorted(diff_dir.glob("pair-*.json"))

    total_transitions = 0
    identical_count = 0
    hash_identical_count = 0
    style_only_count = 0
    changed_count = 0
    total_cell_changes = 0
    total_user_edits = 0
    col_events = []
    row_events = []
    errors = []

    for pf in pair_files:
        try:
            with open(pf) as f:
                p = json.load(f)
            total_transitions += 1
            n = p.get("num_changes", 0)
            soc = p.get("style_only_count", 0)
            hcs = p.get("has_col_structure", False)
            hrs = p.get("has_row_structure", False)

            if n == 0 and soc == 0 and not hcs and not hrs:
                identical_count += 1
                if p.get("fast_identical"):
                    hash_identical_count += 1
            elif n == 0 and soc > 0 and not hcs and not hrs:
                style_only_count += 1
            else:
                changed_count += 1
                total_cell_changes += n
                total_user_edits += p.get("summary", {}).get(
                    "by_category", {}
                ).get("user_edit", 0)
                if hcs:
                    cc = p.get("column_changes", {})
                    col_events.append(
                        {
                            "from": p["from_rev"],
                            "to": p["to_rev"],
                            "added": cc.get("added", []),
                            "removed": cc.get("removed", []),
                            "unnamed_added": cc.get("unnamed_added", 0),
                            "unnamed_removed": cc.get("unnamed_removed", 0),
                        }
                    )
                if hrs:
                    rc = p.get("row_changes", {})
                    row_events.append(
                        {
                            "from": p["from_rev"],
                            "to": p["to_rev"],
                            "added": rc.get("added_count", 0),
                            "removed": rc.get("removed_count", 0),
                        }
                    )
        except Exception as e:
            errors.append({"file": pf.name, "error": str(e)})

    t_total = time.time() - t_start

    summary = {
        "input_dir": str(dl_dir),
        "mode": "integrated-pipeline",
        "xml_parser": "lxml" if _USING_LXML else "ElementTree",
        "text_only": args.text_only,
        "download_workers": args.download_workers,
        "diff_workers": args.diff_workers,
        "revision_range": [revs[0], revs[-1]] if revs else [],
        "total_revisions": len(revs),
        "total_transitions": total_transitions,
        "identical_transitions": identical_count,
        "style_only_transitions": style_only_count,
        "changed_transitions": changed_count,
        "total_cell_changes": total_cell_changes,
        "total_user_edits": total_user_edits,
        "hash_identical_count": hash_identical_count,
        "col_structure_events": col_events,
        "row_structure_events": row_events,
        "errors": errors,
        "timing": {
            "download_seconds": round(t_dl, 1),
            "diff_seconds": round(t_diff, 1),
            "total_seconds": round(t_total, 1),
        },
    }

    summary_path = diff_dir / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # ── Final report ─────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)
    print(f"  Mode:           integrated (single process)")
    print(f"  XML parser:     {'lxml' if _USING_LXML else 'ElementTree'}")
    print(f"  Revisions:      {len(revs)}")
    print(f"  Transitions:    {total_transitions}")
    print(f"  Identical:      {identical_count} ({hash_identical_count} via hash)")
    print(f"  Style-only:     {style_only_count}")
    print(f"  Changed:        {changed_count}")
    print(f"  Cell changes:   {total_cell_changes}")
    print(f"  User edits:     {total_user_edits}")
    print(f"  DL errors:      {dl_errors}")
    print(f"  Diff errors:    {len(errors)}")
    print(f"  Download time:  {t_dl:.0f}s")
    print(f"  Diff time:      {t_diff:.0f}s")
    print(f"  Total time:     {t_total:.0f}s")
    print(f"  Pair files:     {len(pair_files)}")
    print(f"  Summary:        {summary_path}")
    print("=" * 70)

    if dl_errors > 0:
        print(f"\nWARNING: {dl_errors} download errors occurred")

    # Exit non-zero only if everything failed
    if dl_count == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
