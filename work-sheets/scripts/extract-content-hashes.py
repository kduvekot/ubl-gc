#!/usr/bin/env python3
"""
Extract content.xml from each ODS file and compute SHA-256 hashes.

ODS files are ZIP archives. The content.xml inside contains the actual
spreadsheet data. Unlike the full ODS binary (which includes timestamps
and other non-deterministic metadata), content.xml should be identical
for the same spreadsheet state regardless of when the export was done.

This gives us a reliable fingerprint for comparing ODS files downloaded
via different API methods (Method B: v2 exportLinks vs Method C: direct
Sheets URL).

Usage:
    python3 work-sheets/scripts/extract-content-hashes.py
"""

import hashlib
import json
import zipfile
import io
from pathlib import Path

ODS_DIR = Path("work-sheets/revision-ods")


def extract_content_xml(ods_path):
    """Extract content.xml from an ODS file and return its bytes."""
    with zipfile.ZipFile(ods_path) as zf:
        return zf.read("content.xml")


def extract_all_members(ods_path):
    """List all members of the ODS ZIP with sizes."""
    with zipfile.ZipFile(ods_path) as zf:
        return {info.filename: info.file_size for info in zf.infolist()}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    print("=" * 70)
    print("ODS content.xml Hash Extraction")
    print("=" * 70)
    print(f"Source: {ODS_DIR}/")
    print()

    results = {}

    for sheet_dir in sorted(ODS_DIR.iterdir()):
        if not sheet_dir.is_dir() or sheet_dir.name.startswith("."):
            continue

        print(f"\n--- {sheet_dir.name} ---")

        for ods_file in sorted(sheet_dir.glob("*.ods")):
            # Full file hash
            ods_bytes = ods_file.read_bytes()
            full_hash = sha256(ods_bytes)

            # Content.xml hash
            content_xml = extract_content_xml(ods_file)
            content_hash = sha256(content_xml)

            # ZIP member list
            members = extract_all_members(ods_file)

            # Also hash styles.xml and meta.xml separately
            with zipfile.ZipFile(ods_file) as zf:
                styles_hash = sha256(zf.read("styles.xml")) if "styles.xml" in members else None
                meta_hash = sha256(zf.read("meta.xml")) if "meta.xml" in members else None

            rel_path = f"{sheet_dir.name}/{ods_file.name}"
            results[rel_path] = {
                "ods_size": len(ods_bytes),
                "ods_sha256": full_hash,
                "content_xml_size": len(content_xml),
                "content_xml_sha256": content_hash,
                "styles_xml_sha256": styles_hash,
                "meta_xml_sha256": meta_hash,
                "zip_members": list(members.keys()),
            }

            print(f"  {ods_file.name}:")
            print(f"    ODS full:     {full_hash[:24]}... ({len(ods_bytes):,} bytes)")
            print(f"    content.xml:  {content_hash[:24]}... ({len(content_xml):,} bytes)")
            if styles_hash:
                print(f"    styles.xml:   {styles_hash[:24]}...")
            if meta_hash:
                print(f"    meta.xml:     {meta_hash[:24]}...")

    # Write results
    output_path = ODS_DIR / "content-hashes.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*70}")
    print(f"Results saved to: {output_path}")
    print(f"Total ODS files: {len(results)}")
    print()

    # Summary: unique content.xml hashes per sheet
    for prefix in ["ubl25_library", "ubl25_documents"]:
        hashes = [v["content_xml_sha256"] for k, v in results.items() if k.startswith(prefix)]
        unique = len(set(hashes))
        print(f"  {prefix}: {unique} unique content.xml states out of {len(hashes)} files")

    print()
    print("These content.xml hashes are the REFERENCE FINGERPRINTS.")
    print("Any ODS file downloaded via a different API method should produce")
    print("the same content.xml hash if it truly contains the same revision data.")


if __name__ == "__main__":
    main()
