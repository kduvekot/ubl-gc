#!/usr/bin/env python3
"""
Download specific revision ODS files from the public Google Drive folder.

The Colab slow-validation notebook stores revision snapshots as rev-{N}.ods.gz
in a public Google Drive folder. This script downloads them by:
1. Listing the folder contents to get file IDs
2. Downloading specific revisions by filename match

Usage:
    python3 work-sheets/scripts/download-drive-revisions.py --first 10
    python3 work-sheets/scripts/download-drive-revisions.py --revisions 1,2,3,5,10
    python3 work-sheets/scripts/download-drive-revisions.py --sheet library --first 10
    python3 work-sheets/scripts/download-drive-revisions.py --sheet documents --first 5

Output goes to /tmp/ubl-revisions/{sheet}/ as decompressed .ods files.
"""

import argparse
import gzip
import json
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

# Public Google Drive folder IDs (from method-c-slow-validation notebook)
DRIVE_FOLDERS = {
    "library": "1JRvRaqsNP_G-9xICwrgGpY-ArwV8ej1w",    # ubl25_library ODS files
    "documents": "1DsufM2yMqcbE8kR-RH1i5rSBcvPivOxA",   # ubl25_documents ODS files
}

OUTPUT_BASE = Path("/tmp/ubl-revisions")


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
                # Extract confirm token and retry
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


def main():
    parser = argparse.ArgumentParser(
        description="Download revision ODS files from public Google Drive"
    )
    parser.add_argument(
        "--sheet", choices=["library", "documents"], default="library",
        help="Which sheet's revisions to download (default: library)"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Download all revisions found in the folder listing"
    )
    parser.add_argument(
        "--first", type=int, default=10,
        help="Download the first N revisions (default: 10)"
    )
    parser.add_argument(
        "--revisions", type=str,
        help="Comma-separated list of specific revision numbers to download"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output directory (default: /tmp/ubl-revisions/{sheet})"
    )
    parser.add_argument(
        "--list-only", action="store_true",
        help="Only list folder contents, don't download"
    )
    args = parser.parse_args()

    folder_id = DRIVE_FOLDERS[args.sheet]
    outdir = Path(args.output) if args.output else OUTPUT_BASE / args.sheet
    outdir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"Download Revision ODS from Google Drive")
    print("=" * 70)
    print(f"  Sheet:   {args.sheet}")
    print(f"  Folder:  {folder_id}")
    print(f"  Output:  {outdir}")
    print()

    # List folder contents
    entries = list_drive_folder(folder_id)

    if args.list_only:
        for e in sorted(entries, key=lambda x: x.get("name", "")):
            print(f"  {e['name']:40s}  id={e['id']}")
        return

    if not entries:
        print("\n  The embed view returned no entries.")
        print("  This can happen with very large folders (2000+ files).")
        print("  Falling back to direct API approach...")
        print()

    # Parse all revision entries from the listing
    file_map = {}  # rev_num -> {id, name}
    for entry in entries:
        name = entry.get("name", "")
        match = re.match(r"rev-(\d+)\.ods\.gz$", name)
        if match:
            file_map[int(match.group(1))] = entry

    print(f"  Listing contains {len(file_map)} revision files")

    # Filter to requested revisions
    if args.all:
        # Download everything in the listing — no probing needed
        print(f"  Mode: --all (downloading all {len(file_map)} listed revisions)")
    elif args.revisions:
        wanted = set(int(r) for r in args.revisions.split(","))
        file_map = {k: v for k, v in file_map.items() if k in wanted}
        print(f"  Mode: --revisions ({len(file_map)} of {len(wanted)} requested found in listing)")
    else:
        wanted = set(range(1, args.first + 1))
        file_map = {k: v for k, v in file_map.items() if k in wanted}
        print(f"  Mode: --first {args.first} ({len(file_map)} found in listing)")

    if not file_map and not entries:
        # Empty listing — try direct API as last resort
        if args.revisions:
            wanted = set(int(r) for r in args.revisions.split(","))
        else:
            wanted = set(range(1, args.first + 1))
        entries = list_drive_folder_api(folder_id, wanted)
        for entry in entries:
            name = entry.get("name", "")
            match = re.match(r"rev-(\d+)\.ods\.gz$", name)
            if match:
                file_map[int(match.group(1))] = entry
        print(f"  Fallback API found {len(file_map)} revisions")

    # Download each revision
    print(f"\n  Downloading {len(file_map)} revisions...\n")
    downloaded = 0
    errors = 0

    for rev_num in sorted(file_map.keys()):
        entry = file_map[rev_num]
        gz_path = outdir / f"rev-{rev_num}.ods.gz"
        ods_path = outdir / f"rev-{rev_num}.ods"

        # Skip if already downloaded and decompressed
        if ods_path.exists() and ods_path.stat().st_size > 1000:
            print(f"  rev-{rev_num:>5}: skip (already at {ods_path}, "
                  f"{ods_path.stat().st_size:,} bytes)")
            downloaded += 1
            continue

        print(f"  rev-{rev_num:>5}: downloading {entry['name']}...", end="", flush=True)
        try:
            size = download_drive_file(entry["id"], gz_path)
            print(f" {size:,} gz bytes", end="", flush=True)

            # Decompress
            gz_data = gz_path.read_bytes()
            ods_data = gzip.decompress(gz_data)
            ods_path.write_bytes(ods_data)
            print(f" -> {len(ods_data):,} ods bytes")

            # Keep the .gz too for reference, but the .ods is what we diff
            downloaded += 1

        except Exception as e:
            print(f" ERROR: {e}")
            errors += 1

        time.sleep(0.5)  # Be kind to Drive

    print(f"\n{'='*70}")
    print(f"Done: {downloaded} downloaded, {errors} errors")
    print(f"Files in: {outdir}")
    print(f"{'='*70}")

    # List what we got
    ods_files = sorted(outdir.glob("rev-*.ods"))
    print(f"\nODS files available:")
    for f in ods_files:
        print(f"  {f.name:25s}  {f.stat().st_size:>10,} bytes")


def list_drive_folder_api(folder_id, wanted_revs):
    """Fallback: use Google Drive API v3 to search for specific files.
    Works for public folders without auth by using the files.list endpoint
    with a query filter. Requires files to be publicly shared."""
    entries = []
    for rev_num in sorted(wanted_revs):
        entry = find_file_in_folder_api(folder_id, f"rev-{rev_num}.ods.gz")
        if entry:
            entries.append(entry)
    return entries


def find_file_in_folder_api(folder_id, filename):
    """Search for a specific file in a public Drive folder using the API.
    Uses the Drive v3 files.list with q parameter."""
    import urllib.parse

    # Method 1: Try the Google Drive API v3 (needs API key for public access)
    # Since we don't have an API key, we'll try the export download URL directly
    # by constructing a search URL

    # Method 2: Try constructing a direct search via Google
    # Actually, for public files we can try a workaround:
    # use the file search through the Drive web interface

    # Method 3: Simplest - if we know the folder structure, we can try to
    # access the file directly. Google Drive doesn't support this by path,
    # but we can try the API without a key for truly public files.

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


if __name__ == "__main__":
    main()
