# UBL-GC Scripts

Scripts for building and managing the UBL GenericCode historical repository.

## Overview

The build system creates a git history branch showing the complete evolution of UBL semantic models across all 35 releases — with individual commits per ABIE change, proper dependency ordering, and position-aware insertions.

---

## Build Script

### `build_history.py`

Single Python entry point that builds the complete git history branch.

**What it does:**
- Creates an orphan branch from scratch
- Processes all 35 UBL releases in chronological order (2.0 through 2.5)
- Computes granular diffs between consecutive releases
- Creates individual commits for each change (ABIE add/modify/remove/move, metadata, column structure, footer)
- Uses `git mv` at version transitions to preserve file rename history
- Inserts ABIEs in dependency order (topological sort)
- Positions ABIEs correctly relative to the target file's ordering

**Usage:**
```bash
# Build complete history from scratch
python3 scripts/build_history.py

# Dry run (see what would happen without creating commits)
python3 scripts/build_history.py --dry-run

# Resume from a specific release index
python3 scripts/build_history.py --start-at 15

# Build into a specific branch
python3 scripts/build_history.py --branch my-branch

# Keep the work directory after completion
python3 scripts/build_history.py --keep-workdir
```

**Tracked files (3 types):**
- `UBL-Entities-{version}.gc` — Main semantic model (all versions)
- `UBL-Signature-Entities-{version}.gc` — Digital signature entities (2.1+)
- `UBL-Endorsed-Entities-{version}.gc` — Endorsed subset (2.5+ only)

---

## Library Modules (`lib/`)

### `gc_diff.py`
Computes structured diffs between two GenericCode files. Produces an ordered list of change operations:
1. Metadata changes (Identification section)
2. Column structure changes (ColumnSet additions/removals)
3. ABIE removals
4. ABIE modifications (with position correction)
5. ABIE additions (in dependency order, at correct position)
6. ABIE moves (unmodified ABIEs that changed position)
7. Footer updates

### `gc_analyzer.py`
Parses GenericCode XML to extract ABIE structure, builds dependency graphs between ABIEs, and computes topological sort order for correct insertion sequencing.

### `gc_builder.py`
Constructs GenericCode XML files incrementally — used for building the initial UBL 2.0 file ABIE-by-ABIE.

### `gc_commit_builder.py`
Generates the sequence of git commits for the first release (UBL 2.0 PRD), adding ABIEs one at a time in dependency order.

### `release_manifest.py`
Complete manifest of all 35 UBL releases with metadata: version, stage, date, label, and source file paths for each file type (entities, signature, endorsed).

---

## Utility Scripts

### `download-oasis-distributions.sh`
Downloads complete OASIS UBL distribution ZIPs for all 35 releases and extracts XSD schemas, code lists, examples, etc.

### `extract-xsd-from-reference.sh`
Extracts XSD schema files from the ubl-release-package reference repository.

---

## Design Principles

1. **Reproducible** — Delete the history branch, re-run → identical result
2. **Single entry point** — One Python script orchestrates everything
3. **Granular commits** — One commit per logical change, not bulk operations
4. **Dependency-aware** — ABIEs added in topological order
5. **Position-aware** — Insertions, modifications, and moves respect target file ordering
6. **No downloads** — All source files already present in `history/`

---

## Related Documentation

- [README.md](../README.md) — Project overview
- [ARCHITECTURE.md](../ARCHITECTURE.md) — Design decisions
- [docs/historical-releases.md](../docs/historical-releases.md) — All 35 releases
- [docs/genericcode-format.md](../docs/genericcode-format.md) — GenericCode format
