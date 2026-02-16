#!/usr/bin/env python3
"""
Fetch Google Sheets revision metadata (timestamps + authors) for UBL sheets.
Run this on your LOCAL machine (not GCP) — googleapis.com is blocked from GCP IPs.

Usage:
    python3 fetch-revision-metadata.py

Output:
    revision-metadata.json.gz  (~200-500KB compressed)

Paste/upload that file back to the Claude Code session.

Requirements:
    pip install requests   (or use system python3 with urllib — see below)
"""

import json, gzip, sys, time

# --- Use requests if available, fall back to urllib ---
try:
    import requests
    def http_get(url, headers):
        r = requests.get(url, headers=headers, timeout=30)
        return r.status_code, r.json() if r.status_code == 200 else r.text
except ImportError:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
    def http_get(url, headers):
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read())
        except HTTPError as e:
            return e.code, e.read().decode()

# --- Configuration ---
# Set via environment variable or you'll be prompted:
#   export GOOGLE_ACCESS_TOKEN="ya29.a0..."
import os
ACCESS_TOKEN = os.environ.get("GOOGLE_ACCESS_TOKEN") or input("Access token: ").strip()

SHEETS = {
    "ubl25_library":  "18o1YqjHWUw0-s8mb3ja4i99obOUhs-4zpgso6RZrGaY",
    "ubl25_documents": "1024Th-Uj8cqliNEJc-3pDOR7DxAAW7gCG4e-pbtarsg",
    "ubl24_library":  "1kxlFLz2thJOlvpq2ChRAcv76SiKgEIRtoVRqsZ7OBUs",
    "ubl24_documents": "1GNpHCS7_QkJtP3QIOdPJWL5N3kQ1EzPznT6M8sPsA0Y",
}

FOLDER_ID = "0B4X4evii3UjcdG5wNlVFTXlaYVU"

def get_access_token():
    """Return the access token provided by the user."""
    return ACCESS_TOKEN

def get_all_revisions(file_id, token):
    """Paginate through all revisions of a file."""
    all_revisions = []
    page_token = None

    while True:
        url = (
            f"https://www.googleapis.com/drive/v3/files/{file_id}/revisions"
            f"?pageSize=1000"
            f"&fields=nextPageToken,revisions(id,modifiedTime,lastModifyingUser/displayName,size)"
        )
        if page_token:
            url += f"&pageToken={page_token}"

        status, data = http_get(url, {"Authorization": f"Bearer {token}"})

        if status != 200:
            print(f"  ERROR {status}: {str(data)[:200]}")
            break

        revisions = data.get("revisions", [])
        all_revisions.extend(revisions)
        print(f"  Fetched {len(revisions)} revisions (total: {len(all_revisions)})")

        page_token = data.get("nextPageToken")
        if not page_token:
            break
        time.sleep(0.5)

    return all_revisions

def list_folder(folder_id, token):
    """List files in a Drive folder."""
    url = (
        f"https://www.googleapis.com/drive/v3/files"
        f"?q='{folder_id}'+in+parents"
        f"&fields=files(id,name,mimeType,modifiedTime,size)"
        f"&pageSize=100"
    )
    status, data = http_get(url, {"Authorization": f"Bearer {token}"})
    if status == 200:
        return data.get("files", [])
    else:
        print(f"Folder listing failed ({status}): {str(data)[:200]}")
        return []

def main():
    print("=== UBL Google Sheets Revision Metadata Fetcher ===\n")

    token = get_access_token()
    if not token:
        print("ERROR: No access token provided.")
        sys.exit(1)
    print(f"Using token: {token[:20]}...\n")

    output = {"sheets": {}, "folder": None, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    # Fetch revisions for each sheet
    for name, file_id in SHEETS.items():
        print(f"Fetching revisions for {name} ({file_id[:12]}...)...")
        revisions = get_all_revisions(file_id, token)
        output["sheets"][name] = {
            "file_id": file_id,
            "revision_count": len(revisions),
            "revisions": revisions,
        }
        print(f"  Done: {len(revisions)} revisions\n")
        time.sleep(1)

    # List folder contents
    print(f"Listing OASIS TC folder ({FOLDER_ID[:12]}...)...")
    files = list_folder(FOLDER_ID, token)
    output["folder"] = {
        "folder_id": FOLDER_ID,
        "file_count": len(files),
        "files": files,
    }
    print(f"  Found {len(files)} files\n")

    # Write output
    outfile = "revision-metadata.json.gz"
    with gzip.open(outfile, "wt", encoding="utf-8") as f:
        json.dump(output, f, indent=1)

    # Also write uncompressed for easy inspection
    with open("revision-metadata.json", "w") as f:
        json.dump(output, f, indent=1)

    import os
    gz_size = os.path.getsize(outfile)
    json_size = os.path.getsize("revision-metadata.json")

    print(f"=== Done! ===")
    print(f"  revision-metadata.json:    {json_size:,} bytes")
    print(f"  revision-metadata.json.gz: {gz_size:,} bytes")
    print(f"\nUpload revision-metadata.json.gz to the Claude Code session.")

    # Quick summary
    total = sum(s["revision_count"] for s in output["sheets"].values())
    print(f"\nTotal revisions across all sheets: {total}")
    for name, data in output["sheets"].items():
        revs = data["revisions"]
        if revs:
            first = revs[0].get("modifiedTime", "?")
            last = revs[-1].get("modifiedTime", "?")
            print(f"  {name}: {data['revision_count']} revisions, {first} → {last}")

if __name__ == "__main__":
    main()
