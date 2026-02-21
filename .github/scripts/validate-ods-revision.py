#!/usr/bin/env python3
"""Validate ODS revision against official .gc file.

Downloads a specific ODS revision from Google Drive, parses all sheets,
and compares cell content against the official GenericCode (.gc) file.

Usage:
    python3 validate-ods-revision.py \
        --sheet documents --rev 1539 \
        --gc-file history/csd01-UBL-2.5/mod/UBL-Entities-2.5.gc

    python3 validate-ods-revision.py \
        --sheet library --rev 1533 \
        --gc-file history/csd01-UBL-2.5/mod/UBL-Entities-2.5.gc
"""

import argparse
import gzip
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import time
import urllib.parse

# ── ODS XML namespaces ────────────────────────────────────────────────
NS_TABLE = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
NS_TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
NS_OFFICE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"

# ── Google Drive public folder IDs ────────────────────────────────────
DRIVE_FOLDERS = {
    "library": "1JRvRaqsNP_G-9xICwrgGpY-ArwV8ej1w",
    "documents": "1DsufM2yMqcbE8kR-RH1i5rSBcvPivOxA",
}

# ── ODS column name → .gc ColumnRef mapping ──────────────────────────
ODS_TO_GC_COLUMN = {
    "Alternative Business Terms": "AlternativeBusinessTerms",
    "Associated Object Class": "AssociatedObjectClass",
    "Associated Object Class Qualifier": "AssociatedObjectClassQualifier",
    "Cardinality": "Cardinality",
    "Component Name": "ComponentName",
    "Component Type": "ComponentType",
    "Current Version": "CurrentVersion",
    "Data Type": "DataType",
    "Data Type Qualifier": "DataTypeQualifier",
    "Definition": "Definition",
    "Deprecated Definition": "DeprecatedDefinition",
    "Dictionary Entry Name": "DictionaryEntryName",
    "Editor's Notes": "EditorsNotes",
    "Endorsed Cardinality": "EndorsedCardinality",
    "Endorsed Cardinality Rationale": "EndorsedCardinalityRationale",
    "Examples": "Examples",
    "Last Changed": "LastChanged",
    "Object Class": "ObjectClass",
    "Object Class Qualifier": "ObjectClassQualifier",
    "Property Term": "PropertyTerm",
    "Property Term Possessive Noun": "PropertyTermPossessiveNoun",
    "Property Term Primary Noun": "PropertyTermPrimaryNoun",
    "Property Term Qualifier": "PropertyTermQualifier",
    "Representation Term": "RepresentationTerm",
    "Subset": "Subset",
    "UN/TDED Code": "UNTDEDCode",
}

# ── ODS sheet name → .gc ModelName mapping ────────────────────────────
# The .gc ModelName is "UBL-{SheetName}-{version}" but some sheet names
# are abbreviated. We'll build the mapping dynamically.


def list_drive_folder(folder_id):
    """List all files in a public Google Drive folder using the embed view."""
    from html.parser import HTMLParser

    class DriveEmbedParser(HTMLParser):
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

    url = f"https://drive.google.com/embeddedfolderview?id={folder_id}"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=60) as resp:
        html = resp.read().decode("utf-8")

    parser = DriveEmbedParser()
    parser.feed(html)
    return parser.entries


def find_drive_file(folder_id, rev_num):
    """Find a specific revision file in a Google Drive folder."""
    filename = f"rev-{rev_num}.ods.gz"
    print(f"  Listing folder to find {filename}...")
    entries = list_drive_folder(folder_id)
    print(f"  Found {len(entries)} files in folder")

    for entry in entries:
        if entry.get("name") == filename:
            return entry["id"]

    # Fallback: try API
    q = urllib.parse.quote(
        f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    )
    api_url = (
        f"https://www.googleapis.com/drive/v3/files"
        f"?q={q}"
        f"&fields=files(id,name,size)"
        f"&supportsAllDrives=true"
    )
    try:
        req = Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        files = data.get("files", [])
        if files:
            return files[0]["id"]
    except Exception as e:
        print(f"  API fallback failed: {e}")
    return None


def download_drive_file(file_id, dest_path, retries=3):
    """Download a file from Google Drive by ID."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=120) as resp:
                data = resp.read()
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
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  Retry {attempt+1}: {e}, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise


def download_revision(sheet, rev_num, dest_dir):
    """Download and decompress a specific ODS revision."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    ods_path = dest_dir / f"rev-{rev_num}.ods"
    if ods_path.exists() and ods_path.stat().st_size > 1000:
        print(f"  Already downloaded: {ods_path}")
        return ods_path

    folder_id = DRIVE_FOLDERS[sheet]
    print(f"  Finding rev-{rev_num}.ods.gz in {sheet} folder...")
    file_id = find_drive_file(folder_id, rev_num)
    if not file_id:
        print(f"  ERROR: Could not find rev-{rev_num}.ods.gz")
        return None

    gz_path = dest_dir / f"rev-{rev_num}.ods.gz"
    print(f"  Downloading file ID {file_id}...")
    size = download_drive_file(file_id, gz_path)
    print(f"  Downloaded {size:,} bytes")

    gz_data = gz_path.read_bytes()
    ods_data = gzip.decompress(gz_data)
    ods_path.write_bytes(ods_data)
    print(f"  Decompressed to {len(ods_data):,} bytes")

    return ods_path


def extract_cell_text(cell_elem):
    """Extract text content from an ODS cell element."""
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


def parse_ods_sheets(ods_path):
    """Parse all sheets from an ODS file, returning {sheet_name: {headers, rows}}."""
    with zipfile.ZipFile(ods_path) as zf:
        content = zf.read("content.xml")

    root = ET.fromstring(content)
    sheets = {}

    for table in root.findall(f".//{NS_TABLE}table"):
        name = table.get(f"{NS_TABLE}name", "")
        if not name or re.match(r"^Logs", name, re.IGNORECASE):
            continue

        rows_elem = table.findall(f"{NS_TABLE}table-row")
        headers = []
        data_rows = []

        actual_row = 0
        for row_elem in rows_elem:
            row_repeat = int(row_elem.get(f"{NS_TABLE}number-rows-repeated", "1"))
            if row_repeat > 10000:
                actual_row += row_repeat
                continue

            cells = row_elem.findall(f"{NS_TABLE}table-cell")
            row_data = []
            col_idx = 0

            for cell_elem in cells:
                col_repeat = int(cell_elem.get(f"{NS_TABLE}number-columns-repeated", "1"))
                if col_repeat > 1000:
                    col_idx += col_repeat
                    continue

                text = extract_cell_text(cell_elem)
                for _ in range(min(col_repeat, 200)):
                    row_data.append(text)
                    col_idx += 1

            if actual_row == 0:
                headers = row_data
            else:
                # Only include rows that have at least one non-empty cell
                if any(c.strip() for c in row_data):
                    data_rows.append(row_data)

            actual_row += row_repeat

        sheets[name] = {"headers": headers, "rows": data_rows}

    return sheets


def parse_gc_file(gc_path):
    """Parse a .gc file and return {ModelName: [{col_ref: value, ...}, ...]}."""
    tree = ET.parse(gc_path)
    root = tree.getroot()

    # Get column IDs
    columns = []
    for col in root.findall('.//Column'):
        columns.append(col.get('Id'))

    # Get rows grouped by ModelName
    models = {}
    for row in root.findall('.//Row'):
        values = {}
        for val in row.findall('Value'):
            col_ref = val.get('ColumnRef')
            sv = val.find('SimpleValue')
            if sv is not None and sv.text:
                values[col_ref] = sv.text
        model = values.get('ModelName', 'UNKNOWN')
        if model not in models:
            models[model] = []
        models[model].append(values)

    return models, columns


def build_sheet_to_model_map(gc_models, ods_sheets):
    """Build mapping from ODS sheet name to .gc ModelName."""
    mapping = {}
    gc_model_names = set(gc_models.keys())

    for sheet_name in ods_sheets:
        # Try common patterns
        candidates = [
            f"UBL-{sheet_name}-2.5",
            f"UBL-{sheet_name}-2.4",
            f"UBL-{sheet_name}-2.3",
        ]
        for c in candidates:
            if c in gc_model_names:
                mapping[sheet_name] = c
                break

    # For unmatched, try fuzzy matching
    matched_models = set(mapping.values())
    unmatched_sheets = [s for s in ods_sheets if s not in mapping]
    unmatched_models = gc_model_names - matched_models

    # Common abbreviations in ODS sheet names
    ABBREV = {
        "Ctlg": "Catalogue",
        "CtlgDeletion": "CatalogueDeletion",
        "CtlgItemSpecificationUpdate": "CatalogueItemSpecificationUpdate",
        "CtlgPricingUpdate": "CataloguePricingUpdate",
        "CtlgRequest": "CatalogueRequest",
        "QlfctnApplicationRequest": "QualificationApplicationRequest",
        "QlfctnApplicationResponse": "QualificationApplicationResponse",
        "TendererQlfctn": "TendererQualification",
        "TendererQlfctnResponse": "TendererQualificationResponse",
        "TxpExecutionPlan": "TransportExecutionPlan",
        "TxpExecutionPlanRequest": "TransportExecutionPlanRequest",
        "TxpProgressStatus": "TransportProgressStatus",
        "TxpProgressStatusRequest": "TransportProgressStatusRequest",
        "TxpServiceDescription": "TransportServiceDescription",
        "TxpServiceDescriptionRequest": "TransportServiceDescriptionRequest",
        "UnsubscribeFromPrcdRequest": "UnsubscribeFromProcedureRequest",
        "UnsubscribeFromPrcdResponse": "UnsubscribeFromProcedureResponse",
    }

    for sheet_name in unmatched_sheets:
        full_name = ABBREV.get(sheet_name, sheet_name)
        for version in ["2.5", "2.4", "2.3"]:
            candidate = f"UBL-{full_name}-{version}"
            if candidate in unmatched_models:
                mapping[sheet_name] = candidate
                break

    return mapping


def compare_ods_to_gc(ods_sheets, gc_models, gc_columns, sheet_type):
    """Compare ODS cell content against .gc file content.

    sheet_type: 'documents' or 'library'
    For documents: each ODS sheet = one ModelName group in .gc
    For library: single 'CommonLibrary' sheet = all rows in .gc (ModelName varies)
    """
    total_cells = 0
    matched_cells = 0
    mismatches = []
    missing_models = []
    extra_sheets = []

    if sheet_type == "library":
        # Library ODS: single sheet contains ALL models
        # The first column is the model name equivalent
        # Actually for library, all rows go into one big model
        # Let me handle this case separately
        return compare_library_ods_to_gc(ods_sheets, gc_models, gc_columns)

    # Documents ODS: each sheet = one model
    sheet_to_model = build_sheet_to_model_map(gc_models, ods_sheets)

    for sheet_name, model_name in sorted(sheet_to_model.items()):
        sheet_data = ods_sheets[sheet_name]
        gc_rows = gc_models.get(model_name, [])

        if not gc_rows:
            missing_models.append(model_name)
            continue

        ods_headers = sheet_data["headers"]
        ods_rows = sheet_data["rows"]

        # Build ODS column index → gc column ref mapping
        col_map = {}
        for i, header in enumerate(ods_headers):
            gc_ref = ODS_TO_GC_COLUMN.get(header)
            if gc_ref and gc_ref in gc_columns:
                col_map[i] = gc_ref

        # Compare row by row (using Dictionary Entry Name as key)
        den_col = None
        for i, header in enumerate(ods_headers):
            if header == "Dictionary Entry Name":
                den_col = i
                break

        if den_col is None:
            continue

        # Build ODS row map by DEN
        ods_by_den = {}
        for row in ods_rows:
            if den_col < len(row) and row[den_col].strip():
                ods_by_den[row[den_col].strip()] = row

        # Build GC row map by DEN
        gc_by_den = {}
        for row in gc_rows:
            den = row.get("DictionaryEntryName", "")
            if den:
                gc_by_den[den] = row

        # Compare
        for den, gc_row in gc_by_den.items():
            ods_row = ods_by_den.get(den)
            if ods_row is None:
                mismatches.append({
                    "type": "missing_row",
                    "sheet": sheet_name,
                    "model": model_name,
                    "den": den,
                })
                continue

            for ods_col_idx, gc_col_ref in col_map.items():
                ods_val = ods_row[ods_col_idx].strip() if ods_col_idx < len(ods_row) else ""
                gc_val = gc_row.get(gc_col_ref, "").strip()
                # Normalize: ODS cells may contain newlines that .gc flattens to spaces
                ods_val_norm = " ".join(ods_val.split())
                gc_val_norm = " ".join(gc_val.split())
                total_cells += 1

                if ods_val_norm == gc_val_norm:
                    matched_cells += 1
                else:
                    mismatches.append({
                        "type": "cell_mismatch",
                        "sheet": sheet_name,
                        "model": model_name,
                        "den": den,
                        "column": gc_col_ref,
                        "ods_value": ods_val[:100],
                        "gc_value": gc_val[:100],
                    })

        # Check for extra rows in ODS not in GC
        for den in ods_by_den:
            if den not in gc_by_den:
                mismatches.append({
                    "type": "extra_row",
                    "sheet": sheet_name,
                    "model": model_name,
                    "den": den,
                })

    # Check for models in .gc not matched to any sheet
    matched_models = set(sheet_to_model.values())
    for model_name in gc_models:
        if model_name not in matched_models:
            # CommonLibrary is expected to be in library ODS, not documents
            if "CommonLibrary" in model_name:
                continue
            missing_models.append(model_name)

    return {
        "total_cells": total_cells,
        "matched_cells": matched_cells,
        "mismatches": mismatches,
        "missing_models": missing_models,
        "extra_sheets": extra_sheets,
        "sheet_mapping": sheet_to_model,
    }


def compare_library_ods_to_gc(ods_sheets, gc_models, gc_columns):
    """Compare library ODS against the CommonLibrary model in .gc."""
    # The library ODS has a single main sheet (CommonLibrary or similar)
    # that contains all component definitions
    gc_lib_rows = gc_models.get("UBL-CommonLibrary-2.5", [])
    if not gc_lib_rows:
        # Try other version names
        for model_name, rows in gc_models.items():
            if "CommonLibrary" in model_name:
                gc_lib_rows = rows
                break

    if not gc_lib_rows:
        return {"error": "No CommonLibrary model found in .gc"}

    # Find the main sheet in ODS (usually first sheet or "CommonLibrary")
    main_sheet = None
    for name in ["CommonLibrary", "Library"]:
        if name in ods_sheets:
            main_sheet = ods_sheets[name]
            break
    if main_sheet is None:
        # Use the first non-empty sheet
        for name, data in ods_sheets.items():
            if data["rows"]:
                main_sheet = data
                break

    if main_sheet is None:
        return {"error": "No data sheet found in library ODS"}

    ods_headers = main_sheet["headers"]
    ods_rows = main_sheet["rows"]

    # Build column mapping
    col_map = {}
    for i, header in enumerate(ods_headers):
        gc_ref = ODS_TO_GC_COLUMN.get(header)
        if gc_ref and gc_ref in gc_columns:
            col_map[i] = gc_ref

    # Find DEN column
    den_col = None
    for i, header in enumerate(ods_headers):
        if header == "Dictionary Entry Name":
            den_col = i
            break

    if den_col is None:
        return {"error": "No Dictionary Entry Name column in library ODS"}

    # Build maps
    ods_by_den = {}
    for row in ods_rows:
        if den_col < len(row) and row[den_col].strip():
            ods_by_den[row[den_col].strip()] = row

    gc_by_den = {}
    for row in gc_lib_rows:
        den = row.get("DictionaryEntryName", "")
        if den:
            gc_by_den[den] = row

    total_cells = 0
    matched_cells = 0
    mismatches = []

    for den, gc_row in gc_by_den.items():
        ods_row = ods_by_den.get(den)
        if ods_row is None:
            mismatches.append({
                "type": "missing_row",
                "sheet": "CommonLibrary",
                "den": den,
            })
            continue

        for ods_col_idx, gc_col_ref in col_map.items():
            ods_val = ods_row[ods_col_idx].strip() if ods_col_idx < len(ods_row) else ""
            gc_val = gc_row.get(gc_col_ref, "").strip()
            # Normalize: ODS cells may contain newlines that .gc flattens to spaces
            ods_val_norm = " ".join(ods_val.split())
            gc_val_norm = " ".join(gc_val.split())
            total_cells += 1

            if ods_val_norm == gc_val_norm:
                matched_cells += 1
            else:
                mismatches.append({
                    "type": "cell_mismatch",
                    "sheet": "CommonLibrary",
                    "den": den,
                    "column": gc_col_ref,
                    "ods_value": ods_val[:100],
                    "gc_value": gc_val[:100],
                })

    for den in ods_by_den:
        if den not in gc_by_den:
            mismatches.append({
                "type": "extra_row",
                "sheet": "CommonLibrary",
                "den": den,
            })

    return {
        "total_cells": total_cells,
        "matched_cells": matched_cells,
        "mismatches": mismatches,
        "missing_models": [],
        "extra_sheets": [],
    }


def main():
    parser = argparse.ArgumentParser(description="Validate ODS revision against .gc file")
    parser.add_argument("--sheet", required=True, choices=["documents", "library"])
    parser.add_argument("--rev", required=True, type=int, help="Revision number")
    parser.add_argument("--gc-file", required=True, help="Path to official .gc file")
    parser.add_argument("--download-dir", default="/tmp/ods-validation",
                        help="Directory for downloaded ODS files")
    parser.add_argument("--ods-file", help="Use existing ODS file instead of downloading")
    args = parser.parse_args()

    gc_path = Path(args.gc_file)
    if not gc_path.exists():
        print(f"ERROR: .gc file not found: {gc_path}")
        sys.exit(1)

    # Step 1: Get ODS file
    if args.ods_file:
        ods_path = Path(args.ods_file)
    else:
        print(f"\n=== Downloading {args.sheet} ODS rev-{args.rev} ===")
        ods_path = download_revision(args.sheet, args.rev, args.download_dir)
        if not ods_path:
            sys.exit(1)

    # Step 2: Parse ODS
    print(f"\n=== Parsing ODS: {ods_path} ===")
    ods_sheets = parse_ods_sheets(ods_path)
    print(f"  Found {len(ods_sheets)} sheets")
    for name, data in sorted(ods_sheets.items()):
        print(f"    {name}: {len(data['headers'])} columns, {len(data['rows'])} data rows")

    # Step 3: Parse .gc
    print(f"\n=== Parsing .gc: {gc_path} ===")
    gc_models, gc_columns = parse_gc_file(gc_path)
    total_gc_rows = sum(len(rows) for rows in gc_models.values())
    print(f"  {len(gc_models)} models, {total_gc_rows} total rows")
    print(f"  {len(gc_columns)} columns: {gc_columns[:5]}...")

    # Step 4: Compare
    print(f"\n=== Comparing ODS rev-{args.rev} vs .gc ===")
    result = compare_ods_to_gc(ods_sheets, gc_models, gc_columns, args.sheet)

    # Step 5: Report
    total = result["total_cells"]
    matched = result["matched_cells"]
    mismatches = result["mismatches"]

    cell_mismatches = [m for m in mismatches if m["type"] == "cell_mismatch"]
    missing_rows = [m for m in mismatches if m["type"] == "missing_row"]
    extra_rows = [m for m in mismatches if m["type"] == "extra_row"]

    print(f"\n{'='*60}")
    print(f"RESULTS: {args.sheet} rev-{args.rev} vs {gc_path.name}")
    print(f"{'='*60}")
    print(f"  Total cells compared: {total:,}")
    print(f"  Matched:              {matched:,}")
    print(f"  Cell mismatches:      {len(cell_mismatches):,}")
    print(f"  Missing rows (in gc, not in ods): {len(missing_rows)}")
    print(f"  Extra rows (in ods, not in gc):   {len(extra_rows)}")

    if result.get("missing_models"):
        print(f"\n  Models in .gc not matched to ODS sheets:")
        for m in result["missing_models"]:
            print(f"    {m}")

    if cell_mismatches:
        print(f"\n  First {min(20, len(cell_mismatches))} cell mismatches:")
        for m in cell_mismatches[:20]:
            print(f"    [{m.get('sheet','?')}] {m['den']}")
            print(f"      col={m['column']}")
            print(f"      ods: {m['ods_value']!r}")
            print(f"      gc:  {m['gc_value']!r}")

    if missing_rows:
        print(f"\n  Missing rows (first 10):")
        for m in missing_rows[:10]:
            print(f"    [{m.get('sheet','?')}] {m['den']}")

    if extra_rows:
        print(f"\n  Extra rows (first 10):")
        for m in extra_rows[:10]:
            print(f"    [{m.get('sheet','?')}] {m['den']}")

    if total > 0 and len(cell_mismatches) == 0 and len(missing_rows) == 0 and len(extra_rows) == 0:
        print(f"\n  ✓ PERFECT MATCH! All {total:,} cells match exactly.")
        sys.exit(0)
    else:
        pct = (matched / total * 100) if total > 0 else 0
        print(f"\n  ✗ MISMATCH: {pct:.2f}% match ({total - matched} differences)")
        sys.exit(1)


if __name__ == "__main__":
    main()
