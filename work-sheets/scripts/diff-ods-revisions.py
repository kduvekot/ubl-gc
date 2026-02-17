#!/usr/bin/env python3
"""
Diff consecutive ODS revision files to analyze cell-level changes.

Reads ODS (OpenDocument Spreadsheet) files exported from Google Sheets
revision history, extracts all cell data from the content.xml, and
compares consecutive revisions to show exactly what changed.

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
    """Compare two parsed ODS grids and return all differences.

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
    args = parser.parse_args()

    indir = Path(args.input_dir)
    if not indir.is_dir():
        print(f"ERROR: {indir} is not a directory")
        sys.exit(1)

    # Find all rev-N.ods files
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

    # Apply range filter
    all_revs = sorted(ods_files.keys())
    if args.range:
        start, end = args.range.split("-")
        all_revs = [r for r in all_revs if int(start) <= r <= int(end)]

    print("=" * 80)
    print(f"ODS Revision Diff Analysis {'(text-only)' if args.text_only else ''}"
          f"{'(all sheets)' if args.all_sheets else ''}")
    print("=" * 80)
    print(f"  Directory: {indir}")
    print(f"  Revisions: {len(all_revs)} ({all_revs[0]}-{all_revs[-1]})")
    if args.text_only:
        print(f"  Mode: TEXT-ONLY (formulas ignored)")
    if args.all_sheets:
        print(f"  Mode: ALL SHEETS")
    print()

    if args.all_sheets:
        _run_all_sheets_mode(args, indir, ods_files, all_revs)
    else:
        _run_single_sheet_mode(args, indir, ods_files, all_revs)


if __name__ == "__main__":
    main()
