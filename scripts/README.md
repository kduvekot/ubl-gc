# UBL-GC Scripts

This directory contains scripts for building and managing the UBL GenericCode historical repository.

## Overview

These scripts enable **reproducible** construction of the git history branch that demonstrates the complete evolution of UBL semantic models across all 35 releases.

---

## Available Scripts

### 📥 Download & Setup Scripts

#### `download-oasis-distributions.sh`

Downloads complete OASIS UBL distributions for all 35 releases (2.0-2.5).

**Purpose:**
- Download full ZIP distributions from OASIS
- Extract XSD schemas, code lists, examples, and documentation
- Preserve complete historical artifacts beyond just GenericCode files

**Usage:**
```bash
# Download everything for all 35 releases
./scripts/download-oasis-distributions.sh

# Dry run (see what would be downloaded)
./scripts/download-oasis-distributions.sh --dry-run

# Download specific version only
./scripts/download-oasis-distributions.sh --version 2.4

# Download specific release only
./scripts/download-oasis-distributions.sh --release os-UBL-2.4

# Skip releases that already have xsd/ directory
./scripts/download-oasis-distributions.sh --skip-existing

# Verify existing downloads
./scripts/download-oasis-distributions.sh --verify-only
```

**What it downloads:**
- `xsd/` - XML Schema files (shows .gc → .xsd mapping)
- `cl/` - Code lists (enumeration values)
- `val/` - Validation resources
- `cva/` - Context/value association files
- `db/` - Database files
- `art/` - Artifacts
- `xml/` - Example XML documents
- `xsdrt/` - XSD runtime resources
- Documentation (HTML, PDF, XML)

**What it preserves:**
- `mod/` - Skips extraction (preserves our existing .gc files)

**Output structure:**
```
history/
├─ generated/prd-UBL-2.0/
│  ├─ mod/    (existing - preserved)
│  ├─ xsd/    (new - downloaded)
│  ├─ cl/     (new - downloaded)
│  └─ ...
├─ prd1-UBL-2.1/
│  ├─ mod/    (existing - preserved)
│  ├─ xsd/    (new - downloaded)
│  └─ ...
└─ ...
```

---

### 🔨 Build Scripts (To Be Created)

#### `build-history.sh` *(Planned)*

Master orchestrator that builds the complete git history branch.

**Will do:**
- Create or reset the history branch
- Call version-specific build scripts in order
- Apply multi-step transitions between major versions
- Verify commit sequence
- Push to remote

**Usage:**
```bash
# Build complete history from scratch
./scripts/build-history.sh

# Resume from specific version
./scripts/build-history.sh --start-from 2.3

# Build and push
./scripts/build-history.sh --push
```

---

### 📚 Library Modules (To Be Created)

#### `lib/common.sh` *(Planned)*

Shared utility functions used by all build scripts.

**Functions:**
- Git operations (commit, tag, branch management)
- File operations (copy, compare, diff)
- Logging and reporting
- Error handling

#### `lib/commit-helpers.sh` *(Planned)*

Specialized functions for creating consistent git commits.

**Functions:**
- Standard commit message formatting
- Multi-step transition commits
- Commit metadata tracking
- Verification helpers

---

### 🎯 Version-Specific Builders (To Be Created)

#### `versions/build-2.0.sh` *(Planned)*

Processes UBL 2.0 releases (8 stages) using generated GenericCode files.

**Handles:**
- Simple transitions between prd → prd2 → ... → errata
- Single commit per release stage

#### `versions/build-2.1.sh` *(Planned)*

Processes UBL 2.1 releases (8 stages) and transition from 2.0.

**Handles:**
- 6-step transition from 2.0 to 2.1 (filename change)
- 7 simple commits for remaining stages (prd2 → os)

#### `versions/build-2.2.sh` *(Planned)*

Processes UBL 2.2 releases (6 stages) and transition from 2.1.

**Handles:**
- 6-step transition from 2.1 to 2.2 (filename + column structure)
- 5 simple commits for remaining stages

#### `versions/build-2.3.sh` *(Planned)*

Processes UBL 2.3 releases (7 stages) and transition from 2.2.

**Handles:**
- 6-step transition from 2.2 to 2.3 (filename change)
- 6 simple commits for remaining stages

#### `versions/build-2.4.sh` *(Planned)*

Processes UBL 2.4 releases (4 stages) and transition from 2.3.

**Handles:**
- 6-step transition from 2.3 to 2.4 (filename change)
- 3 simple commits for remaining stages

#### `versions/build-2.5.sh` *(Planned)*

Processes UBL 2.5 releases (2 stages) and transition from 2.4.

**Handles:**
- 6-step transition from 2.4 to 2.5 (filename + structure + Endorsed file)
- 1 simple commit for csd02

---

## The 6-Step Transition Process

Major version transitions use a careful 6-step process to track schema evolution:

```
Step 1: Add new columns (empty)
Step 2: Populate new columns with data
Step 3: Mark old columns as deprecated
Step 4: Remove references to old columns
Step 5: Remove deprecated columns
Step 6: Final cleanup/normalization + first release of new version
```

**Applied at:**
- 2.0 → 2.1: Filename changes
- 2.1 → 2.2: Filename + column structure changes (add DEN, AlternativeBusinessTerms)
- 2.2 → 2.3: Filename changes
- 2.3 → 2.4: Filename changes
- 2.4 → 2.5: Filename + column structure changes (add CardinalitySupplement) + add Endorsed file

---

## Expected Output

**Total commits:**
- 35 release commits (one per release stage)
- 30 transition commits (5 transitions × 6 steps)
- **= 65 total commits**

**Timeline:**
- 2006: UBL 2.0 (8 commits)
- 2010-2013: UBL 2.1 (6 transition + 7 release = 13 commits)
- 2016-2018: UBL 2.2 (6 transition + 5 release = 11 commits)
- 2019-2021: UBL 2.3 (6 transition + 6 release = 12 commits)
- 2023-2024: UBL 2.4 (6 transition + 3 release = 9 commits)
- 2025: UBL 2.5 (6 transition + 1 release = 7 commits)

---

## Development Workflow

1. **Download distributions:**
   ```bash
   ./scripts/download-oasis-distributions.sh
   ```

2. **Build history branch:**
   ```bash
   ./scripts/build-history.sh
   ```

3. **Verify result:**
   ```bash
   git checkout claude/git-history-exploration-bunUn
   git log --oneline --all --graph
   ```

4. **Push to remote:**
   ```bash
   git push -u origin claude/git-history-exploration-bunUn
   ```

---

## Design Principles

1. ✅ **Reproducible** - Delete branch, re-run scripts → identical result
2. ✅ **Version controlled** - Scripts are in main branch, reviewable
3. ✅ **Idempotent** - Can re-run without breaking
4. ✅ **Documented** - Each script explains what it does
5. ✅ **No downloads in build scripts** - All files from history/
6. ✅ **Preserves existing files** - Never overwrites our .gc files

---

## Related Documentation

- [README.md](../README.md) - Complete project overview
- [CLAUDE.md](../CLAUDE.md) - Guide for Claude Code sessions
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Design decisions
- [docs/historical-releases.md](../docs/historical-releases.md) - All 35 releases
- [docs/genericcode-format.md](../docs/genericcode-format.md) - GenericCode format documentation

---

**Last Updated:** 2026-02-12
**Status:** Download script ready, build scripts planned
