#!/usr/bin/env python3
"""
PoC: Test if files.download endpoint returns different content per revision.

Our previous script used files.export (which ignores revisionId for Sheets).
The correct endpoint is files.download (POST), which officially supports
revisionId for Google Sheets.

Usage:
    GOOGLE_ACCESS_TOKEN="ya29.a0..." python3 scripts/test-revision-download.py

Tests against ubl25_library where we KNOW content changed:
  - rev 1843 (Nov 12, 2025) — pre-CSD02 state
  - rev 1868 (Nov 19, 2025) — Customs definitions rewritten
  - rev 2005 (Jan 21, 2026) — post-CSD02, BuyerReference renamed

If the endpoint works, these three should produce DIFFERENT CSV hashes.

API reference:
  POST https://www.googleapis.com/drive/v3/files/{fileId}/download
    ?mimeType=text/csv
    &revisionId={revisionId}
  See: https://developers.google.com/workspace/drive/api/reference/rest/v3/files/download
"""

import os, sys, hashlib, json
from urllib.request import Request, urlopen
from urllib.error import HTTPError

TOKEN = os.environ.get("GOOGLE_ACCESS_TOKEN") or input("Access token: ").strip()
FILE_ID = "18o1YqjHWUw0-s8mb3ja4i99obOUhs-4zpgso6RZrGaY"  # ubl25_library

# Revisions we know should differ (from our earlier analysis)
TEST_REVISIONS = [
    ("1843", "2025-11-12", "V1 — initial CSD02 working copy"),
    ("1868", "2025-11-19", "V2 — Customs definitions rewritten"),
    ("1899", "2025-11-20", "V3 — WasteMovement ABIE added"),
    ("2005", "2026-01-21", "V6-V8 — post-CSD02, BuyerReference renamed"),
]

MIME_CSV = "text/csv"
MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

def download_revision(file_id, revision_id, mime_type="text/csv"):
    """Use the files.download endpoint (POST) with revisionId."""
    url = (
        f"https://www.googleapis.com/drive/v3/files/{file_id}/download"
        f"?mimeType={mime_type}"
        f"&revisionId={revision_id}"
    )
    headers = {"Authorization": f"Bearer {TOKEN}"}
    req = Request(url, method="POST", headers=headers)
    try:
        with urlopen(req, timeout=60) as resp:
            status = resp.status
            body = resp.read()
            # files.download returns an Operation object for long-running ops
            # Check if we got JSON (operation) or binary (direct download)
            content_type = resp.headers.get("Content-Type", "")
            return {
                "status": status,
                "content_type": content_type,
                "size": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "body": body,
            }
    except HTTPError as e:
        body = e.read().decode(errors="replace")
        return {
            "status": e.code,
            "error": body[:500],
            "size": 0,
            "sha256": None,
            "body": None,
        }

def try_export_with_revision(file_id, revision_id, mime_type="text/csv"):
    """Also try the v2 approach: GET revisions/{id} with alt=media."""
    url = (
        f"https://www.googleapis.com/drive/v2/files/{file_id}"
        f"/revisions/{revision_id}"
    )
    headers = {"Authorization": f"Bearer {TOKEN}"}
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as resp:
            body = resp.read()
            data = json.loads(body)
            # v2 revision object should have exportLinks
            export_links = data.get("exportLinks", {})
            return {
                "status": resp.status,
                "export_links": export_links,
                "has_export_links": bool(export_links),
            }
    except HTTPError as e:
        return {
            "status": e.code,
            "error": e.read().decode(errors="replace")[:500],
        }

print("=" * 70)
print("PoC: Testing files.download with revisionId for Google Sheets")
print("=" * 70)
print(f"File: ubl25_library ({FILE_ID})")
print(f"Testing {len(TEST_REVISIONS)} revisions that should have different content")
print()

# --- Test 1: files.download (v3 POST) ---
print("--- Method 1: POST files.download (v3) ---")
results = []
for rev_id, date, description in TEST_REVISIONS:
    print(f"\n  rev {rev_id} ({date}): {description}")
    r = download_revision(FILE_ID, rev_id, MIME_CSV)
    print(f"    HTTP {r['status']}, size={r['size']}, content_type={r.get('content_type','?')}")
    if r["sha256"]:
        print(f"    sha256={r['sha256'][:24]}...")
    if r.get("error"):
        print(f"    ERROR: {r['error'][:200]}")
    # If we got JSON back (Operation object), show it
    if r["body"] and r.get("content_type", "").startswith("application/json"):
        try:
            op = json.loads(r["body"])
            print(f"    Operation: {json.dumps(op, indent=2)[:300]}")
        except:
            pass
    results.append(r)

# Compare hashes
hashes = [r["sha256"] for r in results if r["sha256"]]
if hashes:
    unique = set(hashes)
    print(f"\n  RESULT: {len(unique)} unique hashes out of {len(hashes)} downloads")
    if len(unique) > 1:
        print("  *** SUCCESS: Different revisions return different content! ***")
    else:
        print("  Same content for all revisions (endpoint may not support revision param)")

# --- Test 2: Drive v2 revision metadata (to get exportLinks) ---
print("\n--- Method 2: GET revisions/{id} (v2) for exportLinks ---")
first_rev = TEST_REVISIONS[0][0]
print(f"  Testing rev {first_rev}...")
r2 = try_export_with_revision(FILE_ID, first_rev)
print(f"  HTTP {r2.get('status')}")
if r2.get("has_export_links"):
    print(f"  exportLinks found:")
    for fmt, link in r2["export_links"].items():
        print(f"    {fmt}: {link[:80]}...")
    # Try downloading via exportLinks
    csv_link = r2["export_links"].get("text/csv")
    if csv_link:
        print(f"\n  Downloading CSV via exportLink...")
        try:
            req = Request(csv_link, headers={"Authorization": f"Bearer {TOKEN}"})
            with urlopen(req, timeout=60) as resp:
                body = resp.read()
                h = hashlib.sha256(body).hexdigest()
                print(f"    size={len(body)}, sha256={h[:24]}...")
        except HTTPError as e:
            print(f"    ERROR {e.code}: {e.read().decode(errors='replace')[:200]}")
elif r2.get("error"):
    print(f"  ERROR: {r2['error'][:300]}")
else:
    print(f"  No exportLinks in response")

# --- Test 3: Also try a second revision via v2 exportLinks for comparison ---
if r2.get("has_export_links"):
    last_rev = TEST_REVISIONS[-1][0]
    print(f"\n  Testing rev {last_rev} via v2...")
    r3 = try_export_with_revision(FILE_ID, last_rev)
    if r3.get("has_export_links"):
        csv_link2 = r3["export_links"].get("text/csv")
        if csv_link2:
            print(f"  Downloading CSV via exportLink...")
            try:
                req = Request(csv_link2, headers={"Authorization": f"Bearer {TOKEN}"})
                with urlopen(req, timeout=60) as resp:
                    body = resp.read()
                    h = hashlib.sha256(body).hexdigest()
                    print(f"    size={len(body)}, sha256={h[:24]}...")
            except HTTPError as e:
                print(f"    ERROR {e.code}: {e.read().decode(errors='replace')[:200]}")

print("\n" + "=" * 70)
print("Done. If any method produced different hashes, that's our path forward.")
print("=" * 70)
