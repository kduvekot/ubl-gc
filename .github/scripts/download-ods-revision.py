#!/usr/bin/env python3
"""
Download a specific revision of a UBL ODS spreadsheet from Google Drive.

The revisions are stored as gzipped ODS files (rev-{num}.ods.gz) in
public Google Drive folders.

Usage:
  python3 download-ods-revision.py <sheet-type> <revision> <output-path>

  sheet-type: "library" or "documents"
  revision:   revision number (e.g., 1533)
  output-path: where to save the ODS file

Examples:
  python3 download-ods-revision.py library 1533 /tmp/UBL-Library-Google.ods
  python3 download-ods-revision.py documents 2190 /tmp/UBL-Documents-Google.ods
"""

import gzip
import json
import os
import re
import sys
import time
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

# Google Drive folder IDs for the archived ODS revisions
DRIVE_FOLDERS = {
    "library": "1JRvRaqsNP_G-9xICwrgGpY-ArwV8ej1w",
    "documents": "1DsufM2yMqcbE8kR-RH1i5rSBcvPivOxA",
}


class DriveEmbedParser(HTMLParser):
    """Parse the Google Drive embed folder view to extract file entries."""

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

    print(f"  WARNING: {filename} not found in embed view")
    return None


def download_drive_file(file_id, dest_path, retries=3):
    """Download a file from Google Drive by ID."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=120) as resp:
                data = resp.read()
            # Handle virus scan warning for large files
            if data[:100].startswith(b"<!DOCTYPE") or b"virus scan" in data[:2000].lower():
                match = re.search(rb"confirm=([a-zA-Z0-9_-]+)", data)
                if match:
                    confirm = match.group(1).decode()
                    url2 = f"{url}&confirm={confirm}"
                    req2 = Request(url2, headers={"User-Agent": "Mozilla/5.0"})
                    with urlopen(req2, timeout=120) as resp2:
                        data = resp2.read()
            Path(dest_path).write_bytes(data)
            return len(data)
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  Retry {attempt+1}: {e}, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    sheet_type = sys.argv[1]
    rev_num = int(sys.argv[2])
    output_path = sys.argv[3]

    if sheet_type not in DRIVE_FOLDERS:
        print(f"ERROR: Unknown sheet type '{sheet_type}'. Use 'library' or 'documents'.")
        sys.exit(1)

    folder_id = DRIVE_FOLDERS[sheet_type]
    print(f"Downloading {sheet_type} revision {rev_num}...")

    # Find the file
    file_id = find_drive_file(folder_id, rev_num)
    if not file_id:
        print(f"ERROR: Could not find rev-{rev_num}.ods.gz in {sheet_type} folder")
        sys.exit(1)

    print(f"  File ID: {file_id}")

    # Download the gzipped file
    gz_path = f"{output_path}.gz"
    print(f"  Downloading...")
    size = download_drive_file(file_id, gz_path)
    print(f"  Downloaded {size:,} bytes (compressed)")

    # Decompress
    gz_data = Path(gz_path).read_bytes()
    ods_data = gzip.decompress(gz_data)
    Path(output_path).write_bytes(ods_data)
    print(f"  Decompressed to {len(ods_data):,} bytes")

    # Clean up gz
    os.unlink(gz_path)

    print(f"  Output: {output_path}")
    print("Done.")


if __name__ == "__main__":
    main()
