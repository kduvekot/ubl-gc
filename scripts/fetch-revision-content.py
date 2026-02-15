#!/usr/bin/env python3
"""
Download the actual content of each Google Sheets revision for diffing.

This gives us what the Google Sheets "Version history" UI shows:
cell-level changes across time — who changed what, when.

For each revision of each tracked sheet, this script exports the spreadsheet
as XLSX (preserving all tabs) so consecutive revisions can be diffed.

PROVENANCE: Every API call and download is logged with URL, timestamp,
status, and file hash so results are independently reproducible.

Usage:
    # First run: discovers revisions and downloads all of them
    GOOGLE_ACCESS_TOKEN="ya29.a0..." python3 fetch-revision-content.py

    # Resume after interruption (skips already-downloaded revisions)
    GOOGLE_ACCESS_TOKEN="ya29.a0..." python3 fetch-revision-content.py --resume

    # Download only a specific sheet
    GOOGLE_ACCESS_TOKEN="ya29.a0..." python3 fetch-revision-content.py --sheet ubl25_library

    # Limit to last N revisions (useful for testing)
    GOOGLE_ACCESS_TOKEN="ya29.a0..." python3 fetch-revision-content.py --last 5

Output:
    revision-exports/
      {sheet_key}/
        rev-{id}-{timestamp}.xlsx     # Full spreadsheet at this revision
        rev-{id}-{timestamp}.csv      # First sheet tab as CSV (for quick diff)
      manifest.json                   # Index of all downloads with hashes
    revision-exports.tar.gz           # Compressed archive of everything

How to reproduce:
    1. Visit https://developers.google.com/oauthplayground/
    2. Authorize scope: https://www.googleapis.com/auth/drive.readonly
    3. Exchange authorization code for access token
    4. export GOOGLE_ACCESS_TOKEN="ya29.a0..."
    5. python3 fetch-revision-content.py
    NOTE: Must run from a non-GCP IP (googleapis.com blocks many GCP ranges)

Requirements:
    Python 3.7+
    pip install requests   (optional — falls back to stdlib urllib)
"""

import json, sys, time, os, hashlib, argparse
from datetime import datetime, timezone
from pathlib import Path

# --- HTTP layer ---
try:
    import requests as _req_lib
    _HTTP_LIB = "requests"

    def _http_get_json(url, headers):
        r = _req_lib.get(url, headers=headers, timeout=30)
        if r.status_code == 200:
            return r.status_code, r.json()
        return r.status_code, r.text

    def _http_get_binary(url, headers):
        r = _req_lib.get(url, headers=headers, timeout=60, stream=True)
        if r.status_code == 200:
            return r.status_code, r.content
        return r.status_code, r.text

except ImportError:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
    _HTTP_LIB = "urllib"

    def _http_get_json(url, headers):
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read())
        except HTTPError as e:
            return e.code, e.read().decode()

    def _http_get_binary(url, headers):
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=60) as resp:
                return resp.status, resp.read()
        except HTTPError as e:
            return e.code, e.read().decode()


# --- Config ---
ACCESS_TOKEN = os.environ.get("GOOGLE_ACCESS_TOKEN") or input("Access token: ").strip()

# Sheets to track — same as in fetch-revision-metadata.py
KNOWN_SHEETS = {
    "ubl25_library":   "18o1YqjHWUw0-s8mb3ja4i99obOUhs-4zpgso6RZrGaY",
    "ubl25_documents": "1024Th-Uj8cqliNEJc-3pDOR7DxAAW7gCG4e-pbtarsg",
    "ubl24_library":   "1kxlFLz2thJOlvpq2ChRAcv76SiKgEIRtoVRqsZ7OBUs",
    "ubl24_documents": "1GNpHCS7_QkJtP3QIOdPJWL5N3kQ1EzPznT6M8sPsA0Y",
}

# Google Drive API references:
# - Export file:       https://developers.google.com/drive/api/v3/reference/files/export
# - Revisions.get:    https://developers.google.com/drive/api/v3/reference/revisions/get
# - Revisions.list:   https://developers.google.com/drive/api/v3/reference/revisions/list

API_DELAY = 0.5   # seconds between downloads (be kind to Google)
EXPORT_DIR = Path("revision-exports")

# Provenance
api_log = []


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def api_get_json(url, context=""):
    """Authenticated JSON GET with retry and logging."""
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    for attempt in range(4):
        call_time = _now_iso()
        status, data = _http_get_json(url, headers)
        log = {"timestamp": call_time, "url": url, "status": status,
               "attempt": attempt + 1, "context": context}
        if status == 200:
            log["result"] = "ok"
            api_log.append(log)
            time.sleep(API_DELAY)
            return data
        if status == 429 or status >= 500:
            wait = 2 ** (attempt + 1)
            log["result"] = f"retry_after_{wait}s"
            api_log.append(log)
            print(f"      Rate limited ({status}), waiting {wait}s...")
            time.sleep(wait)
            continue
        log["result"] = "error"
        log["error_preview"] = str(data)[:300]
        api_log.append(log)
        print(f"      ERROR {status}: {str(data)[:200]}")
        return None
    return None


def api_download(url, context=""):
    """Authenticated binary GET with retry and logging."""
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    for attempt in range(4):
        call_time = _now_iso()
        status, data = _http_get_binary(url, headers)
        log = {"timestamp": call_time, "url": url, "status": status,
               "attempt": attempt + 1, "context": context}
        if status == 200:
            log["result"] = "ok"
            log["size"] = len(data)
            log["sha256"] = _sha256(data)
            api_log.append(log)
            time.sleep(API_DELAY)
            return data
        if status == 429 or status >= 500:
            wait = 2 ** (attempt + 1)
            log["result"] = f"retry_after_{wait}s"
            api_log.append(log)
            print(f"      Rate limited ({status}), waiting {wait}s...")
            time.sleep(wait)
            continue
        log["result"] = "error"
        log["error_preview"] = str(data)[:300] if isinstance(data, str) else "binary"
        api_log.append(log)
        print(f"      ERROR {status}: {str(data)[:200]}")
        return None
    return None


def get_revisions(file_id, sheet_name):
    """Fetch all revision metadata for a file."""
    all_revisions = []
    page_token = None
    page = 0

    while True:
        page += 1
        url = (
            f"https://www.googleapis.com/drive/v3/files/{file_id}/revisions"
            f"?pageSize=1000"
            f"&fields=nextPageToken,revisions(id,modifiedTime,"
            f"lastModifyingUser/displayName,lastModifyingUser/emailAddress,"
            f"size,exportLinks)"
        )
        if page_token:
            url += f"&pageToken={page_token}"

        data = api_get_json(url, context=f"list_revisions:{sheet_name}:page{page}")
        if not data:
            break

        revisions = data.get("revisions", [])
        all_revisions.extend(revisions)

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return all_revisions


def safe_timestamp(ts):
    """Convert ISO timestamp to filesystem-safe string."""
    return ts.replace(":", "").replace("-", "").replace(".", "_")[:19] if ts else "unknown"


def export_revision(file_id, revision_id, mime_type, context=""):
    """Export a specific revision in the given format.

    For Google Sheets, we use the export endpoint with a revision parameter.
    Two approaches that work:
    1. Use exportLinks from the revision metadata (if available)
    2. Use the files.export endpoint with revision parameter
    """
    # Approach: export the file at a specific revision
    # The Drive API v3 supports exporting a revision via:
    #   GET /drive/v3/files/{fileId}/export?mimeType=...&revision={revisionId}
    # Note: This is undocumented but works. If it fails, we fall back to exportLinks.

    url = (
        f"https://www.googleapis.com/drive/v3/files/{file_id}/export"
        f"?mimeType={mime_type}"
        f"&revision={revision_id}"
    )
    return api_download(url, context=context)


def download_revision_content(sheet_key, file_id, revision, outdir, manifest_entries):
    """Download a single revision as both XLSX and CSV."""
    rev_id = revision["id"]
    rev_time = revision.get("modifiedTime", "")
    rev_author = (revision.get("lastModifyingUser", {}).get("displayName")
                  or revision.get("lastModifyingUser", {}).get("emailAddress")
                  or "unknown")

    ts_safe = safe_timestamp(rev_time)
    base_name = f"rev-{rev_id}-{ts_safe}"

    # Check if already downloaded (for --resume)
    xlsx_path = outdir / f"{base_name}.xlsx"
    csv_path = outdir / f"{base_name}.csv"

    if xlsx_path.exists() and csv_path.exists():
        print(f"    [skip] {base_name} (already exists)")
        return True

    entry = {
        "sheet_key": sheet_key,
        "file_id": file_id,
        "revision_id": rev_id,
        "modified_time": rev_time,
        "author": rev_author,
        "files": {},
    }

    # Try XLSX export first
    print(f"    [xlsx] {base_name} ({rev_author})...", end="", flush=True)
    xlsx_data = export_revision(
        file_id, rev_id,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        context=f"export_xlsx:{sheet_key}:rev{rev_id}"
    )
    if xlsx_data:
        xlsx_path.write_bytes(xlsx_data)
        entry["files"]["xlsx"] = {
            "path": str(xlsx_path),
            "size": len(xlsx_data),
            "sha256": _sha256(xlsx_data),
        }
        print(f" {len(xlsx_data):,} bytes", flush=True)
    else:
        print(" FAILED", flush=True)
        # Try using exportLinks from revision metadata if available
        export_links = revision.get("exportLinks", {})
        xlsx_link = export_links.get(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        if xlsx_link:
            print(f"    [xlsx] retrying via exportLinks...", end="", flush=True)
            xlsx_data = api_download(xlsx_link, context=f"exportlink_xlsx:{sheet_key}:rev{rev_id}")
            if xlsx_data:
                xlsx_path.write_bytes(xlsx_data)
                entry["files"]["xlsx"] = {
                    "path": str(xlsx_path),
                    "size": len(xlsx_data),
                    "sha256": _sha256(xlsx_data),
                }
                print(f" {len(xlsx_data):,} bytes", flush=True)
            else:
                print(" FAILED", flush=True)

    # Try CSV export (just the first sheet tab)
    print(f"    [csv]  {base_name}...", end="", flush=True)
    csv_data = export_revision(
        file_id, rev_id,
        "text/csv",
        context=f"export_csv:{sheet_key}:rev{rev_id}"
    )
    if csv_data:
        csv_path.write_bytes(csv_data)
        entry["files"]["csv"] = {
            "path": str(csv_path),
            "size": len(csv_data),
            "sha256": _sha256(csv_data),
        }
        print(f" {len(csv_data):,} bytes", flush=True)
    else:
        print(" FAILED", flush=True)
        export_links = revision.get("exportLinks", {})
        csv_link = export_links.get("text/csv")
        if csv_link:
            print(f"    [csv]  retrying via exportLinks...", end="", flush=True)
            csv_data = api_download(csv_link, context=f"exportlink_csv:{sheet_key}:rev{rev_id}")
            if csv_data:
                csv_path.write_bytes(csv_data)
                entry["files"]["csv"] = {
                    "path": str(csv_path),
                    "size": len(csv_data),
                    "sha256": _sha256(csv_data),
                }
                print(f" {len(csv_data):,} bytes", flush=True)
            else:
                print(" FAILED", flush=True)

    manifest_entries.append(entry)
    return bool(entry["files"])


def main():
    parser = argparse.ArgumentParser(description="Download Google Sheets revision content")
    parser.add_argument("--resume", action="store_true",
                        help="Skip already-downloaded revisions")
    parser.add_argument("--sheet", type=str, choices=list(KNOWN_SHEETS.keys()),
                        help="Only process this sheet")
    parser.add_argument("--last", type=int, default=0,
                        help="Only download the last N revisions per sheet")
    parser.add_argument("--discover", action="store_true",
                        help="Also discover sheets from drive-discovery.json.gz if present")
    args = parser.parse_args()

    print("=" * 70)
    print("Google Sheets Revision Content Downloader")
    print("=" * 70)
    print()
    print("Downloads the actual spreadsheet content at each revision point,")
    print("giving us the same data shown in Google Sheets Version History UI")
    print("(who changed what cells, when).")
    print()

    if not ACCESS_TOKEN:
        print("ERROR: Set GOOGLE_ACCESS_TOKEN environment variable")
        sys.exit(1)

    start_time = _now_iso()
    print(f"Started:      {start_time}")
    print(f"Token:        {ACCESS_TOKEN[:20]}...{ACCESS_TOKEN[-4:]}")
    print(f"HTTP library: {_HTTP_LIB}")
    print(f"Resume mode:  {args.resume}")
    if args.last:
        print(f"Last N:       {args.last}")
    print()

    # Determine which sheets to process
    sheets_to_process = {}
    if args.sheet:
        sheets_to_process[args.sheet] = KNOWN_SHEETS[args.sheet]
    else:
        sheets_to_process = dict(KNOWN_SHEETS)

    # If --discover flag, also pick up any extra sheets from discovery data
    if args.discover:
        discovery_path = Path(".claude/swap/drive-discovery.json.gz")
        if discovery_path.exists():
            import gzip
            with gzip.open(discovery_path, "rt") as f:
                disc = json.load(f)
            # Walk the tree for spreadsheets not in KNOWN_SHEETS
            def find_sheets(node, found):
                for child in node.get("children", []):
                    if child.get("type") == "spreadsheet":
                        fid = child["id"]
                        if fid not in KNOWN_SHEETS.values():
                            key = child["name"].replace(" ", "_")[:40].lower()
                            found[key] = fid
                    elif child.get("type") == "folder":
                        find_sheets(child, found)
                    elif child.get("type") == "shortcut":
                        target = child.get("shortcutTarget", {})
                        if target.get("targetMimeType") == "application/vnd.google-apps.spreadsheet":
                            tid = target.get("targetId")
                            if tid and tid not in KNOWN_SHEETS.values():
                                key = f"shortcut_{child['name'].replace(' ', '_')[:30].lower()}"
                                found[key] = tid
            extra = {}
            find_sheets(disc.get("tree", {}), extra)
            if extra:
                print(f"Discovered {len(extra)} additional sheets from drive-discovery.json.gz:")
                for k, v in extra.items():
                    print(f"  {k}: {v}")
                sheets_to_process.update(extra)
            print()

    EXPORT_DIR.mkdir(exist_ok=True)
    manifest_entries = []
    total_downloaded = 0
    total_skipped = 0
    total_failed = 0

    for sheet_key, file_id in sheets_to_process.items():
        print(f"\n{'='*60}")
        print(f"Sheet: {sheet_key}")
        print(f"File ID: {file_id}")
        print(f"{'='*60}")

        # Create output directory
        sheet_dir = EXPORT_DIR / sheet_key
        sheet_dir.mkdir(exist_ok=True)

        # Get all revisions
        print(f"  Fetching revision list...")
        revisions = get_revisions(file_id, sheet_key)
        print(f"  Found {len(revisions)} revisions")

        if not revisions:
            print(f"  No revisions found, skipping")
            continue

        # Apply --last filter
        if args.last and args.last < len(revisions):
            print(f"  Limiting to last {args.last} revisions")
            revisions = revisions[-args.last:]

        # Show time range
        first_time = revisions[0].get("modifiedTime", "?")
        last_time = revisions[-1].get("modifiedTime", "?")
        print(f"  Time range: {first_time} -> {last_time}")
        print()

        # Download each revision
        for i, rev in enumerate(revisions, 1):
            rev_id = rev["id"]
            rev_time = rev.get("modifiedTime", "?")
            print(f"  [{i}/{len(revisions)}] Revision {rev_id} ({rev_time})")

            success = download_revision_content(
                sheet_key, file_id, rev, sheet_dir, manifest_entries
            )
            if success:
                total_downloaded += 1
            else:
                total_failed += 1

    # Write manifest
    manifest = {
        "_provenance": {
            "description": "Google Sheets revision content exports for UBL standardization research",
            "how_to_reproduce": [
                "1. Visit https://developers.google.com/oauthplayground/",
                "2. Authorize: https://www.googleapis.com/auth/drive.readonly",
                "3. Exchange code for access token",
                "4. GOOGLE_ACCESS_TOKEN='ya29...' python3 fetch-revision-content.py",
                "NOTE: Run from non-GCP IP; googleapis.com blocks many GCP ranges",
            ],
            "apis_used": [
                "https://developers.google.com/drive/api/v3/reference/revisions/list",
                "https://developers.google.com/drive/api/v3/reference/files/export",
            ],
            "script": "scripts/fetch-revision-content.py",
            "script_version": "1.0.0",
            "started_at": start_time,
            "completed_at": _now_iso(),
            "http_library": _HTTP_LIB,
            "python_version": sys.version,
            "args": {
                "resume": args.resume,
                "sheet": args.sheet,
                "last": args.last,
                "discover": args.discover,
            },
        },
        "sheets_processed": list(sheets_to_process.keys()),
        "stats": {
            "total_revisions_downloaded": total_downloaded,
            "total_skipped": total_skipped,
            "total_failed": total_failed,
            "total_api_calls": len(api_log),
        },
        "entries": manifest_entries,
        "api_log": api_log,
    }

    manifest_path = EXPORT_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n{'='*70}")
    print(f"DONE")
    print(f"{'='*70}")
    print(f"  Revisions downloaded: {total_downloaded}")
    print(f"  Revisions skipped:    {total_skipped}")
    print(f"  Revisions failed:     {total_failed}")
    print(f"  API calls made:       {len(api_log)}")
    print(f"  Manifest:             {manifest_path}")
    print(f"  Export directory:      {EXPORT_DIR}/")
    print()

    # Size summary
    total_size = sum(
        f.stat().st_size
        for f in EXPORT_DIR.rglob("*")
        if f.is_file()
    )
    print(f"  Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
    print()
    print("Next steps:")
    print("  1. Compress: tar czf revision-exports.tar.gz revision-exports/")
    print("  2. Upload to repo: cp revision-exports.tar.gz .claude/swap/")
    print("  3. Or just upload manifest.json for metadata-only analysis")


if __name__ == "__main__":
    main()
