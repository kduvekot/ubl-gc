#!/usr/bin/env python3
"""
Deep discovery of ALL files and revision history in the UBL OASIS Google Drive folder.

Recursively explores subfolders, fetches revision history for every spreadsheet,
and captures detailed metadata including who changed what and when.

PROVENANCE: Every API call is logged with its exact URL, timestamp, and HTTP status
so anyone with the correct Google Drive access can independently reproduce these results.

Usage:
    GOOGLE_ACCESS_TOKEN="ya29.a0..." python3 discover-drive-history.py

Output:
    drive-discovery.json.gz   (compressed, upload to Claude Code session)
    drive-discovery.json      (human-readable)

How to reproduce:
    1. Visit https://developers.google.com/oauthplayground/
    2. Authorize scope: https://www.googleapis.com/auth/drive.readonly
    3. Exchange authorization code for tokens
    4. Export the access token:
         export GOOGLE_ACCESS_TOKEN="ya29.a0..."
    5. Run this script from your local machine (NOT from a GCP VM —
       googleapis.com blocks many GCP IP ranges)
    6. Compare output against the committed drive-discovery.json.gz

    The Google Drive folder is the OASIS UBL TC shared folder:
    https://drive.google.com/drive/folders/0B4X4evii3UjcdG5wNlVFTXlaYVU

Requirements:
    Python 3.7+
    pip install requests   (optional — falls back to stdlib urllib)
"""

import json, gzip, sys, time, os
from datetime import datetime, timezone

# --- HTTP layer (requests preferred, urllib fallback) ---
try:
    import requests as _requests_lib
    _HTTP_LIB = "requests"
    def _http_get_raw(url, headers):
        r = _requests_lib.get(url, headers=headers, timeout=30)
        if r.status_code == 200:
            return r.status_code, r.json()
        return r.status_code, r.text
except ImportError:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
    _HTTP_LIB = "urllib"
    def _http_get_raw(url, headers):
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read())
        except HTTPError as e:
            return e.code, e.read().decode()

# --- Config ---
ACCESS_TOKEN = os.environ.get("GOOGLE_ACCESS_TOKEN") or input("Access token: ").strip()
ROOT_FOLDER_ID = "0B4X4evii3UjcdG5wNlVFTXlaYVU"

# Google Drive API documentation references:
# - Files.list:      https://developers.google.com/drive/api/v3/reference/files/list
# - Revisions.list:  https://developers.google.com/drive/api/v3/reference/revisions/list
# - Files.get:       https://developers.google.com/drive/api/v3/reference/files/get

# Rate limiting: stay well under 1000 req/100s quota
API_DELAY = 0.3  # seconds between API calls

# --- Provenance log: records every API call for reproducibility ---
api_log = []


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _sanitize_url(url):
    """Return the URL with the access token removed (for safe logging)."""
    # The token is in the Authorization header, not the URL, so URL is safe.
    # But just in case someone constructs a URL with key= param:
    if "key=" in url:
        import re
        return re.sub(r'key=[^&]+', 'key=REDACTED', url)
    return url


def api_get(url, context=""):
    """Authenticated GET with rate limiting, retry, and provenance logging."""
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    safe_url = _sanitize_url(url)

    for attempt in range(4):
        call_time = _now_iso()
        status, data = _http_get_raw(url, headers)

        log_entry = {
            "timestamp": call_time,
            "url": safe_url,
            "status": status,
            "attempt": attempt + 1,
            "context": context,
        }

        if status == 200:
            log_entry["result"] = "ok"
            api_log.append(log_entry)
            time.sleep(API_DELAY)
            return data

        if status == 429 or status >= 500:
            wait = 2 ** (attempt + 1)
            log_entry["result"] = f"retry_after_{wait}s"
            api_log.append(log_entry)
            print(f"    Rate limited/error ({status}), waiting {wait}s...")
            time.sleep(wait)
            continue

        log_entry["result"] = f"error"
        log_entry["error_preview"] = str(data)[:300]
        api_log.append(log_entry)
        print(f"    ERROR {status}: {str(data)[:200]}")
        return None

    api_log.append({
        "timestamp": _now_iso(),
        "url": safe_url,
        "status": "failed_all_retries",
        "context": context,
    })
    print(f"    FAILED after 4 retries")
    return None


def list_folder_paginated(folder_id):
    """List ALL files in a folder, handling pagination."""
    all_files = []
    page_token = None
    page = 0

    while True:
        page += 1
        url = (
            f"https://www.googleapis.com/drive/v3/files"
            f"?q=%27{folder_id}%27+in+parents+and+trashed%3Dfalse"
            f"&fields=nextPageToken,files(id,name,mimeType,modifiedTime,createdTime,size,"
            f"owners/displayName,owners/emailAddress,"
            f"lastModifyingUser/displayName,lastModifyingUser/emailAddress,"
            f"shared,webViewLink)"
            f"&pageSize=100"
            f"&orderBy=name"
        )
        if page_token:
            url += f"&pageToken={page_token}"

        data = api_get(url, context=f"list_folder:{folder_id}:page{page}")
        if not data:
            break

        files = data.get("files", [])
        all_files.extend(files)

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return all_files


def get_all_revisions(file_id, file_name):
    """Fetch complete revision history for a file."""
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

        data = api_get(url, context=f"revisions:{file_id}:{file_name}:page{page}")
        if not data:
            break

        revisions = data.get("revisions", [])
        all_revisions.extend(revisions)

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return all_revisions


def explore_folder(folder_id, folder_name, path="/", depth=0):
    """Recursively explore a folder and all its contents."""
    indent = "  " * depth
    print(f"{indent}[folder] {folder_name} ({folder_id[:12]}...)")

    files = list_folder_paginated(folder_id)
    print(f"{indent}   Found {len(files)} items")

    result = {
        "id": folder_id,
        "name": folder_name,
        "path": path,
        "type": "folder",
        "children": [],
    }

    for f in files:
        mime = f.get("mimeType", "")
        name = f.get("name", "?")
        fid = f.get("id", "")
        child_path = f"{path}{name}"

        entry = {
            "id": fid,
            "name": name,
            "path": child_path,
            "mimeType": mime,
            "modifiedTime": f.get("modifiedTime"),
            "createdTime": f.get("createdTime"),
            "size": f.get("size"),
            "owners": f.get("owners"),
            "lastModifyingUser": f.get("lastModifyingUser"),
            "webViewLink": f.get("webViewLink"),
        }

        if mime == "application/vnd.google-apps.folder":
            subfolder = explore_folder(fid, name, path=f"{child_path}/", depth=depth + 1)
            entry["children"] = subfolder["children"]
            entry["type"] = "folder"

        elif mime == "application/vnd.google-apps.spreadsheet":
            print(f"{indent}   [spreadsheet] {name}")
            revisions = get_all_revisions(fid, name)
            entry["type"] = "spreadsheet"
            entry["revision_count"] = len(revisions)
            entry["revisions"] = revisions
            if revisions:
                entry["first_revision"] = revisions[0].get("modifiedTime")
                entry["last_revision"] = revisions[-1].get("modifiedTime")
                authors = set()
                for rev in revisions:
                    user = rev.get("lastModifyingUser", {})
                    dn = user.get("displayName") or user.get("emailAddress")
                    if dn:
                        authors.add(dn)
                entry["unique_authors"] = sorted(authors)
            print(f"{indent}     -> {len(revisions)} revisions, authors: {entry.get('unique_authors', [])}")

        elif mime == "application/vnd.google-apps.shortcut":
            entry["type"] = "shortcut"
            print(f"{indent}   [shortcut] {name}")
            target_url = (
                f"https://www.googleapis.com/drive/v3/files/{fid}"
                f"?fields=shortcutDetails(targetId,targetMimeType,targetResourceKey)"
            )
            target_data = api_get(target_url, context=f"shortcut_resolve:{fid}:{name}")
            if target_data and "shortcutDetails" in target_data:
                entry["shortcutTarget"] = target_data["shortcutDetails"]
                tid = target_data["shortcutDetails"].get("targetId", "?")
                tmime = target_data["shortcutDetails"].get("targetMimeType", "?")
                print(f"{indent}     -> points to {tid} ({tmime})")

                # If shortcut points to a spreadsheet, fetch its revisions too
                if tmime == "application/vnd.google-apps.spreadsheet":
                    print(f"{indent}     -> following shortcut to fetch spreadsheet revisions")
                    revisions = get_all_revisions(tid, f"[via shortcut] {name}")
                    entry["shortcutTarget"]["revision_count"] = len(revisions)
                    entry["shortcutTarget"]["revisions"] = revisions
                    if revisions:
                        entry["shortcutTarget"]["first_revision"] = revisions[0].get("modifiedTime")
                        entry["shortcutTarget"]["last_revision"] = revisions[-1].get("modifiedTime")
                    print(f"{indent}       -> {len(revisions)} revisions")

        else:
            entry["type"] = "other"
            print(f"{indent}   [file] {name} ({mime})")

        result["children"].append(entry)

    return result


def count_items(tree):
    """Count spreadsheets and total revisions in the tree."""
    total_spreadsheets = 0
    total_revisions = 0
    total_files = 0
    total_folders = 0
    total_shortcuts = 0

    for child in tree.get("children", []):
        t = child.get("type")
        if t == "folder":
            total_folders += 1
            s, r, fi, fo, sh = count_items(child)
            total_spreadsheets += s
            total_revisions += r
            total_files += fi
            total_folders += fo
            total_shortcuts += sh
        elif t == "spreadsheet":
            total_spreadsheets += 1
            total_revisions += child.get("revision_count", 0)
            # Count shortcut-target revisions too
        elif t == "shortcut":
            total_shortcuts += 1
            target = child.get("shortcutTarget", {})
            total_revisions += target.get("revision_count", 0)
        else:
            total_files += 1

    return total_spreadsheets, total_revisions, total_files, total_folders, total_shortcuts


def print_summary(tree, depth=0):
    """Print a human-readable summary."""
    indent = "  " * depth
    for child in tree.get("children", []):
        t = child.get("type")
        name = child.get("name", "?")

        if t == "folder":
            print(f"{indent}  {name}/")
            print_summary(child, depth + 1)
        elif t == "spreadsheet":
            rc = child.get("revision_count", 0)
            authors = ", ".join(child.get("unique_authors", []))
            period = ""
            if child.get("first_revision") and child.get("last_revision"):
                period = f" ({child['first_revision'][:10]} -> {child['last_revision'][:10]})"
            print(f"{indent}  {name}: {rc} revisions{period}")
            if authors:
                print(f"{indent}    Authors: {authors}")
        elif t == "shortcut":
            target = child.get("shortcutTarget", {})
            tid = target.get("targetId", "?")
            rc = target.get("revision_count", 0)
            extra = f" ({rc} revisions)" if rc else ""
            print(f"{indent}  {name} -> {tid}{extra}")
        else:
            print(f"{indent}  {name}")


def main():
    print("=" * 70)
    print("UBL OASIS Google Drive - Deep Discovery with Provenance Tracking")
    print("=" * 70)
    print()
    print("This script records every Google Drive API call it makes so that")
    print("anyone with read access to the OASIS UBL TC shared folder can")
    print("independently verify and reproduce these results.")
    print()

    if not ACCESS_TOKEN:
        print("ERROR: Set GOOGLE_ACCESS_TOKEN environment variable")
        print()
        print("How to get a token:")
        print("  1. Go to https://developers.google.com/oauthplayground/")
        print("  2. Authorize: https://www.googleapis.com/auth/drive.readonly")
        print("  3. Exchange code for tokens")
        print("  4. export GOOGLE_ACCESS_TOKEN='ya29.a0...'")
        sys.exit(1)

    start_time = _now_iso()
    print(f"Started:      {start_time}")
    print(f"Token:        {ACCESS_TOKEN[:20]}...{ACCESS_TOKEN[-4:]}")
    print(f"HTTP library: {_HTTP_LIB}")
    print(f"Root folder:  {ROOT_FOLDER_ID}")
    print(f"Folder URL:   https://drive.google.com/drive/folders/{ROOT_FOLDER_ID}")
    print()

    # Phase 1: Recursive exploration
    print("Phase 1: Recursive folder exploration + revision history fetch")
    print("-" * 70)
    tree = explore_folder(ROOT_FOLDER_ID, "UBL TC (root)")

    end_time = _now_iso()

    # Phase 2: Statistics
    sheets, revs, files, folders, shortcuts = count_items(tree)

    print()
    print("=" * 70)
    print("DISCOVERY RESULTS")
    print("=" * 70)
    print_summary(tree)
    print()
    print(f"Statistics:")
    print(f"  Spreadsheets:   {sheets}")
    print(f"  Total revisions: {revs}")
    print(f"  Other files:    {files}")
    print(f"  Folders:        {folders}")
    print(f"  Shortcuts:      {shortcuts}")
    print(f"  API calls made: {len(api_log)}")

    # Phase 3: Write output with full provenance
    output = {
        "_provenance": {
            "description": "Deep discovery of the OASIS UBL TC Google Drive shared folder",
            "purpose": "Capture complete file inventory and revision history for UBL standardization research",
            "how_to_reproduce": [
                "1. Visit https://developers.google.com/oauthplayground/",
                "2. Authorize scope: https://www.googleapis.com/auth/drive.readonly",
                "3. Exchange authorization code for access token",
                "4. export GOOGLE_ACCESS_TOKEN='ya29.a0...'",
                "5. python3 discover-drive-history.py",
                "NOTE: Must run from a non-GCP IP (googleapis.com blocks many GCP ranges)",
            ],
            "root_folder_url": f"https://drive.google.com/drive/folders/{ROOT_FOLDER_ID}",
            "root_folder_id": ROOT_FOLDER_ID,
            "apis_used": [
                "https://developers.google.com/drive/api/v3/reference/files/list",
                "https://developers.google.com/drive/api/v3/reference/revisions/list",
                "https://developers.google.com/drive/api/v3/reference/files/get",
            ],
            "script": "scripts/discover-drive-history.py",
            "script_version": "1.0.0",
            "started_at": start_time,
            "completed_at": end_time,
            "http_library": _HTTP_LIB,
            "python_version": sys.version,
        },
        "stats": {
            "total_spreadsheets": sheets,
            "total_revisions": revs,
            "total_other_files": files,
            "total_folders": folders,
            "total_shortcuts": shortcuts,
            "total_api_calls": len(api_log),
        },
        "tree": tree,
        "api_log": api_log,
    }

    outfile_gz = "drive-discovery.json.gz"
    outfile_json = "drive-discovery.json"

    with gzip.open(outfile_gz, "wt", encoding="utf-8") as f:
        json.dump(output, f, indent=1)

    with open(outfile_json, "w") as f:
        json.dump(output, f, indent=1)

    gz_size = os.path.getsize(outfile_gz)
    json_size = os.path.getsize(outfile_json)

    print(f"\nOutput files:")
    print(f"  {outfile_json}:    {json_size:,} bytes")
    print(f"  {outfile_gz}: {gz_size:,} bytes")
    print()
    print("To upload to the repo:")
    print(f"  cp {outfile_gz} .claude/swap/")
    print(f"  git add .claude/swap/{outfile_gz}")
    print(f"  git commit -m 'Add deep drive discovery data'")
    print(f"  git push")


if __name__ == "__main__":
    main()
