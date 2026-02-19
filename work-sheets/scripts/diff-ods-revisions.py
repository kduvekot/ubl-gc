#!/usr/bin/env python3
"""
Diff consecutive ODS revision files to analyze cell-level changes.

Reads ODS (OpenDocument Spreadsheet) files exported from Google Sheets
revision history, extracts all cell data from the content.xml, and
compares consecutive revisions to show exactly what changed.

Default mode uses **semantic matching**: columns are matched by header name
and rows by Dictionary Entry Name, eliminating false changes from column/row
insertions. Use --positional to fall back to raw position-based comparison.

Supports multi-sheet ODS files (e.g. the documents sheet with 93+ worksheets).
Can operate in text-only mode to ignore formula reference shifts caused by
column/row insertions.

For each cell change, reports:
  - Cell address (e.g. A1, B42)
  - Column header name
  - Old value -> New value
  - Whether the cell has a formula
  - Whether it was likely a user edit vs formula/auto change

Usage:
    python3 diff-ods-revisions.py /tmp/ubl-revisions/library
    python3 diff-ods-revisions.py /tmp/ubl-revisions/library --range 1-10
    python3 diff-ods-revisions.py /tmp/ubl-revisions/library --verbose
    python3 diff-ods-revisions.py /tmp/ubl-revisions/library --text-only
    python3 diff-ods-revisions.py /tmp/ubl-revisions/library --positional
    python3 diff-ods-revisions.py /tmp/ubl-revisions/documents --all-sheets
    python3 diff-ods-revisions.py /tmp/ubl-revisions/library --json /tmp/diff-results.json

Expects files named rev-{N}.ods in the input directory.
"""

import argparse
import json
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

# ODS XML namespaces
NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
}

# Shorthand for namespace URIs used in element access
NS_TABLE = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
NS_TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
NS_OFFICE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"


def col_letter(idx):
    """Convert 0-based column index to Excel-style letter (A, B, ..., Z, AA, AB, ...)."""
    if idx < 26:
        return chr(65 + idx)
    return chr(64 + idx // 26) + chr(65 + idx % 26)


def extract_cell_text(cell_elem):
    """Extract all text content from a cell, including nested <text:p> elements."""
    texts = []
    for p in cell_elem.findall(f"{NS_TEXT}p"):
        # Get direct text
        if p.text:
            texts.append(p.text)
        # Get text from child elements (e.g. <text:span>)
        for child in p:
            if child.text:
                texts.append(child.text)
            if child.tail:
                texts.append(child.tail)
    return "\n".join(texts) if texts else ""


def _parse_table(table_elem, text_only=False):
    """Parse a single ODS table element and extract all cell data.

    Args:
        table_elem: XML element for the table
        text_only: if True, ignore formulas (only compare text content)

    Returns:
        dict with table_name, headers, grid, max_row, max_col, num_cells
    """
    table_name = table_elem.get(f"{NS_TABLE}name", "unknown")
    rows = table_elem.findall(f"{NS_TABLE}table-row")

    grid = {}  # (row_idx, col_idx) -> CellInfo dict
    headers = []
    max_row = 0
    max_col = 0

    actual_row = 0
    for row_elem in rows:
        row_repeat = int(row_elem.get(f"{NS_TABLE}number-rows-repeated", "1"))

        # Skip rows with huge repetition (empty spacer rows in Google Sheets)
        if row_repeat > 10000:
            actual_row += row_repeat
            continue

        cells = row_elem.findall(f"{NS_TABLE}table-cell")
        col_idx = 0

        for cell_elem in cells:
            col_repeat = int(cell_elem.get(f"{NS_TABLE}number-columns-repeated", "1"))

            # Skip cells with huge repetition (empty spacer columns)
            if col_repeat > 1000:
                col_idx += col_repeat
                continue

            # Extract cell data
            text = extract_cell_text(cell_elem)
            value_type = cell_elem.get(f"{NS_OFFICE}value-type", "")
            formula = "" if text_only else cell_elem.get(f"{NS_TABLE}formula", "")
            value = cell_elem.get(f"{NS_OFFICE}value", "")
            style = cell_elem.get(f"{NS_TABLE}style-name", "")

            # Only store non-empty cells
            has_content = bool(text or formula or value_type)

            if has_content:
                cell_info = {
                    "text": text,
                    "type": value_type,
                    "formula": formula,
                    "value": value,
                    "style": style,
                }

                # For repeated cells with content, store each instance
                for r in range(min(col_repeat, 100)):  # cap at 100 to avoid OOM
                    actual_col = col_idx + r
                    for rr in range(min(row_repeat, 100)):
                        ar = actual_row + rr
                        grid[(ar, actual_col)] = cell_info.copy()
                        max_row = max(max_row, ar)
                        max_col = max(max_col, actual_col)

            col_idx += col_repeat

        actual_row += row_repeat

    # Extract headers from row 0
    for c in range(max_col + 1):
        cell = grid.get((0, c))
        if cell:
            headers.append(cell["text"])
        else:
            headers.append("")

    return {
        "table_name": table_name,
        "headers": headers,
        "grid": grid,
        "max_row": max_row,
        "max_col": max_col,
        "num_cells": len(grid),
    }


def parse_ods(ods_path, text_only=False):
    """Parse an ODS file and extract cell data from the first table.

    Returns:
        dict with table_name, headers, grid, max_row, max_col, num_cells
    """
    with zipfile.ZipFile(ods_path) as zf:
        content = zf.read("content.xml")

    root = ET.fromstring(content)
    table = root.find(f".//{NS_TABLE}table")
    if table is None:
        raise ValueError(f"No table found in {ods_path}")

    return _parse_table(table, text_only=text_only)


def parse_ods_all_sheets(ods_path, text_only=False):
    """Parse an ODS file and extract cell data from ALL sheets.

    Returns:
        dict of sheet_name -> parsed data (same format as parse_ods)
    """
    with zipfile.ZipFile(ods_path) as zf:
        content = zf.read("content.xml")

    root = ET.fromstring(content)
    tables = root.findall(f".//{NS_TABLE}table")

    if not tables:
        raise ValueError(f"No tables found in {ods_path}")

    sheets = {}
    for table in tables:
        data = _parse_table(table, text_only=text_only)
        sheets[data["table_name"]] = data

    return sheets


def diff_grids(old_data, new_data):
    """Compare two parsed ODS grids and return all differences (positional).

    Returns a list of change dicts, each containing:
        - row, col: cell position
        - address: Excel-style address (e.g. "B42")
        - header: column header name
        - change_type: "added", "removed", "modified"
        - old_text, new_text: text values
        - old_formula, new_formula: formula strings
        - old_type, new_type: value types
        - is_formula_cell: whether either version has a formula
        - formula_changed: whether the formula itself changed
        - text_changed: whether the displayed text changed
        - change_category: "user_edit", "formula_result", "formula_change",
                           "style_only", "type_change"
    """
    old_grid = old_data["grid"]
    new_grid = new_data["grid"]
    headers = new_data["headers"] if new_data["headers"] else old_data["headers"]

    # All cell positions that exist in either grid
    all_positions = set(old_grid.keys()) | set(new_grid.keys())

    changes = []

    for (row, col) in sorted(all_positions):
        old_cell = old_grid.get((row, col))
        new_cell = new_grid.get((row, col))

        # Skip header row for diff purposes (report separately)
        if row == 0:
            if old_cell != new_cell:
                changes.append(_make_change(
                    row, col, headers, old_cell, new_cell, "header_change"
                ))
            continue

        if old_cell is None and new_cell is not None:
            changes.append(_make_change(row, col, headers, old_cell, new_cell, "added"))
        elif old_cell is not None and new_cell is None:
            changes.append(_make_change(row, col, headers, old_cell, new_cell, "removed"))
        elif old_cell != new_cell:
            # Determine what kind of change
            category = _categorize_change(old_cell, new_cell)
            changes.append(_make_change(row, col, headers, old_cell, new_cell, category))

    return changes


def _build_col_map(headers):
    """Build header_name -> col_index mapping, handling duplicates/empties.

    Empty/unnamed headers are stored as "(unnamed_N)" where N is the col index.
    """
    col_map = {}  # header_name -> col_index (first occurrence)
    for idx, name in enumerate(headers):
        key = name if name else f"(unnamed_{idx})"
        if key not in col_map:
            col_map[key] = idx
    return col_map


def _match_columns(old_headers, new_headers):
    """Match columns between two revisions using header names.

    Returns:
        matched: list of (old_col, new_col, header_name) for matched columns
        added: list of (new_col, header_name) for columns only in new
        removed: list of (old_col, header_name) for columns only in old
        unnamed_added: count of unnamed columns added
        unnamed_removed: count of unnamed columns removed
        unnamed_positions: list of positions where unnamed columns were inserted
    """
    # Build name -> index maps for named columns only
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

    added = []
    for name in sorted(new_names - old_names):
        added.append((new_named[name], name))

    removed = []
    for name in sorted(old_names - new_names):
        removed.append((old_named[name], name))

    # Figure out where unnamed columns were inserted by looking at gaps
    # between matched column positions
    unnamed_positions = []
    for idx in new_unnamed:
        # Find neighboring named columns in new
        before_name = None
        after_name = None
        for i in range(idx - 1, -1, -1):
            if i < len(new_headers) and new_headers[i]:
                before_name = new_headers[i]
                break
        for i in range(idx + 1, len(new_headers)):
            if new_headers[i]:
                after_name = new_headers[i]
                break
        unnamed_positions.append({
            "col": idx,
            "col_letter": col_letter(idx),
            "after": before_name,
            "before": after_name,
        })

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
    """Build a row identity key using Dictionary Entry Name column.

    Falls back to Component Name (col 0) if DEN not available.
    Returns None for empty/spacer rows.
    """
    # Try Dictionary Entry Name first (unique per component)
    if den_col is not None:
        cell = grid.get((row, den_col))
        if cell and cell["text"].strip():
            return cell["text"].strip()

    # Fallback: Component Name (col 0) — not unique but better than position
    cell = grid.get((row, 0))
    if cell and cell["text"].strip():
        return cell["text"].strip()

    return None


def _build_row_identity_map(grid, max_row, den_col):
    """Build row identity maps for all data rows.

    Returns:
        key_to_row: dict of identity_key -> row_index
        key_order: list of keys in original row order
        unmatched_rows: list of row indices with no identity key
        row_count: total data rows (excluding header)
    """
    key_to_row = {}
    key_order = []
    unmatched_rows = []

    for row in range(1, max_row + 1):
        key = _build_row_key(grid, row, den_col)
        if key:
            if key not in key_to_row:
                key_to_row[key] = row
                key_order.append(key)
            # Duplicate keys — keep first occurrence, note the duplicate
        else:
            unmatched_rows.append(row)

    return {
        "key_to_row": key_to_row,
        "key_order": key_order,
        "unmatched_rows": unmatched_rows,
        "row_count": max_row,  # data rows (max_row is 0-indexed, row 0 is header)
    }


def diff_grids_semantic(old_data, new_data):
    """Compare two ODS grids using semantic matching (by column name and row identity).

    Instead of comparing (row, col) positions directly, this:
    1. Matches columns by header name (handles column insertions/removals)
    2. Matches rows by Dictionary Entry Name (handles row insertions/removals)
    3. Reports structural changes (new/removed columns and rows) separately

    Returns a dict with:
        - changes: list of semantic change dicts
        - column_changes: dict describing column additions/removals/renames
        - row_changes: dict describing row additions/removals
        - summary: aggregated statistics
    """
    old_grid = old_data["grid"]
    new_grid = new_data["grid"]
    old_headers = old_data["headers"]
    new_headers = new_data["headers"]

    # Step 1: Match columns by header name
    col_match = _match_columns(old_headers, new_headers)

    # Step 2: Find Dictionary Entry Name column in both
    old_den_col = None
    new_den_col = None
    for old_col, new_col, name in col_match["matched"]:
        if name == "Dictionary Entry Name":
            old_den_col = old_col
            new_den_col = new_col
            break

    # Step 3: Build row identity maps
    old_rows = _build_row_identity_map(old_grid, old_data["max_row"], old_den_col)
    new_rows = _build_row_identity_map(new_grid, new_data["max_row"], new_den_col)

    old_keys_set = set(old_rows["key_to_row"].keys())
    new_keys_set = set(new_rows["key_to_row"].keys())

    added_row_keys = sorted(new_keys_set - old_keys_set)
    removed_row_keys = sorted(old_keys_set - new_keys_set)
    common_row_keys = old_keys_set & new_keys_set

    # Step 4: Compare cells in matched (row, column) pairs
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

            # Style-only changes are ODS export artifacts (internal style IDs
            # shift when columns are inserted/removed). Count them but don't
            # include in the main change list.
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

            changes.append({
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
            })

    # Step 5: Report cells in added named columns (for matched rows)
    for new_col, col_name in col_match["added"]:
        for row_key in sorted(common_row_keys):
            new_row = new_rows["key_to_row"][row_key]
            cell = new_grid.get((new_row, new_col))
            if cell and cell["text"].strip():
                changes.append({
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
                })

    # Step 6: Report cells in removed named columns (for matched rows)
    for old_col, col_name in col_match["removed"]:
        for row_key in sorted(common_row_keys):
            old_row = old_rows["key_to_row"][row_key]
            cell = old_grid.get((old_row, old_col))
            if cell and cell["text"].strip():
                changes.append({
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
                })

    column_changes = {
        "added": [(name, col_letter(idx), idx) for idx, name in col_match["added"]],
        "removed": [(name, col_letter(idx), idx) for idx, name in col_match["removed"]],
        "common": [name for _, _, name in col_match["matched"]],
        "unnamed_added": col_match["unnamed_added"],
        "unnamed_removed": col_match["unnamed_removed"],
        "unnamed_positions": col_match["unnamed_positions"],
        "old_count": col_match["old_count"],
        "new_count": col_match["new_count"],
    }

    # Include row positions for added/removed rows
    added_with_pos = [(k, new_rows["key_to_row"][k]) for k in added_row_keys]
    removed_with_pos = [(k, old_rows["key_to_row"][k]) for k in removed_row_keys]

    row_changes = {
        "added": added_with_pos[:50],  # cap display for very large lists
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


def _make_change(row, col, headers, old_cell, new_cell, category):
    """Build a change record."""
    header = headers[col] if col < len(headers) else f"col_{col}"
    address = f"{col_letter(col)}{row + 1}"

    old_text = old_cell["text"] if old_cell else ""
    new_text = new_cell["text"] if new_cell else ""
    old_formula = old_cell.get("formula", "") if old_cell else ""
    new_formula = new_cell.get("formula", "") if new_cell else ""
    old_type = old_cell.get("type", "") if old_cell else ""
    new_type = new_cell.get("type", "") if new_cell else ""

    is_formula = bool(old_formula or new_formula)
    formula_changed = old_formula != new_formula
    text_changed = old_text != new_text

    return {
        "row": row,
        "col": col,
        "address": address,
        "header": header,
        "change_type": category,
        "old_text": old_text,
        "new_text": new_text,
        "old_formula": old_formula,
        "new_formula": new_formula,
        "old_type": old_type,
        "new_type": new_type,
        "is_formula_cell": is_formula,
        "formula_changed": formula_changed,
        "text_changed": text_changed,
    }


def _categorize_change(old_cell, new_cell):
    """Categorize the type of change between two cell versions."""
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

    # Case 1: Formula itself changed (user edited the formula)
    if formula_changed:
        return "formula_change"

    # Case 2: Has formula, only the computed result changed
    if (old_formula or new_formula) and text_changed and not formula_changed:
        return "formula_result"

    # Case 3: No formula, text changed -> direct user edit
    if text_changed and not old_formula and not new_formula:
        return "user_edit"

    # Case 4: Only style changed
    if style_changed and not text_changed and not formula_changed:
        return "style_only"

    # Case 5: Only type changed
    if type_changed and not text_changed:
        return "type_change"

    # Fallback
    return "other"


def format_change(change, verbose=False):
    """Format a single change for display."""
    addr = change["address"]
    header = change["header"]
    cat = change["change_type"]

    # Truncate long texts
    def trunc(s, maxlen=60):
        s = s.replace("\n", "\\n")
        if len(s) > maxlen:
            return s[:maxlen-3] + "..."
        return s

    old_t = trunc(change["old_text"])
    new_t = trunc(change["new_text"])

    # Color-code by category
    cat_label = {
        "user_edit": "USER EDIT",
        "formula_result": "FORMULA RESULT",
        "formula_change": "FORMULA CHANGED",
        "style_only": "STYLE ONLY",
        "type_change": "TYPE CHANGE",
        "added": "ADDED",
        "removed": "REMOVED",
        "header_change": "HEADER CHANGE",
        "column_added": "COL ADDED",
        "column_removed": "COL REMOVED",
        "row_added": "ROW ADDED",
        "row_removed": "ROW REMOVED",
        "other": "OTHER",
    }.get(cat, cat.upper())

    line = f"  {addr:>6} ({header:>30}): [{cat_label:>16}]"

    if change["text_changed"]:
        line += f'  "{old_t}" -> "{new_t}"'
    elif cat == "style_only":
        line += f'  (text unchanged: "{old_t}")'

    if verbose and change["formula_changed"]:
        old_f = trunc(change["old_formula"], 80)
        new_f = trunc(change["new_formula"], 80)
        line += f"\n         formula: {old_f} -> {new_f}"

    return line


def summarize_changes(changes):
    """Create a summary of changes by category and column."""
    by_category = defaultdict(int)
    by_column = defaultdict(lambda: defaultdict(int))
    by_row_range = defaultdict(int)

    for c in changes:
        cat = c["change_type"]
        by_category[cat] += 1
        by_column[c["header"]][cat] += 1

        # Bucket rows
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


def diff_all_sheets(old_sheets, new_sheets):
    """Compare all sheets between two ODS files.

    Args:
        old_sheets: dict of sheet_name -> parsed data
        new_sheets: dict of sheet_name -> parsed data

    Returns:
        dict with:
            per_sheet: dict of sheet_name -> {changes, summary}
            added_sheets: list of sheet names only in new
            removed_sheets: list of sheet names only in old
            unchanged_sheets: list of sheet names with zero changes
            changed_sheets: list of sheet names with changes
            total_changes: total across all sheets
    """
    old_names = set(old_sheets.keys())
    new_names = set(new_sheets.keys())

    added_sheets = sorted(new_names - old_names)
    removed_sheets = sorted(old_names - new_names)
    common_sheets = sorted(old_names & new_names)

    per_sheet = {}
    unchanged_sheets = []
    changed_sheets = []
    total_changes = 0

    for name in common_sheets:
        changes = diff_grids(old_sheets[name], new_sheets[name])
        summary = summarize_changes(changes)
        per_sheet[name] = {"changes": changes, "summary": summary}
        total_changes += len(changes)
        if changes:
            changed_sheets.append(name)
        else:
            unchanged_sheets.append(name)

    # For added sheets, all cells are "added"
    for name in added_sheets:
        data = new_sheets[name]
        changes = []
        for (row, col), cell in sorted(data["grid"].items()):
            if row == 0:
                continue
            header = data["headers"][col] if col < len(data["headers"]) else f"col_{col}"
            changes.append({
                "row": row, "col": col,
                "address": f"{col_letter(col)}{row + 1}",
                "header": header,
                "change_type": "added",
                "old_text": "", "new_text": cell["text"],
                "old_formula": "", "new_formula": cell.get("formula", ""),
                "old_type": "", "new_type": cell.get("type", ""),
                "is_formula_cell": bool(cell.get("formula")),
                "formula_changed": bool(cell.get("formula")),
                "text_changed": bool(cell["text"]),
            })
        summary = summarize_changes(changes)
        per_sheet[name] = {"changes": changes, "summary": summary}
        total_changes += len(changes)

    return {
        "per_sheet": per_sheet,
        "added_sheets": added_sheets,
        "removed_sheets": removed_sheets,
        "unchanged_sheets": unchanged_sheets,
        "changed_sheets": changed_sheets,
        "total_changes": total_changes,
    }


def _run_single_sheet_mode(args, indir, ods_files, all_revs):
    """Original single-sheet diff mode."""
    text_only = args.text_only

    print("Parsing ODS files...")
    parsed = {}
    for rev_num in all_revs:
        path = ods_files[rev_num]
        print(f"  rev-{rev_num:>5}: parsing...", end="", flush=True)
        try:
            data = parse_ods(path, text_only=text_only)
            parsed[rev_num] = data
            print(f" {data['num_cells']} cells, {data['max_row']+1} rows, "
                  f"{data['max_col']+1} cols ({data['table_name']})")
        except Exception as e:
            print(f" ERROR: {e}")

    # Show header row for context
    if parsed:
        first_rev = min(parsed.keys())
        headers = parsed[first_rev]["headers"]
        print(f"\nColumn headers (from rev-{first_rev}):")
        for i, h in enumerate(headers):
            if h:
                print(f"  {col_letter(i):>3} ({i:2d}): {h}")

    # Compare consecutive pairs
    print()
    print("=" * 80)
    print("Comparing consecutive revisions")
    print("=" * 80)

    all_results = []
    total_changes = 0
    total_user_edits = 0
    total_formula_results = 0
    total_formula_changes = 0

    for i in range(len(all_revs) - 1):
        rev_a = all_revs[i]
        rev_b = all_revs[i + 1]

        if rev_a not in parsed or rev_b not in parsed:
            continue

        changes = diff_grids(parsed[rev_a], parsed[rev_b])

        result = {
            "from_rev": rev_a,
            "to_rev": rev_b,
            "num_changes": len(changes),
            "changes": changes,
            "summary": summarize_changes(changes),
        }
        all_results.append(result)

        # Display
        if not changes:
            if args.show_unchanged:
                print(f"\nrev-{rev_a} -> rev-{rev_b}: IDENTICAL (no changes)")
            continue

        _display_transition(result, args)

        # Accumulate totals
        cats = result["summary"]["by_category"]
        total_changes += len(changes)
        total_user_edits += cats.get("user_edit", 0)
        total_formula_results += cats.get("formula_result", 0)
        total_formula_changes += cats.get("formula_change", 0)

    _display_overall_summary(all_results, total_changes, total_user_edits,
                             total_formula_results, total_formula_changes)

    if args.json:
        _write_json(args.json, indir, all_revs, all_results, total_changes,
                     total_user_edits, total_formula_results, total_formula_changes)


def _run_all_sheets_mode(args, indir, ods_files, all_revs):
    """Multi-sheet diff mode for ODS files with multiple worksheets."""
    text_only = args.text_only

    print("Parsing ODS files (all sheets)...")
    parsed = {}
    for rev_num in all_revs:
        path = ods_files[rev_num]
        print(f"  rev-{rev_num:>5}: parsing...", end="", flush=True)
        try:
            sheets = parse_ods_all_sheets(path, text_only=text_only)
            parsed[rev_num] = sheets
            total_cells = sum(s["num_cells"] for s in sheets.values())
            print(f" {len(sheets)} sheets, {total_cells} total cells")
        except Exception as e:
            print(f" ERROR: {e}")

    if not parsed:
        print("ERROR: No files parsed successfully")
        return

    # Show sheet listing from first revision
    first_rev = min(parsed.keys())
    first_sheets = parsed[first_rev]
    print(f"\nSheets in rev-{first_rev} ({len(first_sheets)}):")
    for name, data in sorted(first_sheets.items()):
        print(f"  {name:>40}: {data['max_row']+1:5d} rows, "
              f"{data['max_col']+1:3d} cols, {data['num_cells']:5d} cells")

    # Compare consecutive pairs
    print()
    print("=" * 80)
    print("Comparing consecutive revisions (all sheets)")
    print("=" * 80)

    all_results = []
    grand_total = 0

    for i in range(len(all_revs) - 1):
        rev_a = all_revs[i]
        rev_b = all_revs[i + 1]

        if rev_a not in parsed or rev_b not in parsed:
            continue

        result = diff_all_sheets(parsed[rev_a], parsed[rev_b])
        result["from_rev"] = rev_a
        result["to_rev"] = rev_b
        all_results.append(result)

        if result["total_changes"] == 0 and not result["added_sheets"] and not result["removed_sheets"]:
            if args.show_unchanged:
                print(f"\nrev-{rev_a} -> rev-{rev_b}: ALL SHEETS IDENTICAL")
            continue

        grand_total += result["total_changes"]

        print(f"\n{'─'*80}")
        print(f"rev-{rev_a} -> rev-{rev_b}: {result['total_changes']} changes "
              f"across {len(result['changed_sheets'])} sheets")

        if result["added_sheets"]:
            print(f"  NEW SHEETS: {', '.join(result['added_sheets'])}")
        if result["removed_sheets"]:
            print(f"  REMOVED SHEETS: {', '.join(result['removed_sheets'])}")
        if result["unchanged_sheets"]:
            print(f"  Unchanged: {len(result['unchanged_sheets'])} sheets")

        # Show per-sheet change counts for changed sheets
        for sheet_name in result["changed_sheets"]:
            sheet_data = result["per_sheet"][sheet_name]
            n = len(sheet_data["changes"])
            cats = sheet_data["summary"]["by_category"]
            parts = [f"{k}={v}" for k, v in sorted(cats.items())]
            print(f"    {sheet_name:>40}: {n:5d} changes ({', '.join(parts)})")

        # Show per-sheet changes for added sheets (summary only)
        for sheet_name in result["added_sheets"]:
            if sheet_name in result["per_sheet"]:
                n = len(result["per_sheet"][sheet_name]["changes"])
                print(f"    {sheet_name:>40}: {n:5d} cells (new sheet)")

        # Show detailed changes if requested (up to limit across all sheets)
        if args.verbose:
            shown = 0
            for sheet_name in result["changed_sheets"] + result["added_sheets"]:
                if sheet_name not in result["per_sheet"]:
                    continue
                changes = result["per_sheet"][sheet_name]["changes"]
                if not changes:
                    continue

                # Prioritize user edits
                priority = {
                    "user_edit": 0, "header_change": 1, "formula_change": 2,
                    "added": 3, "removed": 4, "formula_result": 5,
                    "style_only": 6, "type_change": 7, "other": 8,
                }
                sorted_changes = sorted(changes, key=lambda c: (
                    priority.get(c["change_type"], 99), c["row"], c["col"]
                ))

                for change in sorted_changes:
                    if shown >= args.max_changes:
                        break
                    print(f"    [{sheet_name}] {format_change(change, verbose=True)}")
                    shown += 1

                if shown >= args.max_changes:
                    break

            if shown >= args.max_changes and grand_total > shown:
                print(f"    ... and more (use --max-changes to see more)")

    # Overall summary
    print()
    print("=" * 80)
    print("MULTI-SHEET OVERALL SUMMARY")
    print("=" * 80)
    print(f"  Transitions analyzed: {len(all_results)}")
    identical = sum(1 for r in all_results if r["total_changes"] == 0
                    and not r["added_sheets"] and not r["removed_sheets"])
    changed = len(all_results) - identical
    print(f"  Identical transitions: {identical}")
    print(f"  Changed transitions:   {changed}")
    print(f"  Total cell changes:    {grand_total}")

    # Aggregate per-sheet stats
    sheet_change_counts = defaultdict(int)
    for r in all_results:
        for sheet_name, sheet_data in r["per_sheet"].items():
            sheet_change_counts[sheet_name] += len(sheet_data["changes"])

    if sheet_change_counts:
        print(f"\n  Changes per sheet (top 20):")
        for name, count in sorted(sheet_change_counts.items(), key=lambda x: -x[1])[:20]:
            print(f"    {name:>40}: {count:5d}")

    # Write JSON
    if args.json:
        json_output = {
            "input_dir": str(indir),
            "mode": "all_sheets",
            "text_only": text_only,
            "revisions": all_revs,
            "transitions": [],
        }
        for r in all_results:
            t = {
                "from_rev": r["from_rev"],
                "to_rev": r["to_rev"],
                "total_changes": r["total_changes"],
                "added_sheets": r["added_sheets"],
                "removed_sheets": r["removed_sheets"],
                "changed_sheets": r["changed_sheets"],
                "unchanged_sheets_count": len(r["unchanged_sheets"]),
                "per_sheet_summary": {},
            }
            for name, data in r["per_sheet"].items():
                t["per_sheet_summary"][name] = {
                    "num_changes": len(data["changes"]),
                    "summary": data["summary"],
                }
            json_output["transitions"].append(t)

        json_path = Path(args.json)
        with open(json_path, "w") as f:
            json.dump(json_output, f, indent=2)
        print(f"\n  JSON results: {json_path}")


def _display_transition(result, args):
    """Display a single transition's changes."""
    rev_a = result["from_rev"]
    rev_b = result["to_rev"]
    changes = result["changes"]
    cats = result["summary"]["by_category"]

    user_edits = cats.get("user_edit", 0)
    formula_results = cats.get("formula_result", 0)
    formula_changes = cats.get("formula_change", 0)
    style_changes = cats.get("style_only", 0)
    added = cats.get("added", 0)
    removed = cats.get("removed", 0)

    print(f"\n{'─'*80}")
    print(f"rev-{rev_a} -> rev-{rev_b}: {len(changes)} changes")
    print(f"  User edits: {user_edits}  |  Formula results: {formula_results}  |  "
          f"Formula changes: {formula_changes}")
    if style_changes:
        print(f"  Style changes: {style_changes}")
    if added or removed:
        print(f"  Added: {added}  |  Removed: {removed}")

    # Show by column
    by_col = result["summary"]["by_column"]
    if by_col:
        print(f"\n  Changes by column:")
        for col_name in sorted(by_col.keys(), key=lambda x: (x == "", x)):
            col_cats = by_col[col_name]
            parts = []
            for cat, count in sorted(col_cats.items()):
                parts.append(f"{cat}={count}")
            label = col_name if col_name else "(empty header)"
            print(f"    {label:>35}: {', '.join(parts)}")

    # Show individual changes (up to limit)
    print(f"\n  Changes (showing {min(len(changes), args.max_changes)}"
          f"/{len(changes)}):")

    priority = {
        "user_edit": 0, "header_change": 1, "formula_change": 2,
        "added": 3, "removed": 4, "formula_result": 5,
        "style_only": 6, "type_change": 7, "other": 8,
    }
    sorted_changes = sorted(changes, key=lambda c: (
        priority.get(c["change_type"], 99), c["row"], c["col"]
    ))

    shown = 0
    for change in sorted_changes:
        if shown >= args.max_changes:
            remaining = len(changes) - shown
            print(f"  ... and {remaining} more changes")
            break
        print(format_change(change, verbose=args.verbose))
        shown += 1


def _display_overall_summary(all_results, total_changes, total_user_edits,
                              total_formula_results, total_formula_changes):
    """Display overall summary for single-sheet mode."""
    print()
    print("=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    print(f"  Revisions compared: {len(all_results)} transitions")
    identical = sum(1 for r in all_results if r["num_changes"] == 0)
    changed = sum(1 for r in all_results if r["num_changes"] > 0)
    print(f"  Identical transitions: {identical}")
    print(f"  Changed transitions:   {changed}")
    print(f"  Total cell changes:    {total_changes}")
    print(f"    User edits:          {total_user_edits}")
    print(f"    Formula results:     {total_formula_results}")
    print(f"    Formula changes:     {total_formula_changes}")

    if total_changes > 0:
        user_pct = 100 * total_user_edits / total_changes
        formula_pct = 100 * (total_formula_results + total_formula_changes) / total_changes
        print(f"\n  User edits:     {user_pct:.1f}% of all changes")
        print(f"  Formula-driven: {formula_pct:.1f}% of all changes")

    # Pattern analysis: which columns get edited most?
    global_col_counts = defaultdict(int)
    global_col_user_edits = defaultdict(int)
    for r in all_results:
        for c in r["changes"]:
            global_col_counts[c["header"]] += 1
            if c["change_type"] == "user_edit":
                global_col_user_edits[c["header"]] += 1

    if global_col_counts:
        print(f"\n  Most-changed columns (all types):")
        for col, count in sorted(global_col_counts.items(), key=lambda x: -x[1])[:10]:
            label = col if col else "(empty)"
            user = global_col_user_edits.get(col, 0)
            print(f"    {label:>35}: {count:4d} total ({user} user edits)")


def _write_json(json_path, indir, all_revs, all_results, total_changes,
                total_user_edits, total_formula_results, total_formula_changes):
    """Write JSON results for single-sheet mode."""
    identical = sum(1 for r in all_results if r["num_changes"] == 0)
    changed = sum(1 for r in all_results if r["num_changes"] > 0)

    json_output = {
        "input_dir": str(indir),
        "revisions": all_revs,
        "transitions": [
            {
                "from_rev": r["from_rev"],
                "to_rev": r["to_rev"],
                "num_changes": r["num_changes"],
                "summary": r["summary"],
                "changes": [
                    {k: v for k, v in c.items()}
                    for c in r["changes"]
                ],
            }
            for r in all_results
        ],
        "overall": {
            "total_transitions": len(all_results),
            "identical_transitions": identical,
            "changed_transitions": changed,
            "total_changes": total_changes,
            "user_edits": total_user_edits,
            "formula_results": total_formula_results,
            "formula_changes": total_formula_changes,
        },
    }

    jp = Path(json_path)
    with open(jp, "w") as f:
        json.dump(json_output, f, indent=2)
    print(f"\n  JSON results: {jp}")


def _run_semantic_mode(args, indir, ods_files, all_revs):
    """Semantic diff mode: match columns by name and rows by identity."""
    text_only = args.text_only

    print("Parsing ODS files...")
    parsed = {}
    for rev_num in all_revs:
        path = ods_files[rev_num]
        print(f"  rev-{rev_num:>5}: parsing...", end="", flush=True)
        try:
            data = parse_ods(path, text_only=text_only)
            parsed[rev_num] = data
            print(f" {data['num_cells']} cells, {data['max_row']+1} rows, "
                  f"{data['max_col']+1} cols ({data['table_name']})")
        except Exception as e:
            print(f" ERROR: {e}")

    # Show header rows for context
    if parsed:
        first_rev = min(parsed.keys())
        last_rev = max(parsed.keys())
        for rev in [first_rev, last_rev]:
            if rev in parsed:
                headers = parsed[rev]["headers"]
                print(f"\nColumn headers (rev-{rev}, {len(headers)} cols):")
                for i, h in enumerate(headers):
                    if h:
                        print(f"  {col_letter(i):>3} ({i:2d}): {h}")

    # Compare consecutive pairs
    print()
    print("=" * 80)
    print("Comparing consecutive revisions (semantic matching)")
    print("=" * 80)

    all_results = []
    total_cell_changes = 0
    total_user_edits = 0

    for i in range(len(all_revs) - 1):
        rev_a = all_revs[i]
        rev_b = all_revs[i + 1]

        if rev_a not in parsed or rev_b not in parsed:
            continue

        result = diff_grids_semantic(parsed[rev_a], parsed[rev_b])
        result["from_rev"] = rev_a
        result["to_rev"] = rev_b

        changes = result["changes"]
        col_changes = result["column_changes"]
        row_changes = result["row_changes"]
        summary = result["summary"]

        all_results.append(result)

        style_only_count = result.get("style_only_count", 0)

        # Determine if there are any structural or data changes
        has_col_structure = (col_changes["added"] or col_changes["removed"]
                            or col_changes["unnamed_added"] > 0
                            or col_changes["unnamed_removed"] > 0
                            or col_changes["old_count"] != col_changes["new_count"])
        has_row_structure = (row_changes["added_count"] > 0
                            or row_changes["removed_count"] > 0
                            or row_changes["old_row_count"] != row_changes["new_row_count"])
        has_data_changes = bool(changes)

        # Skip truly identical transitions unless requested
        if not has_col_structure and not has_row_structure and not has_data_changes:
            if style_only_count > 0:
                if args.show_unchanged:
                    print(f"\nrev-{rev_a} -> rev-{rev_b}: "
                          f"formatting only ({style_only_count} style changes, no data changes)")
            elif args.show_unchanged:
                print(f"\nrev-{rev_a} -> rev-{rev_b}: IDENTICAL (no changes)")
            continue

        cats = summary["by_category"]
        user_edits = cats.get("user_edit", 0)
        total_cell_changes += len(changes)
        total_user_edits += user_edits

        print(f"\n{'─'*80}")
        print(f"rev-{rev_a} -> rev-{rev_b}:")

        # Column structure changes
        if has_col_structure:
            print(f"  COLUMNS: {col_changes['old_count']} -> "
                  f"{col_changes['new_count']} columns")
            if col_changes["added"]:
                for name, letter, idx in col_changes["added"]:
                    print(f"    + col {letter} ({idx}): \"{name}\"")
            if col_changes["removed"]:
                for name, letter, idx in col_changes["removed"]:
                    print(f"    - col {letter} ({idx}): \"{name}\"")
            if col_changes["unnamed_added"] > 0:
                for pos in col_changes.get("unnamed_positions", []):
                    context = ""
                    if pos["after"] and pos["before"]:
                        context = f" (between \"{pos['after']}\" and \"{pos['before']}\")"
                    elif pos["after"]:
                        context = f" (after \"{pos['after']}\")"
                    print(f"    + col {pos['col_letter']} ({pos['col']}): "
                          f"(empty/unnamed){context}")
            if col_changes["unnamed_removed"] > 0:
                print(f"    - {col_changes['unnamed_removed']} "
                      f"empty column(s) removed")

        # Row structure changes
        if has_row_structure:
            print(f"  ROWS: {row_changes['old_row_count']} -> "
                  f"{row_changes['new_row_count']} data rows "
                  f"({row_changes['matched']} matched by identity)")
            if row_changes["added_count"] > 0:
                n = row_changes["added_count"]
                print(f"    + {n} row(s) added")
                if n <= 10:
                    for k, new_row in row_changes["added"]:
                        print(f"      + row {new_row + 1}: {k}")
            if row_changes["removed_count"] > 0:
                n = row_changes["removed_count"]
                print(f"    - {n} row(s) removed")
                if n <= 10:
                    for k, old_row in row_changes["removed"]:
                        print(f"      - row {old_row + 1}: {k}")

        # Cell changes summary
        if changes:
            style_note = f"  (+ {style_only_count} style-only ignored)" if style_only_count else ""
            print(f"  CELL CHANGES: {len(changes)}{style_note}")
            parts = [f"{k}={v}" for k, v in sorted(cats.items())]
            print(f"    {', '.join(parts)}")

            # Changes by column
            by_col = summary.get("by_column", {})
            if by_col:
                print(f"\n  Changes by column:")
                for col_name in sorted(by_col.keys(), key=lambda x: (x == "", x)):
                    col_cats = by_col[col_name]
                    cparts = [f"{c}={n}" for c, n in sorted(col_cats.items())]
                    label = col_name if col_name else "(empty header)"
                    print(f"    {label:>35}: {', '.join(cparts)}")

            # Show individual changes
            priority = {
                "user_edit": 0, "column_added": 1, "column_removed": 2,
                "added": 3, "removed": 4, "formula_change": 5,
                "formula_result": 6, "style_only": 7, "type_change": 8,
                "other": 9,
            }
            sorted_changes = sorted(changes, key=lambda c: (
                priority.get(c["change_type"], 99), c["row"], c["col"]
            ))

            show_n = min(len(sorted_changes), args.max_changes)
            print(f"\n  Changes (showing {show_n}/{len(changes)}):")
            for j, change in enumerate(sorted_changes):
                if j >= args.max_changes:
                    print(f"  ... and {len(changes) - j} more changes")
                    break
                # Include row key for context
                rk = change.get("row_key", "")
                rk_short = rk[:40] + "..." if len(rk) > 40 else rk
                line = format_change(change, verbose=args.verbose)
                if rk:
                    line += f"  [{rk_short}]"
                print(line)

        elif style_only_count > 0 and (has_col_structure or has_row_structure):
            print(f"  ({style_only_count} style-only changes ignored)")
        else:
            if has_col_structure or has_row_structure:
                print(f"  No cell data changes (structure change only)")

    # Overall summary
    print()
    print("=" * 80)
    print("SEMANTIC DIFF SUMMARY")
    print("=" * 80)
    print(f"  Transitions analyzed: {len(all_results)}")

    def _is_identical(r):
        cc = r["column_changes"]
        rc = r["row_changes"]
        return (not r["changes"]
                and r.get("style_only_count", 0) == 0
                and not cc["added"] and not cc["removed"]
                and cc["unnamed_added"] == 0 and cc["unnamed_removed"] == 0
                and cc["old_count"] == cc["new_count"]
                and rc["added_count"] == 0 and rc["removed_count"] == 0
                and rc["old_row_count"] == rc["new_row_count"])

    def _is_style_only(r):
        cc = r["column_changes"]
        rc = r["row_changes"]
        return (not r["changes"]
                and r.get("style_only_count", 0) > 0
                and not cc["added"] and not cc["removed"]
                and cc["unnamed_added"] == 0 and cc["unnamed_removed"] == 0
                and cc["old_count"] == cc["new_count"]
                and rc["added_count"] == 0 and rc["removed_count"] == 0
                and rc["old_row_count"] == rc["new_row_count"])

    identical = sum(1 for r in all_results if _is_identical(r))
    style_only_transitions = sum(1 for r in all_results if _is_style_only(r))
    total_style_only = sum(r.get("style_only_count", 0) for r in all_results)
    print(f"  Identical transitions: {identical}")
    if style_only_transitions:
        print(f"  Style-only transitions: {style_only_transitions} "
              f"(formatting noise, no data changes)")
    print(f"  Changed transitions:   {len(all_results) - identical - style_only_transitions}")
    print(f"  Total cell changes:    {total_cell_changes}")
    print(f"  Total user edits:      {total_user_edits}")
    if total_style_only:
        print(f"  Style-only ignored:    {total_style_only} "
              f"(ODS formatting artifacts)")

    # Aggregate column structure changes
    all_col_adds = []
    all_col_removes = []
    for r in all_results:
        if r["column_changes"]["added"]:
            all_col_adds.append((r["from_rev"], r["to_rev"], r["column_changes"]["added"]))
        if r["column_changes"]["removed"]:
            all_col_removes.append((r["from_rev"], r["to_rev"], r["column_changes"]["removed"]))

    if all_col_adds or all_col_removes:
        print(f"\n  Column structure changes:")
        for fr, tr, cols in all_col_adds:
            names = [name for name, _, _ in cols] if isinstance(cols[0], tuple) else cols
            print(f"    rev-{fr} -> rev-{tr}: +{', '.join(names)}")
        for fr, tr, cols in all_col_removes:
            names = [name for name, _, _ in cols] if isinstance(cols[0], tuple) else cols
            print(f"    rev-{fr} -> rev-{tr}: -{', '.join(names)}")

    # Aggregate row changes
    total_added_rows = sum(r["row_changes"]["added_count"] for r in all_results)
    total_removed_rows = sum(r["row_changes"]["removed_count"] for r in all_results)
    if total_added_rows or total_removed_rows:
        print(f"\n  Row identity changes:")
        print(f"    Total rows added:   {total_added_rows}")
        print(f"    Total rows removed: {total_removed_rows}")

    # Most-changed columns
    global_col_counts = defaultdict(int)
    global_col_user_edits = defaultdict(int)
    for r in all_results:
        for c in r["changes"]:
            global_col_counts[c["header"]] += 1
            if c["change_type"] == "user_edit":
                global_col_user_edits[c["header"]] += 1

    if global_col_counts:
        print(f"\n  Most-changed columns:")
        for col, count in sorted(global_col_counts.items(), key=lambda x: -x[1])[:10]:
            label = col if col else "(empty)"
            user = global_col_user_edits.get(col, 0)
            print(f"    {label:>35}: {count:4d} total ({user} user edits)")

    # Write JSON
    if args.json:
        json_output = {
            "input_dir": str(indir),
            "mode": "semantic",
            "text_only": text_only,
            "revisions": all_revs,
            "transitions": [],
        }
        for r in all_results:
            t = {
                "from_rev": r["from_rev"],
                "to_rev": r["to_rev"],
                "column_changes": r["column_changes"],
                "row_changes": r["row_changes"],
                "num_changes": len(r["changes"]),
                "summary": r["summary"],
                "changes": r["changes"],
            }
            json_output["transitions"].append(t)

        json_path = Path(args.json)
        with open(json_path, "w") as f:
            json.dump(json_output, f, indent=2)
        print(f"\n  JSON results: {json_path}")


def _wait_for_file(path, timeout=600, poll=2.0):
    """Wait for a file to appear on disk. Used in pipeline mode."""
    import time as _time
    deadline = _time.time() + timeout
    while not path.exists():
        if _time.time() > deadline:
            raise TimeoutError(f"Timed out after {timeout}s waiting for {path.name}")
        _time.sleep(poll)


def _run_semantic_streaming(args, indir, ods_files, all_revs):
    """Streaming pairwise semantic diff: parse 2 files at a time, write to disk, free memory.

    This avoids loading all ODS files into memory simultaneously, making it
    feasible to diff 1000+ consecutive revisions on a machine with limited RAM.
    Each pair's result is written as a separate JSON file to the output directory.
    """
    import gc as gc_mod

    text_only = args.text_only
    wait_mode = getattr(args, "wait", False)
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"Streaming pairwise diff: {len(all_revs) - 1} transitions")
    print(f"  Output: {outdir}/")
    if wait_mode:
        print(f"  Wait mode: ON (will poll for files)")
    print()

    # Track aggregates as we go
    total_transitions = 0
    identical_count = 0
    style_only_count_total = 0
    changed_count = 0
    total_cell_changes = 0
    total_user_edits = 0
    col_structure_events = []
    row_structure_events = []
    errors = []

    # Cache: keep the "new" parse from the previous pair as "old" for the next
    prev_rev = None
    prev_data = None

    for i in range(len(all_revs) - 1):
        rev_a = all_revs[i]
        rev_b = all_revs[i + 1]

        pair_json = outdir / f"pair-{rev_a}-{rev_b}.json"

        # Skip if already computed
        if pair_json.exists() and pair_json.stat().st_size > 10:
            # Read the existing result to accumulate stats
            try:
                with open(pair_json) as f:
                    existing = json.load(f)
                total_transitions += 1
                n_changes = existing.get("num_changes", 0)
                if n_changes == 0 and existing.get("style_only_count", 0) == 0:
                    if not existing.get("has_col_structure") and not existing.get("has_row_structure"):
                        identical_count += 1
                    else:
                        changed_count += 1
                elif n_changes == 0:
                    style_only_count_total += 1
                else:
                    changed_count += 1
                    total_cell_changes += n_changes
                    total_user_edits += existing.get("summary", {}).get(
                        "by_category", {}).get("user_edit", 0)
                print(f"  rev-{rev_a:>5} -> rev-{rev_b:>5}: skip (cached, "
                      f"{n_changes} changes)")
                # Invalidate cache since we didn't parse rev_b
                prev_rev = None
                prev_data = None
                continue
            except (json.JSONDecodeError, KeyError):
                pass  # Re-compute if file is corrupt

        # Wait for files if in pipeline mode (downloads may still be in progress)
        if wait_mode:
            try:
                _wait_for_file(ods_files[rev_a])
                _wait_for_file(ods_files[rev_b])
            except TimeoutError as e:
                print(f"  rev-{rev_a:>5} -> rev-{rev_b:>5}: {e}")
                errors.append({"pair": f"{rev_a}-{rev_b}", "error": str(e)})
                prev_rev = None
                prev_data = None
                continue

        # Parse old revision (use cache if possible)
        if prev_rev == rev_a and prev_data is not None:
            old_data = prev_data
        else:
            try:
                old_data = parse_ods(ods_files[rev_a], text_only=text_only)
            except Exception as e:
                print(f"  rev-{rev_a:>5} -> rev-{rev_b:>5}: ERROR parsing rev-{rev_a}: {e}")
                errors.append({"pair": f"{rev_a}-{rev_b}", "error": str(e)})
                prev_rev = None
                prev_data = None
                continue

        # Parse new revision
        try:
            new_data = parse_ods(ods_files[rev_b], text_only=text_only)
        except Exception as e:
            print(f"  rev-{rev_a:>5} -> rev-{rev_b:>5}: ERROR parsing rev-{rev_b}: {e}")
            errors.append({"pair": f"{rev_a}-{rev_b}", "error": str(e)})
            prev_rev = None
            prev_data = None
            del old_data
            gc_mod.collect()
            continue

        # Run semantic diff
        result = diff_grids_semantic(old_data, new_data)

        changes = result["changes"]
        col_changes = result["column_changes"]
        row_changes = result["row_changes"]
        style_only = result.get("style_only_count", 0)

        has_col_structure = (col_changes["added"] or col_changes["removed"]
                            or col_changes["unnamed_added"] > 0
                            or col_changes["unnamed_removed"] > 0
                            or col_changes["old_count"] != col_changes["new_count"])
        has_row_structure = (row_changes["added_count"] > 0
                            or row_changes["removed_count"] > 0
                            or row_changes["old_row_count"] != row_changes["new_row_count"])

        # Write per-pair JSON
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
            json.dump(pair_result, f, indent=2)

        # Accumulate stats
        total_transitions += 1
        cats = result["summary"]["by_category"]
        user_edits = cats.get("user_edit", 0)

        if not changes and style_only == 0 and not has_col_structure and not has_row_structure:
            identical_count += 1
            tag = "IDENTICAL"
        elif not changes and style_only > 0 and not has_col_structure and not has_row_structure:
            style_only_count_total += 1
            tag = f"style-only ({style_only})"
        else:
            changed_count += 1
            total_cell_changes += len(changes)
            total_user_edits += user_edits
            parts = []
            if len(changes):
                parts.append(f"{len(changes)} changes")
            if user_edits:
                parts.append(f"{user_edits} user edits")
            if has_col_structure:
                parts.append(f"cols {col_changes['old_count']}->{col_changes['new_count']}")
                col_structure_events.append(
                    (rev_a, rev_b, col_changes["added"], col_changes["removed"],
                     col_changes["unnamed_added"], col_changes["unnamed_removed"]))
            if has_row_structure:
                parts.append(f"rows {row_changes['old_row_count']}->{row_changes['new_row_count']}")
                row_structure_events.append(
                    (rev_a, rev_b, row_changes["added_count"], row_changes["removed_count"]))
            if style_only > 0:
                parts.append(f"+{style_only} style")
            tag = ", ".join(parts) if parts else "no data changes"

        print(f"  rev-{rev_a:>5} -> rev-{rev_b:>5}: {tag}")

        # Cache new_data for next iteration, free old_data
        prev_rev = rev_b
        prev_data = new_data
        del old_data
        del result
        gc_mod.collect()

    # Write aggregate summary
    summary_path = outdir / "summary.json"
    summary = {
        "input_dir": str(indir),
        "mode": "semantic_streaming",
        "text_only": text_only,
        "revision_range": [all_revs[0], all_revs[-1]],
        "total_revisions": len(all_revs),
        "total_transitions": total_transitions,
        "identical_transitions": identical_count,
        "style_only_transitions": style_only_count_total,
        "changed_transitions": changed_count,
        "total_cell_changes": total_cell_changes,
        "total_user_edits": total_user_edits,
        "col_structure_events": [
            {"from": a, "to": b,
             "added": list(added) if added else [],
             "removed": list(removed) if removed else [],
             "unnamed_added": ua, "unnamed_removed": ur}
            for a, b, added, removed, ua, ur in col_structure_events
        ],
        "row_structure_events": [
            {"from": a, "to": b, "added": ac, "removed": rc}
            for a, b, ac, rc in row_structure_events
        ],
        "errors": errors,
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print()
    print("=" * 80)
    print("STREAMING SEMANTIC DIFF SUMMARY")
    print("=" * 80)
    print(f"  Transitions: {total_transitions}")
    print(f"  Identical:   {identical_count}")
    print(f"  Style-only:  {style_only_count_total}")
    print(f"  Changed:     {changed_count}")
    print(f"  Errors:      {len(errors)}")
    print(f"  Total cell changes: {total_cell_changes}")
    print(f"  Total user edits:   {total_user_edits}")
    if col_structure_events:
        print(f"\n  Column structure changes ({len(col_structure_events)}):")
        for rev_a, rev_b, added, removed, ua, ur in col_structure_events:
            parts = []
            if added:
                parts.append("+" + ",".join(n for n, _, _ in added))
            if removed:
                parts.append("-" + ",".join(n for n, _, _ in removed))
            if ua:
                parts.append(f"+{ua} unnamed")
            if ur:
                parts.append(f"-{ur} unnamed")
            print(f"    rev-{rev_a} -> rev-{rev_b}: {', '.join(parts)}")
    if row_structure_events:
        print(f"\n  Row structure changes ({len(row_structure_events)}):")
        for rev_a, rev_b, ac, rc in row_structure_events:
            print(f"    rev-{rev_a} -> rev-{rev_b}: +{ac} -{rc} rows")
    print(f"\n  Per-pair JSON: {outdir}/pair-*.json")
    print(f"  Summary JSON:  {summary_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Diff consecutive ODS revision files"
    )
    parser.add_argument(
        "input_dir", type=str,
        help="Directory containing rev-N.ods files"
    )
    parser.add_argument(
        "--range", type=str, default=None,
        help="Range of revisions to compare, e.g. '1-10' or '5-15'"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show formula details for changes"
    )
    parser.add_argument(
        "--json", type=str, default=None,
        help="Write detailed results to JSON file"
    )
    parser.add_argument(
        "--show-unchanged", action="store_true",
        help="Also report when consecutive revisions are identical"
    )
    parser.add_argument(
        "--max-changes", type=int, default=50,
        help="Max changes to display per transition (default: 50)"
    )
    parser.add_argument(
        "--text-only", action="store_true",
        help="Ignore formulas, only compare text content (eliminates column-shift noise)"
    )
    parser.add_argument(
        "--all-sheets", action="store_true",
        help="Compare all sheets in the ODS file (for multi-sheet documents)"
    )
    parser.add_argument(
        "--positional", action="store_true",
        help="Use positional comparison instead of the default semantic matching. "
             "Compares by (row, col) position, which generates false changes "
             "when columns or rows are inserted/removed."
    )
    parser.add_argument(
        "--streaming", action="store_true",
        help="Streaming pairwise mode: parse only 2 ODS files at a time, "
             "write per-pair JSON to output-dir, free memory between pairs. "
             "Essential for large ranges (100+ revisions)."
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Output directory for streaming mode per-pair JSON files "
             "(default: /tmp/semantic-diff-streaming/)"
    )
    parser.add_argument(
        "--manifest", type=str, default=None,
        help="File listing expected revision numbers (one per line). "
             "Use instead of directory glob — allows starting before all files exist."
    )
    parser.add_argument(
        "--wait", action="store_true",
        help="Wait for ODS files to appear on disk (poll every 2s, 10 min timeout). "
             "Use with --manifest when downloads are still in progress."
    )
    args = parser.parse_args()

    indir = Path(args.input_dir)
    if not indir.is_dir():
        print(f"ERROR: {indir} is not a directory")
        sys.exit(1)

    # Build the revision list: from manifest (pipeline) or directory glob
    if args.manifest:
        manifest_revs = sorted(
            int(line.strip())
            for line in Path(args.manifest).read_text().splitlines()
            if line.strip()
        )
        ods_files = {r: indir / f"rev-{r}.ods" for r in manifest_revs}
        all_revs = manifest_revs
    else:
        ods_files = {}
        for f in indir.glob("rev-*.ods"):
            if f.suffix == ".ods":
                try:
                    rev_num = int(f.stem.split("-")[1])
                    ods_files[rev_num] = f
                except (ValueError, IndexError):
                    pass
        if not ods_files:
            print(f"ERROR: No rev-N.ods files found in {indir}")
            sys.exit(1)
        all_revs = sorted(ods_files.keys())

    # Apply range filter
    if args.range:
        start, end = args.range.split("-")
        all_revs = [r for r in all_revs if int(start) <= r <= int(end)]
        ods_files = {r: ods_files[r] for r in all_revs}

    modes = []
    if args.text_only:
        modes.append("text-only")
    if args.all_sheets:
        modes.append("all sheets")
    if args.positional:
        modes.append("positional")
    else:
        modes.append("semantic")
    mode_str = f" ({', '.join(modes)})" if modes else ""

    print("=" * 80)
    print(f"ODS Revision Diff Analysis{mode_str}")
    print("=" * 80)
    print(f"  Directory: {indir}")
    print(f"  Revisions: {len(all_revs)} ({all_revs[0]}-{all_revs[-1]})")
    for m in modes:
        print(f"  Mode: {m.upper()}")
    print()

    if args.streaming:
        if not args.output_dir:
            args.output_dir = "/tmp/semantic-diff-streaming"
        _run_semantic_streaming(args, indir, ods_files, all_revs)
    elif args.positional:
        # Legacy positional mode
        if args.all_sheets:
            _run_all_sheets_mode(args, indir, ods_files, all_revs)
        else:
            _run_single_sheet_mode(args, indir, ods_files, all_revs)
    elif args.all_sheets:
        _run_all_sheets_mode(args, indir, ods_files, all_revs)
    else:
        _run_semantic_mode(args, indir, ods_files, all_revs)


if __name__ == "__main__":
    main()
