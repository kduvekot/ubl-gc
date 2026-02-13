#!/usr/bin/env python3
"""
UBL Release Manifest

Complete chronological list of all 35 UBL releases from UBL 2.0 (2006) through UBL 2.5 (2025).
This manifest drives the git history orchestrator that creates commits.

Verified against actual filesystem on 2026-02-13.
All file paths relative to repository root.
"""

# All 35 UBL releases in chronological order
RELEASES = [
    # ========== UBL 2.0 (2006) - 8 releases ==========
    # UBL 2.0 files are generated from ODS sources, stored in history/generated/
    {
        "version": "2.0",
        "stage": "prd",
        "label": "prd-UBL-2.0",
        "date": "2006-01-19",
        "dir": "history/generated/prd-UBL-2.0",
        "entities_file": "mod/UBL-Entities-2.0.gc",
        "signature_file": None,
        "endorsed_file": None,
        "is_first_of_version": True,
    },
    {
        "version": "2.0",
        "stage": "prd2",
        "label": "prd2-UBL-2.0",
        "date": "2006-07-28",
        "dir": "history/generated/prd2-UBL-2.0",
        "entities_file": "mod/UBL-Entities-2.0.gc",
        "signature_file": None,
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.0",
        "stage": "prd3",
        "label": "prd3-UBL-2.0",
        "date": "2006-09-21",
        "dir": "history/generated/prd3-UBL-2.0",
        "entities_file": "mod/UBL-Entities-2.0.gc",
        "signature_file": None,
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.0",
        "stage": "prd3r1",
        "label": "prd3r1-UBL-2.0",
        "date": "2006-10-05",
        "dir": "history/generated/prd3r1-UBL-2.0",
        "entities_file": "mod/UBL-Entities-2.0.gc",
        "signature_file": None,
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.0",
        "stage": "cs",
        "label": "cs-UBL-2.0",
        "date": "2006-10-12",
        "dir": "history/generated/cs-UBL-2.0",
        "entities_file": "mod/UBL-Entities-2.0.gc",
        "signature_file": None,
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.0",
        "stage": "os",
        "label": "os-UBL-2.0",
        "date": "2006-12-12",
        "dir": "history/generated/os-UBL-2.0",
        "entities_file": "mod/UBL-Entities-2.0.gc",
        "signature_file": None,
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.0",
        "stage": "os-update",
        "label": "os-update-UBL-2.0",
        "date": "2008-05-26",
        "dir": "history/generated/os-update-UBL-2.0",
        "entities_file": "mod/UBL-Entities-2.0.gc",
        "signature_file": None,
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.0",
        "stage": "errata",
        "label": "errata-UBL-2.0",
        "date": "2008-04-23",
        "dir": "history/generated/errata-UBL-2.0",
        "entities_file": "mod/UBL-Entities-2.0.gc",
        "signature_file": None,
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    # ========== UBL 2.1 (2013) - 8 releases ==========
    {
        "version": "2.1",
        "stage": "prd1",
        "label": "prd1-UBL-2.1",
        "date": "2010-09-25",
        "dir": "history/prd1-UBL-2.1",
        "entities_file": "mod/UBL-Entities-2.1.gc",
        "signature_file": None,  # Not published for prd1
        "endorsed_file": None,
        "is_first_of_version": True,
    },
    {
        "version": "2.1",
        "stage": "prd2",
        "label": "prd2-UBL-2.1",
        "date": "2011-05-30",
        "dir": "history/prd2-UBL-2.1",
        "entities_file": "mod/UBL-Entities-2.1.gc",
        "signature_file": None,  # Not published for prd2
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.1",
        "stage": "prd3",
        "label": "prd3-UBL-2.1",
        "date": "2013-02-23",
        "dir": "history/prd3-UBL-2.1",
        "entities_file": "mod/UBL-Entities-2.1.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.1.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.1",
        "stage": "prd4",
        "label": "prd4-UBL-2.1",
        "date": "2013-05-14",
        "dir": "history/prd4-UBL-2.1",
        "entities_file": "mod/UBL-Entities-2.1.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.1.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.1",
        "stage": "csd4",
        "label": "csd4-UBL-2.1",
        "date": "2013-05-14",
        "dir": "history/csd4-UBL-2.1",
        "entities_file": "mod/UBL-Entities-2.1.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.1.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.1",
        "stage": "cs1",
        "label": "cs1-UBL-2.1",
        "date": "2013-06-29",
        "dir": "history/cs1-UBL-2.1",
        "entities_file": "mod/UBL-Entities-2.1.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.1.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.1",
        "stage": "cos1",
        "label": "cos1-UBL-2.1",
        "date": "2013-07-15",
        "dir": "history/cos1-UBL-2.1",
        "entities_file": "mod/UBL-Entities-2.1.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.1.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.1",
        "stage": "os",
        "label": "os-UBL-2.1",
        "date": "2013-11-04",
        "dir": "history/os-UBL-2.1",
        "entities_file": "mod/UBL-Entities-2.1.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.1.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    # ========== UBL 2.2 (2018) - 6 releases ==========
    {
        "version": "2.2",
        "stage": "csprd01",
        "label": "csprd01-UBL-2.2",
        "date": "2016-12-21",
        "dir": "history/csprd01-UBL-2.2",
        "entities_file": "mod/UBL-Entities-2.2.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.2.gc",
        "endorsed_file": None,
        "is_first_of_version": True,
    },
    {
        "version": "2.2",
        "stage": "csprd02",
        "label": "csprd02-UBL-2.2",
        "date": "2017-11-01",
        "dir": "history/csprd02-UBL-2.2",
        "entities_file": "mod/UBL-Entities-2.2.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.2.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.2",
        "stage": "csprd03",
        "label": "csprd03-UBL-2.2",
        "date": "2018-02-21",
        "dir": "history/csprd03-UBL-2.2",
        "entities_file": "mod/UBL-Entities-2.2.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.2.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.2",
        "stage": "cs01",
        "label": "cs01-UBL-2.2",
        "date": "2018-03-22",
        "dir": "history/cs01-UBL-2.2",
        "entities_file": "mod/UBL-Entities-2.2.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.2.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.2",
        "stage": "cos01",
        "label": "cos01-UBL-2.2",
        "date": "2018-04-22",
        "dir": "history/cos01-UBL-2.2",
        "entities_file": "mod/UBL-Entities-2.2.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.2.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.2",
        "stage": "os",
        "label": "os-UBL-2.2",
        "date": "2018-07-09",
        "dir": "history/os-UBL-2.2",
        "entities_file": "mod/UBL-Entities-2.2.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.2.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    # ========== UBL 2.3 (2021) - 7 releases ==========
    {
        "version": "2.3",
        "stage": "csprd01",
        "label": "csprd01-UBL-2.3",
        "date": "2019-08-07",
        "dir": "history/csprd01-UBL-2.3",
        "entities_file": "mod/UBL-Entities-2.3.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.3.gc",
        "endorsed_file": None,
        "is_first_of_version": True,
    },
    {
        "version": "2.3",
        "stage": "csprd02",
        "label": "csprd02-UBL-2.3",
        "date": "2020-01-29",
        "dir": "history/csprd02-UBL-2.3",
        "entities_file": "mod/UBL-Entities-2.3.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.3.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.3",
        "stage": "csd03",
        "label": "csd03-UBL-2.3",
        "date": "2020-07-29",
        "dir": "history/csd03-UBL-2.3",
        "entities_file": "mod/UBL-Entities-2.3.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.3.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.3",
        "stage": "csd04",
        "label": "csd04-UBL-2.3",
        "date": "2020-11-25",
        "dir": "history/csd04-UBL-2.3",
        "entities_file": "mod/UBL-Entities-2.3.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.3.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.3",
        "stage": "cs01",
        "label": "cs01-UBL-2.3",
        "date": "2021-01-19",
        "dir": "history/cs01-UBL-2.3",
        "entities_file": "mod/UBL-Entities-2.3.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.3.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.3",
        "stage": "cs02",
        "label": "cs02-UBL-2.3",
        "date": "2021-05-25",
        "dir": "history/cs02-UBL-2.3",
        "entities_file": "mod/UBL-Entities-2.3.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.3.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.3",
        "stage": "os",
        "label": "os-UBL-2.3",
        "date": "2021-06-15",
        "dir": "history/os-UBL-2.3",
        "entities_file": "mod/UBL-Entities-2.3.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.3.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    # ========== UBL 2.4 (2024) - 4 releases ==========
    {
        "version": "2.4",
        "stage": "csd01",
        "label": "csd01-UBL-2.4",
        "date": "2023-02-08",
        "dir": "history/csd01-UBL-2.4",
        "entities_file": "mod/UBL-Entities-2.4.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.4.gc",
        "endorsed_file": None,
        "is_first_of_version": True,
    },
    {
        "version": "2.4",
        "stage": "csd02",
        "label": "csd02-UBL-2.4",
        "date": "2023-07-26",
        "dir": "history/csd02-UBL-2.4",
        "entities_file": "mod/UBL-Entities-2.4.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.4.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.4",
        "stage": "cs01",
        "label": "cs01-UBL-2.4",
        "date": "2023-10-17",
        "dir": "history/cs01-UBL-2.4",
        "entities_file": "mod/UBL-Entities-2.4.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.4.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    {
        "version": "2.4",
        "stage": "os",
        "label": "os-UBL-2.4",
        "date": "2024-06-20",
        "dir": "history/os-UBL-2.4",
        "entities_file": "mod/UBL-Entities-2.4.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.4.gc",
        "endorsed_file": None,
        "is_first_of_version": False,
    },
    # ========== UBL 2.5 (2025) - 2 releases ==========
    {
        "version": "2.5",
        "stage": "csd01",
        "label": "csd01-UBL-2.5",
        "date": "2025-08-20",
        "dir": "history/csd01-UBL-2.5",
        "entities_file": "mod/UBL-Entities-2.5.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.5.gc",
        "endorsed_file": "endorsed/mod/UBL-Endorsed-Entities-2.5.gc",
        "is_first_of_version": True,
    },
    {
        "version": "2.5",
        "stage": "csd02",
        "label": "csd02-UBL-2.5",
        "date": "2025-12-03",
        "dir": "history/csd02-UBL-2.5",
        "entities_file": "mod/UBL-Entities-2.5.gc",
        "signature_file": "mod/UBL-Signature-Entities-2.5.gc",
        "endorsed_file": "endorsed/mod/UBL-Endorsed-Entities-2.5.gc",
        "is_first_of_version": False,
    },
]

# Validation: ensure all files exist on disk
def validate_manifest():
    """Verify that all files referenced in the manifest exist on disk."""
    import os
    repo_root = "/home/user/ubl-gc"
    missing = []

    for release in RELEASES:
        dir_path = os.path.join(repo_root, release["dir"])

        # Check entities file
        entities_path = os.path.join(dir_path, release["entities_file"])
        if not os.path.exists(entities_path):
            missing.append(f"Missing: {release['label']} entities at {entities_path}")

        # Check signature file if it should exist
        if release["signature_file"]:
            sig_path = os.path.join(dir_path, release["signature_file"])
            if not os.path.exists(sig_path):
                missing.append(f"Missing: {release['label']} signature at {sig_path}")

        # Check endorsed file if it should exist
        if release["endorsed_file"]:
            endorsed_path = os.path.join(dir_path, release["endorsed_file"])
            if not os.path.exists(endorsed_path):
                missing.append(f"Missing: {release['label']} endorsed at {endorsed_path}")

    return missing

def get_release_pairs():
    """Return list of (old_release, new_release) tuples for sequential processing.

    Returns:
        List of tuples where each tuple contains (previous_release, current_release)
        in chronological order.
    """
    pairs = []
    for i in range(1, len(RELEASES)):
        pairs.append((RELEASES[i-1], RELEASES[i]))
    return pairs

def get_version_transitions():
    """Return list of (old_release, new_release) tuples where major version changes.

    These transitions require 6-step multi-commit sequences:
    1. Add new columns (empty)
    2. Populate new columns
    3. Mark old columns as deprecated
    4. Remove references to old columns
    5. Remove deprecated columns
    6. Final cleanup/normalization

    Returns:
        List of tuples where each tuple represents a major version transition.
    """
    return [(old, new) for old, new in get_release_pairs()
            if old['version'] != new['version']]

def get_releases_by_version(version):
    """Get all releases for a specific major version.

    Args:
        version: Major version string (e.g., '2.0', '2.1', '2.5')

    Returns:
        List of release dicts for that version in chronological order.
    """
    return [r for r in RELEASES if r['version'] == version]

def get_first_release_of_version(version):
    """Get the first (earliest) release of a major version.

    Args:
        version: Major version string (e.g., '2.0', '2.1', '2.5')

    Returns:
        Release dict for the first release of that version, or None.
    """
    for release in RELEASES:
        if release['version'] == version and release['is_first_of_version']:
            return release
    return None

def get_official_releases():
    """Get all official releases (os/OS stage).

    Returns:
        List of release dicts that are official standards.
    """
    return [r for r in RELEASES if r['stage'] == 'os']

def get_all_versions():
    """Get all unique major versions in the manifest.

    Returns:
        List of version strings in chronological order.
    """
    seen = []
    for release in RELEASES:
        if release['version'] not in seen:
            seen.append(release['version'])
    return seen

# Statistics
TOTAL_RELEASES = len(RELEASES)
TOTAL_ENTITIES_FILES = sum(1 for r in RELEASES if r['entities_file'])
TOTAL_SIGNATURE_FILES = sum(1 for r in RELEASES if r['signature_file'])
TOTAL_ENDORSED_FILES = sum(1 for r in RELEASES if r['endorsed_file'])
TOTAL_GC_FILES = TOTAL_ENTITIES_FILES + TOTAL_SIGNATURE_FILES + TOTAL_ENDORSED_FILES

# Summary by version
RELEASES_BY_VERSION = {
    '2.0': 8,
    '2.1': 8,
    '2.2': 6,
    '2.3': 7,
    '2.4': 4,
    '2.5': 2,
}

if __name__ == '__main__':
    print(f"UBL Release Manifest")
    print(f"===================")
    print(f"Total releases: {TOTAL_RELEASES}")
    print(f"Total Entities files: {TOTAL_ENTITIES_FILES}")
    print(f"Total Signature-Entities files: {TOTAL_SIGNATURE_FILES}")
    print(f"Total Endorsed-Entities files: {TOTAL_ENDORSED_FILES}")
    print(f"Total GenericCode files: {TOTAL_GC_FILES}")
    print()
    print(f"Releases by version:")
    for version, count in RELEASES_BY_VERSION.items():
        print(f"  UBL {version}: {count} releases")
    print()
    print(f"Version transitions (require 6-step commits): {len(get_version_transitions())}")
    print()

    # Validate manifest
    missing = validate_manifest()
    if missing:
        print("Validation FAILED - Missing files:")
        for msg in missing:
            print(f"  {msg}")
    else:
        print("Validation PASSED - All files exist on disk")
