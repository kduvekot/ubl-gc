#!/usr/bin/env python3
"""
Compare ODS-generated GC files against CI artifact reference files.

Computes hashes both WITH and WITHOUT the <Identification> block to
distinguish between:
  1. Stage-label differences (only Identification differs)
  2. Actual data differences (content outside Identification differs)

This tells us whether the revision-to-workflow mapping is correct.
"""

import hashlib
import re
from pathlib import Path

# CI artifact reference files (from work/work-history/)
CI_REFS = {
    "V1":  "work/work-history/pre-csd02-2025-11-17-1042-UBL-2.5",
    "V2":  "work/work-history/pre-csd02-2025-11-19-0915-UBL-2.5",
    "V3":  "work/work-history/pre-csd02-2025-11-20-1350-UBL-2.5",
    "V4":  "work/work-history/pre-csd02-2025-11-20-1405-UBL-2.5",
    # V5 = published CSD02
    "V6":  "work/work-history/pre-csd03-2026-01-21-1638-UBL-2.5",
    "V7":  "work/work-history/pre-csd03-2026-01-21-1701-UBL-2.5",
    "V8":  "work/work-history/pre-csd03-2026-01-21-1926-UBL-2.5",
    "V9":  "work/work-history/pre-csd03-2026-02-09-1442-UBL-2.5",
    "V10": "work/work-history/pre-csd03-2026-02-09-1446-UBL-2.5",
}

# Also check published CSD02
PUBLISHED_CSD02 = "history/csd02-UBL-2.5"

# ODS-generated files
ODS_GEN = "work-sheets/gc-from-revisions"

# Revision mapping from manifest
REV_MAP = {
    "V1":  {"lib": "1843", "doc": "1793", "stage": "CSD02"},
    "V2":  {"lib": "1843", "doc": "1793", "stage": "CSD02"},
    "V3":  {"lib": "1868", "doc": "1803", "stage": "CSD02"},
    "V4":  {"lib": "1868", "doc": "1983", "stage": "CSD02"},
    "V5":  {"lib": "1999", "doc": "2190", "stage": "CSD02"},
    "V6":  {"lib": "1999", "doc": "2190", "stage": "CSD03"},
    "V7":  {"lib": "2005", "doc": "2190", "stage": "CSD03"},
    "V8":  {"lib": "2005", "doc": "2200", "stage": "CSD03"},
    "V9":  {"lib": "2005", "doc": "2204", "stage": "CSD03"},
    "V10": {"lib": "2005", "doc": "2204", "stage": "CSD03"},
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def strip_identification(gc_text):
    """Remove the <Identification>...</Identification> block."""
    return re.sub(
        r'<Identification>.*?</Identification>\s*',
        '', gc_text, count=1, flags=re.DOTALL
    )


def read_gc(path):
    """Read a GC file and return (full_hash, data_hash, text)."""
    p = Path(path)
    if not p.exists():
        return None, None, None
    text = p.read_text()
    full_hash = sha256(text.encode())
    data_hash = sha256(strip_identification(text).encode())
    return full_hash, data_hash, text


def main():
    print("=" * 80)
    print("GC File Verification: ODS-Generated vs CI Artifact Reference")
    print("=" * 80)
    print()

    # === Entities comparison ===
    print("UBL-Entities-2.5.gc")
    print("-" * 80)
    print(f"{'Ver':<5} {'Rev (lib/doc)':<18} {'ODS full':<18} {'CI full':<18} {'ODS data':<18} {'CI data':<18} {'Match'}")
    print("-" * 80)

    for ver in ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10"]:
        rev = REV_MAP[ver]
        rev_label = f"L{rev['lib']}/D{rev['doc']}"

        # ODS-generated
        ods_path = f"{ODS_GEN}/{ver}/UBL-Entities-2.5.gc"
        ods_full, ods_data, _ = read_gc(ods_path)

        # CI reference
        if ver == "V5":
            ci_path = f"{PUBLISHED_CSD02}/mod/UBL-Entities-2.5.gc"
        else:
            ci_dir = CI_REFS.get(ver, "")
            ci_path = f"{ci_dir}/mod/UBL-Entities-2.5.gc" if ci_dir else ""

        ci_full, ci_data, _ = read_gc(ci_path) if ci_path else (None, None, None)

        ods_full_short = ods_full[:16] if ods_full else "N/A"
        ci_full_short = ci_full[:16] if ci_full else "N/A"
        ods_data_short = ods_data[:16] if ods_data else "N/A"
        ci_data_short = ci_data[:16] if ci_data else "N/A"

        if ci_full is None:
            match = "no-ref"
        elif ods_full == ci_full:
            match = "FULL"
        elif ods_data == ci_data:
            match = "DATA-ONLY"
        else:
            match = "MISMATCH"

        print(f"{ver:<5} {rev_label:<18} {ods_full_short:<18} {ci_full_short:<18} {ods_data_short:<18} {ci_data_short:<18} {match}")

    print()

    # === Cross-match: find which CI version each ODS version's DATA matches ===
    print()
    print("=" * 80)
    print("Cross-Match: Which CI artifact does each ODS version's DATA content match?")
    print("=" * 80)
    print()

    # Collect all CI data hashes
    ci_data_hashes = {}
    for ver, ci_dir in CI_REFS.items():
        _, ci_data, _ = read_gc(f"{ci_dir}/mod/UBL-Entities-2.5.gc")
        if ci_data:
            ci_data_hashes[ver] = ci_data

    # Add published CSD02
    _, csd02_data, _ = read_gc(f"{PUBLISHED_CSD02}/mod/UBL-Entities-2.5.gc")
    if csd02_data:
        ci_data_hashes["V5(csd02)"] = csd02_data

    for ver in ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10"]:
        ods_path = f"{ODS_GEN}/{ver}/UBL-Entities-2.5.gc"
        _, ods_data, _ = read_gc(ods_path)
        if not ods_data:
            print(f"  {ver}: ODS file missing")
            continue

        rev = REV_MAP[ver]
        matches = [ci_ver for ci_ver, ci_data in ci_data_hashes.items()
                   if ci_data == ods_data]

        if matches:
            print(f"  {ver} (L{rev['lib']}/D{rev['doc']}, {rev['stage']}): "
                  f"DATA matches CI → {', '.join(matches)}")
        else:
            print(f"  {ver} (L{rev['lib']}/D{rev['doc']}, {rev['stage']}): "
                  f"DATA matches NO CI artifact  data={ods_data[:16]}...")

    # === Also show all unique CI data hashes ===
    print()
    print("=" * 80)
    print("All unique CI artifact data hashes (Entities)")
    print("=" * 80)
    seen = {}
    for ver in ["V1", "V2", "V3", "V4", "V5(csd02)", "V6", "V7", "V8", "V9", "V10"]:
        h = ci_data_hashes.get(ver)
        if h:
            if h not in seen:
                seen[h] = []
            seen[h].append(ver)

    for h, vers in seen.items():
        print(f"  {h[:24]}... → {', '.join(vers)}")

    print()
    print("=" * 80)
    print("All unique ODS-generated data hashes (Entities)")
    print("=" * 80)
    seen_ods = {}
    for ver in ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10"]:
        _, ods_data, _ = read_gc(f"{ODS_GEN}/{ver}/UBL-Entities-2.5.gc")
        if ods_data:
            if ods_data not in seen_ods:
                seen_ods[ods_data] = []
            seen_ods[ods_data].append(ver)

    for h, vers in seen_ods.items():
        print(f"  {h[:24]}... → {', '.join(vers)}")

    # === Summary of findings ===
    print()
    print("=" * 80)
    print("FINDINGS")
    print("=" * 80)

    ci_unique = len(set(ci_data_hashes.values()))
    ods_unique = len(seen_ods)
    print(f"  CI artifacts produce {ci_unique} unique data states")
    print(f"  ODS revisions produce {ods_unique} unique data states")
    print()
    print("  If ODS and CI data hashes don't match, the revision-to-workflow")
    print("  mapping may be wrong — the revision number may not correspond to")
    print("  the exact sheet state that was live when the CI workflow ran.")
    print()
    print("  A match count of 10/10 would confirm Method B (v2 exportLinks)")
    print("  returns the correct revision content.")


if __name__ == "__main__":
    main()
