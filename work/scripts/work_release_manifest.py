#!/usr/bin/env python3
"""
UBL Work Release Manifest

Combined manifest of all 35 official UBL releases PLUS 9 intermediate working
drafts discovered in CI artifacts from oasis-tcs/ubl build-history.yml.

Total: 44 releases in chronological order.

The intermediate files are UBL 2.5 working drafts captured between:
- CSD01 (Aug 20, 2025) and CSD02 (Dec 3, 2025): 4 working drafts (V1-V4)
- CSD02 and CSD03 (pending): 5 working drafts (V6-V10)

V5 = the published CSD02 (already in the official manifest).

Source files live in work/work-history/ with the same directory layout as history/.
"""

import sys
from pathlib import Path

# Ensure scripts/lib/ is on the import path (for standalone use)
_repo_root = Path(__file__).resolve().parent.parent.parent
_scripts_lib = _repo_root / 'scripts' / 'lib'
if str(_scripts_lib) not in sys.path:
    sys.path.insert(0, str(_scripts_lib))

from release_manifest import RELEASES as OFFICIAL_RELEASES

# ========== Intermediate Working Drafts ==========
# These 9 entries are inserted into the UBL 2.5 section of the manifest,
# interleaved chronologically with the 2 official CSD01/CSD02 releases.

_WORK_SOURCE = "CI artifact from oasis-tcs/ubl build-history.yml"

INTERMEDIATE_RELEASES = [
    # --- Pre-CSD02 working drafts (between CSD01 and CSD02) ---
    {
        "version": "2.5",
        "stage": "pre-csd02-v1",
        "label": "pre-csd02-2025-11-17-1042-UBL-2.5",
        "date": "2025-11-17",
        "timestamp": "2025-11-17T10:42:00+00:00",
        "dir": "work/work-history/pre-csd02-2025-11-17-1042-UBL-2.5",
        "entities_file": "mod/UBL-Entities-2.5.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.5.gc",
        "endorsed_file": "endorsed/mod/UBL-Endorsed-Entities-2.5.gc",
        "is_first_of_version": False,
        "source": _WORK_SOURCE,
        "description": "Initial CSD02 working copy",
    },
    {
        "version": "2.5",
        "stage": "pre-csd02-v2",
        "label": "pre-csd02-2025-11-19-0915-UBL-2.5",
        "date": "2025-11-19",
        "timestamp": "2025-11-19T09:15:00+00:00",
        "dir": "work/work-history/pre-csd02-2025-11-19-0915-UBL-2.5",
        "entities_file": "mod/UBL-Entities-2.5.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.5.gc",
        "endorsed_file": "endorsed/mod/UBL-Endorsed-Entities-2.5.gc",
        "is_first_of_version": False,
        "source": _WORK_SOURCE,
        "description": "Customs definitions rewritten",
    },
    {
        "version": "2.5",
        "stage": "pre-csd02-v3",
        "label": "pre-csd02-2025-11-20-1350-UBL-2.5",
        "date": "2025-11-20",
        "timestamp": "2025-11-20T13:50:00+00:00",
        "dir": "work/work-history/pre-csd02-2025-11-20-1350-UBL-2.5",
        "entities_file": "mod/UBL-Entities-2.5.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.5.gc",
        "endorsed_file": "endorsed/mod/UBL-Endorsed-Entities-2.5.gc",
        "is_first_of_version": False,
        "source": _WORK_SOURCE,
        "description": "WasteMovement ABIE added (with NDR errors)",
    },
    {
        "version": "2.5",
        "stage": "pre-csd02-v4",
        "label": "pre-csd02-2025-11-20-1405-UBL-2.5",
        "date": "2025-11-20",
        "timestamp": "2025-11-20T14:05:00+00:00",
        "dir": "work/work-history/pre-csd02-2025-11-20-1405-UBL-2.5",
        "entities_file": "mod/UBL-Entities-2.5.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.5.gc",
        "endorsed_file": "endorsed/mod/UBL-Endorsed-Entities-2.5.gc",
        "is_first_of_version": False,
        "source": _WORK_SOURCE,
        "description": "NDR fix: WasteProducer spacing corrected",
    },
    # --- Post-CSD02 / Pre-CSD03 working drafts ---
    {
        "version": "2.5",
        "stage": "pre-csd03-v6",
        "label": "pre-csd03-2026-01-21-1638-UBL-2.5",
        "date": "2026-01-21",
        "timestamp": "2026-01-21T16:38:00+00:00",
        "dir": "work/work-history/pre-csd03-2026-01-21-1638-UBL-2.5",
        "entities_file": "mod/UBL-Entities-2.5.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.5.gc",
        "endorsed_file": "endorsed/mod/UBL-Endorsed-Entities-2.5.gc",
        "is_first_of_version": False,
        "source": _WORK_SOURCE,
        "description": "BuyerReference renamed to BuyerAssignedReference",
    },
    {
        "version": "2.5",
        "stage": "pre-csd03-v7",
        "label": "pre-csd03-2026-01-21-1701-UBL-2.5",
        "date": "2026-01-21",
        "timestamp": "2026-01-21T17:01:00+00:00",
        "dir": "work/work-history/pre-csd03-2026-01-21-1701-UBL-2.5",
        "entities_file": "mod/UBL-Entities-2.5.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.5.gc",
        "endorsed_file": "endorsed/mod/UBL-Endorsed-Entities-2.5.gc",
        "is_first_of_version": False,
        "source": _WORK_SOURCE,
        "description": "Cardinality changes: 0..1 to 0..n",
    },
    {
        "version": "2.5",
        "stage": "pre-csd03-v8",
        "label": "pre-csd03-2026-01-21-1926-UBL-2.5",
        "date": "2026-01-21",
        "timestamp": "2026-01-21T19:26:00+00:00",
        "dir": "work/work-history/pre-csd03-2026-01-21-1926-UBL-2.5",
        "entities_file": "mod/UBL-Entities-2.5.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.5.gc",
        "endorsed_file": "endorsed/mod/UBL-Endorsed-Entities-2.5.gc",
        "is_first_of_version": False,
        "source": _WORK_SOURCE,
        "description": "BuyerAssignedReference rename propagated to more document types",
    },
    {
        "version": "2.5",
        "stage": "pre-csd03-v9",
        "label": "pre-csd03-2026-02-09-1442-UBL-2.5",
        "date": "2026-02-09",
        "timestamp": "2026-02-09T14:42:00+00:00",
        "dir": "work/work-history/pre-csd03-2026-02-09-1442-UBL-2.5",
        "entities_file": "mod/UBL-Entities-2.5.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.5.gc",
        "endorsed_file": "endorsed/mod/UBL-Endorsed-Entities-2.5.gc",
        "is_first_of_version": False,
        "source": _WORK_SOURCE,
        "description": "Three additional 0..1 to 0..n cardinality changes",
    },
    {
        "version": "2.5",
        "stage": "pre-csd03-v10",
        "label": "pre-csd03-2026-02-09-1446-UBL-2.5",
        "date": "2026-02-09",
        "timestamp": "2026-02-09T14:46:00+00:00",
        "dir": "work/work-history/pre-csd03-2026-02-09-1446-UBL-2.5",
        "entities_file": "mod/UBL-Entities-2.5.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.5.gc",
        "endorsed_file": "endorsed/mod/UBL-Endorsed-Entities-2.5.gc",
        "is_first_of_version": False,
        "source": _WORK_SOURCE,
        "description": "CSD02 to CSD03 metadata update in headers",
    },
]


def _build_combined_releases():
    """Build the combined release list: 35 official + 9 intermediate = 44 total.

    Inserts intermediates at the correct chronological positions within UBL 2.5:
    - 4 pre-CSD02 drafts between csd01-UBL-2.5 and csd02-UBL-2.5
    - 5 pre-CSD03 drafts after csd02-UBL-2.5
    """
    combined = []
    pre_csd02 = [r for r in INTERMEDIATE_RELEASES if r["stage"].startswith("pre-csd02")]
    pre_csd03 = [r for r in INTERMEDIATE_RELEASES if r["stage"].startswith("pre-csd03")]

    for release in OFFICIAL_RELEASES:
        combined.append(release)

        # After csd01-UBL-2.5, insert pre-CSD02 working drafts
        if release["label"] == "csd01-UBL-2.5":
            combined.extend(pre_csd02)

        # After csd02-UBL-2.5, insert pre-CSD03 working drafts
        if release["label"] == "csd02-UBL-2.5":
            combined.extend(pre_csd03)

    return combined


# The combined release list (44 entries)
RELEASES = _build_combined_releases()


# Re-export utility functions that work on the combined RELEASES
def get_release_pairs():
    """Return list of (old_release, new_release) tuples for sequential processing."""
    pairs = []
    for i in range(1, len(RELEASES)):
        pairs.append((RELEASES[i-1], RELEASES[i]))
    return pairs


def get_version_transitions():
    """Return list of (old_release, new_release) tuples where major version changes."""
    return [(old, new) for old, new in get_release_pairs()
            if old['version'] != new['version']]


def get_releases_by_version(version):
    """Get all releases for a specific major version."""
    return [r for r in RELEASES if r['version'] == version]


def get_all_versions():
    """Get all unique major versions in the manifest."""
    seen = []
    for release in RELEASES:
        if release['version'] not in seen:
            seen.append(release['version'])
    return seen


# Validation
def validate_manifest():
    """Verify that all files referenced in the manifest exist on disk."""
    import os
    repo_root = "/home/user/ubl-gc"
    missing = []

    for release in RELEASES:
        dir_path = os.path.join(repo_root, release["dir"])

        entities_path = os.path.join(dir_path, release["entities_file"])
        if not os.path.exists(entities_path):
            missing.append(f"Missing: {release['label']} entities at {entities_path}")

        if release["signature_file"]:
            sig_path = os.path.join(dir_path, release["signature_file"])
            if not os.path.exists(sig_path):
                missing.append(f"Missing: {release['label']} signature at {sig_path}")

        if release["endorsed_file"]:
            endorsed_path = os.path.join(dir_path, release["endorsed_file"])
            if not os.path.exists(endorsed_path):
                missing.append(f"Missing: {release['label']} endorsed at {endorsed_path}")

    return missing


# Statistics
TOTAL_RELEASES = len(RELEASES)
TOTAL_OFFICIAL = len(OFFICIAL_RELEASES)
TOTAL_INTERMEDIATE = len(INTERMEDIATE_RELEASES)
TOTAL_ENTITIES_FILES = sum(1 for r in RELEASES if r['entities_file'])
TOTAL_SIGNATURE_FILES = sum(1 for r in RELEASES if r['signature_file'])
TOTAL_ENDORSED_FILES = sum(1 for r in RELEASES if r['endorsed_file'])
TOTAL_GC_FILES = TOTAL_ENTITIES_FILES + TOTAL_SIGNATURE_FILES + TOTAL_ENDORSED_FILES


if __name__ == '__main__':
    print(f"UBL Work Release Manifest")
    print(f"=========================")
    print(f"Official releases: {TOTAL_OFFICIAL}")
    print(f"Intermediate working drafts: {TOTAL_INTERMEDIATE}")
    print(f"Total releases: {TOTAL_RELEASES}")
    print(f"Total GenericCode files: {TOTAL_GC_FILES}")
    print()
    print(f"UBL 2.5 sequence ({len(get_releases_by_version('2.5'))} entries):")
    for r in get_releases_by_version('2.5'):
        ts = r.get('timestamp', f"{r['date']}T12:00:00+00:00")
        src = f"  [{r.get('source', 'OASIS')}]" if r.get('source') else ""
        desc = f"  - {r['description']}" if r.get('description') else ""
        print(f"  {r['label']:<50} {ts}{src}{desc}")
    print()

    # Validate
    missing = validate_manifest()
    if missing:
        print(f"Validation FAILED - {len(missing)} missing files:")
        for msg in missing:
            print(f"  {msg}")
    else:
        print(f"Validation PASSED - All {TOTAL_GC_FILES} files exist on disk")
