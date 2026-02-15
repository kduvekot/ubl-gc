#!/usr/bin/env python3
"""
Download ODS exports for specific Google Sheets revisions.

Uses the Drive API v2 revisions endpoint to get exportLinks, which
provide revision-specific content (unlike v3 files.export which
ignores the revision parameter).

The ODS files can then be converted to GenericCode (.gc) using the
existing Crane-ods2obdgc + Saxon pipeline for comparison against
workflow-generated GC files.

Usage:
    GOOGLE_ACCESS_TOKEN="ya29.a0..." python3 scripts/download-revision-ods.py

Proven by PoC (Step 3): v2 exportLinks return different content per revision.

Output:
    .claude/swap/revision-ods/
      {sheet_key}/
        rev-{id}.ods              # ODS at this revision
      manifest.json               # Download metadata with hashes
    .claude/swap/revision-ods.tar.gz  # Compressed archive
"""

import os, sys, json, hashlib, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from datetime import datetime, timezone

TOKEN = os.environ.get("GOOGLE_ACCESS_TOKEN", "")
if not TOKEN:
    print("ERROR: Set GOOGLE_ACCESS_TOKEN environment variable")
    sys.exit(1)

# --- Sheets and their file IDs ---
SHEETS = {
    "ubl25_library":   "18o1YqjHWUw0-s8mb3ja4i99obOUhs-4zpgso6RZrGaY",
    "ubl25_documents": "1024Th-Uj8cqliNEJc-3pDOR7DxAAW7gCG4e-pbtarsg",
}

# --- Revisions to download ---
# These are the "BEFORE" revisions for each workflow run timestamp.
# The workflow downloads the sheet's current state as ODS, so the matching
# revision is the last one saved BEFORE the workflow ran.
#
# Mapping (from before/after analysis):
#   V1 (Nov 17 10:42) + V2 (Nov 19 09:15) → library rev-1843, docs rev-1793
#   V3 (Nov 20 13:50) → library rev-1868, docs rev-1803
#   V4 (Nov 20 14:05) → library rev-1868, docs rev-1983
#   V5 (Dec 3 ~csd02) + V6 (Jan 21 16:38) → library rev-1999, docs rev-2190
#   V7 (Jan 21 17:01) → library rev-2005, docs rev-2190
#   V8 (Jan 21 19:26) → library rev-2005, docs rev-2200
#   V9+V10 (Feb 9) → library rev-2005, docs rev-2204

REVISIONS_TO_DOWNLOAD = {
    "ubl25_library": [
        {"id": "1843", "date": "2025-11-12", "maps_to": "V1+V2",
         "desc": "Pre-CSD02 initial working copy"},
        {"id": "1868", "date": "2025-11-19", "maps_to": "V3+V4",
         "desc": "Customs definitions rewritten"},
        {"id": "1999", "date": "2025-12-03", "maps_to": "V5(csd02)+V6",
         "desc": "CSD02 official state"},
        {"id": "2005", "date": "2026-01-21", "maps_to": "V7+V8+V9+V10",
         "desc": "Post-CSD02, BuyerReference renamed"},
    ],
    "ubl25_documents": [
        {"id": "1793", "date": "2025-10-17", "maps_to": "V1+V2",
         "desc": "Pre-CSD02 baseline"},
        {"id": "1803", "date": "2025-11-19", "maps_to": "V3",
         "desc": "Before Nov 20 edit"},
        {"id": "1983", "date": "2025-11-20", "maps_to": "V4",
         "desc": "Nov 20 14:00 edit (between V3 and V4 workflow runs)"},
        {"id": "2190", "date": "2025-11-21", "maps_to": "V5(csd02)+V6+V7",
         "desc": "Last edit before csd02"},
        {"id": "2200", "date": "2026-01-21", "maps_to": "V8",
         "desc": "Jan 21 19:26 edit"},
        {"id": "2204", "date": "2026-02-04", "maps_to": "V9+V10",
         "desc": "Feb 4 edit, latest before V9/V10"},
    ],
}

# ODS MIME type for Google Sheets export
ODS_MIME = "application/x-vnd.oasis.opendocument.spreadsheet"

OUTPUT_DIR = Path(".claude/swap/revision-ods")
API_DELAY = 1.0  # seconds between API calls


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def api_get_json(url):
    """Authenticated JSON GET with retry."""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    for attempt in range(4):
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read())
        except HTTPError as e:
            status = e.code
            body = e.read().decode(errors="replace")
            if status == 429 or status >= 500:
                wait = 2 ** (attempt + 1)
                print(f"      Rate limited ({status}), waiting {wait}s...")
                time.sleep(wait)
                continue
            return status, body
    return 0, "max retries exceeded"


def api_download(url):
    """Authenticated binary GET with retry."""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    for attempt in range(4):
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=120) as resp:
                return resp.status, resp.read()
        except HTTPError as e:
            status = e.code
            body = e.read().decode(errors="replace")
            if status == 429 or status >= 500:
                wait = 2 ** (attempt + 1)
                print(f"      Rate limited ({status}), waiting {wait}s...")
                time.sleep(wait)
                continue
            return status, body
    return 0, b"max retries exceeded"


def get_revision_export_links(file_id, revision_id):
    """Get exportLinks from Drive API v2 for a specific revision."""
    url = (
        f"https://www.googleapis.com/drive/v2/files/{file_id}"
        f"/revisions/{revision_id}"
    )
    status, data = api_get_json(url)
    if status == 200 and isinstance(data, dict):
        return data.get("exportLinks", {})
    print(f"      ERROR getting exportLinks: HTTP {status}")
    if isinstance(data, str):
        print(f"      {data[:200]}")
    return {}


def download_ods_for_revision(file_id, revision_id, export_links):
    """Download ODS via exportLinks."""
    ods_url = export_links.get(ODS_MIME)
    if not ods_url:
        # Try alternative MIME type
        ods_url = export_links.get("application/vnd.oasis.opendocument.spreadsheet")
    if not ods_url:
        print(f"      No ODS export link found. Available formats:")
        for k in export_links:
            print(f"        {k}")
        return None

    status, data = api_download(ods_url)
    if status == 200 and isinstance(data, bytes):
        return data
    print(f"      ERROR downloading ODS: HTTP {status}")
    return None


def main():
    start_time = _now_iso()
    print("=" * 70)
    print("Download ODS for Key Google Sheets Revisions")
    print("=" * 70)
    print(f"  Method:  Drive API v2 revisions → exportLinks → ODS")
    print(f"  Sheets:  {len(SHEETS)}")
    total_revs = sum(len(v) for v in REVISIONS_TO_DOWNLOAD.values())
    print(f"  Revisions: {total_revs}")
    print(f"  Output:  {OUTPUT_DIR}/")
    print(f"  Token:   {TOKEN[:15]}...{TOKEN[-4:]}")
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_entries = []
    total_ok = 0
    total_fail = 0

    for sheet_key, file_id in SHEETS.items():
        revisions = REVISIONS_TO_DOWNLOAD.get(sheet_key, [])
        if not revisions:
            continue

        print(f"--- {sheet_key} ({len(revisions)} revisions) ---")
        sheet_dir = OUTPUT_DIR / sheet_key
        sheet_dir.mkdir(exist_ok=True)

        for rev in revisions:
            rev_id = rev["id"]
            rev_date = rev["date"]
            rev_desc = rev["desc"]
            maps_to = rev["maps_to"]
            ods_path = sheet_dir / f"rev-{rev_id}.ods"

            print(f"  rev-{rev_id} ({rev_date}) [{maps_to}]: {rev_desc}")

            # Skip if already downloaded
            if ods_path.exists() and ods_path.stat().st_size > 0:
                h = _sha256(ods_path.read_bytes())
                print(f"    [skip] already exists ({ods_path.stat().st_size:,} bytes, sha256={h[:16]}...)")
                manifest_entries.append({
                    "sheet_key": sheet_key,
                    "file_id": file_id,
                    "revision_id": rev_id,
                    "date": rev_date,
                    "maps_to": maps_to,
                    "description": rev_desc,
                    "ods_path": str(ods_path),
                    "ods_size": ods_path.stat().st_size,
                    "ods_sha256": h,
                    "status": "skipped",
                })
                total_ok += 1
                continue

            # Step 1: Get exportLinks for this revision
            print(f"    Getting exportLinks...", end="", flush=True)
            export_links = get_revision_export_links(file_id, rev_id)
            if not export_links:
                print(" FAILED")
                manifest_entries.append({
                    "sheet_key": sheet_key,
                    "file_id": file_id,
                    "revision_id": rev_id,
                    "date": rev_date,
                    "maps_to": maps_to,
                    "description": rev_desc,
                    "status": "failed_exportlinks",
                })
                total_fail += 1
                time.sleep(API_DELAY)
                continue
            print(f" OK ({len(export_links)} formats)")
            time.sleep(API_DELAY)

            # Step 2: Download ODS
            print(f"    Downloading ODS...", end="", flush=True)
            ods_data = download_ods_for_revision(file_id, rev_id, export_links)
            if not ods_data:
                print(" FAILED")
                manifest_entries.append({
                    "sheet_key": sheet_key,
                    "file_id": file_id,
                    "revision_id": rev_id,
                    "date": rev_date,
                    "maps_to": maps_to,
                    "description": rev_desc,
                    "status": "failed_download",
                })
                total_fail += 1
                time.sleep(API_DELAY)
                continue

            # Save
            ods_path.write_bytes(ods_data)
            h = _sha256(ods_data)
            print(f" {len(ods_data):,} bytes (sha256={h[:16]}...)")

            manifest_entries.append({
                "sheet_key": sheet_key,
                "file_id": file_id,
                "revision_id": rev_id,
                "date": rev_date,
                "maps_to": maps_to,
                "description": rev_desc,
                "ods_path": str(ods_path),
                "ods_size": len(ods_data),
                "ods_sha256": h,
                "status": "ok",
                "downloaded_at": _now_iso(),
            })
            total_ok += 1
            time.sleep(API_DELAY)

        print()

    # Write manifest
    manifest = {
        "_provenance": {
            "description": "ODS exports of specific Google Sheets revisions for UBL CSD02/CSD03 analysis",
            "method": "Drive API v2 revisions/{id} → exportLinks → ODS download",
            "poc_confirmation": "PoC in .claude/swap/poc-revision-download.txt proved v2 exportLinks return revision-specific content",
            "script": "scripts/download-revision-ods.py",
            "started_at": start_time,
            "completed_at": _now_iso(),
        },
        "revision_to_workflow_mapping": {
            "V1":  {"timestamp": "2025-11-17T10:42", "library": "rev-1843", "documents": "rev-1793"},
            "V2":  {"timestamp": "2025-11-19T09:15", "library": "rev-1843", "documents": "rev-1793"},
            "V3":  {"timestamp": "2025-11-20T13:50", "library": "rev-1868", "documents": "rev-1803"},
            "V4":  {"timestamp": "2025-11-20T14:05", "library": "rev-1868", "documents": "rev-1983"},
            "V5":  {"timestamp": "2025-12-03T~09:00", "library": "rev-1999", "documents": "rev-2190", "note": "csd02 official"},
            "V6":  {"timestamp": "2026-01-21T16:38", "library": "rev-1999", "documents": "rev-2190"},
            "V7":  {"timestamp": "2026-01-21T17:01", "library": "rev-2005", "documents": "rev-2190"},
            "V8":  {"timestamp": "2026-01-21T19:26", "library": "rev-2005", "documents": "rev-2200"},
            "V9":  {"timestamp": "2026-02-09T14:42", "library": "rev-2005", "documents": "rev-2204"},
            "V10": {"timestamp": "2026-02-09T14:46", "library": "rev-2005", "documents": "rev-2204"},
        },
        "stats": {
            "total_ok": total_ok,
            "total_failed": total_fail,
        },
        "entries": manifest_entries,
    }

    manifest_path = OUTPUT_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Create tar.gz
    import tarfile
    tar_path = Path(".claude/swap/revision-ods.tar.gz")
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(OUTPUT_DIR, arcname="revision-ods")
    tar_size = tar_path.stat().st_size

    print("=" * 70)
    print(f"DONE: {total_ok} OK, {total_fail} failed")
    print(f"  ODS files: {OUTPUT_DIR}/")
    print(f"  Manifest:  {manifest_path}")
    print(f"  Archive:   {tar_path} ({tar_size:,} bytes)")
    print("=" * 70)

    # Check hash uniqueness per sheet
    for sheet_key in SHEETS:
        hashes = [e["ods_sha256"] for e in manifest_entries
                  if e["sheet_key"] == sheet_key and e.get("ods_sha256")]
        unique = len(set(hashes))
        print(f"  {sheet_key}: {unique} unique / {len(hashes)} total")
        if unique == len(hashes):
            print(f"    ✓ All revisions have different content")
        elif unique == 1:
            print(f"    ✗ All identical — exportLinks may not be revision-specific for ODS")
        else:
            print(f"    ~ Some duplicates (expected for revisions that map to same workflow)")

    print()
    print("Next steps:")
    print("  git add .claude/swap/revision-ods.tar.gz")
    print("  git commit -m 'Step 4: ODS exports for key revisions'")
    print("  git push -u origin claude/google-sheets-history-cQ6AV")


if __name__ == "__main__":
    main()
