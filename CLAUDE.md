# Claude Code Guide for ubl-gc Repository

**Purpose:** Help Claude understand this repository's structure, what's already done, and what needs to be built.

---

## 📖 READ THESE FIRST!

Before making any assumptions, READ these files:

1. **[README.md](README.md)** - Complete project overview, UBL 2.0 synthesis explanation
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture, data sources, design decisions
3. **[docs/historical-releases.md](docs/historical-releases.md)** - All 35 UBL releases with URLs
4. **[history/README.md](history/README.md)** - History directory organization
5. **[history/tools/README.md](history/tools/README.md)** - Tool documentation (Crane, Saxon)

---

## 🎯 What This Repository Is

A **complete historical archive** of UBL (Universal Business Language) GenericCode semantic model files:
- **Coverage:** UBL 2.0 (2006) through UBL 2.5 (2025)
- **Total Releases:** 35 releases across 5 major versions
- **Total Files:** 65 GenericCode (.gc) files
- **Status:** All source files downloaded and organized

### Version Breakdown

| Version | Releases | Files | Source | Status |
|---------|----------|-------|--------|--------|
| **UBL 2.0** (2006) | 8 | 8 generated .gc | history/generated/ | ✅ Complete |
| **UBL 2.1** (2013) | 8 | 16 .gc (2 per release) | history/*-UBL-2.1/ | ✅ Complete |
| **UBL 2.2** (2018) | 6 | 12 .gc (2 per release) | history/*-UBL-2.2/ | ✅ Complete |
| **UBL 2.3** (2021) | 7 | 14 .gc (2 per release) | history/*-UBL-2.3/ | ✅ Complete |
| **UBL 2.4** (2024) | 4 | 8 .gc (2 per release) | history/*-UBL-2.4/ | ✅ Complete |
| **UBL 2.5** (2025) | 2 | 7 .gc (3 per release: Entities + Signature + Endorsed) | history/*-UBL-2.5/ | ✅ Complete |
| **TOTAL** | **35** | **65 files** | | |

### Three Types of GenericCode Files

1. **UBL-Entities-{version}.gc** - Main semantic model (all versions)
2. **UBL-Signature-Entities-{version}.gc** - Digital signature entities (2.1-2.5)
3. **UBL-Endorsed-Entities-{version}.gc** - Endorsed subset (NEW in 2.5!)

---

## 📂 Key Directories

```
ubl-gc/
├── README.md                    ← START HERE! Complete documentation
├── ARCHITECTURE.md              ← Design decisions, data sources
├── CLAUDE.md                    ← This file (for Claude)
├── docs/
│   └── historical-releases.md   ← All 35 releases with OASIS URLs
├── history/
│   ├── README.md                ← History directory overview
│   ├── tools/                   ← Conversion tools (Crane, Saxon)
│   ├── generated/               ← UBL 2.0 .gc files (8 releases)
│   │   ├── prd-UBL-2.0/
│   │   ├── prd2-UBL-2.0/
│   │   ├── ...
│   │   └── errata-UBL-2.0/
│   ├── prd1-UBL-2.1/            ← UBL 2.1 releases (8)
│   ├── ...
│   ├── os-UBL-2.4/              ← UBL 2.4 releases (4)
│   └── csd02-UBL-2.5/           ← UBL 2.5 releases (2)
└── scripts/                     ← BUILD SCRIPTS (to be created!)
```

---

## ✅ What's Already Done

1. **All 65 GenericCode files downloaded/generated**
   - UBL 2.0: Generated from .ods using Crane-ods2obdgc tool
   - UBL 2.1-2.5: Downloaded directly from OASIS

2. **Complete documentation**
   - README.md explains everything
   - ARCHITECTURE.md documents design decisions
   - docs/historical-releases.md lists all 35 releases

3. **Conversion tools for UBL 2.0**
   - Crane-ods2obdgc XSLT stylesheet
   - Saxon 9 HE XSLT processor
   - Conversion scripts

4. **All source data organized**
   - history/generated/ for UBL 2.0
   - history/*-UBL-{version}/ for UBL 2.1-2.5

---

## 🚧 What Needs To Be Built

### Goal: Git History Branch with Full Evolution

**Objective:** Create a git branch (`claude/git-history-exploration-bunUn`) that shows the complete evolution of UBL semantic models through commits.

**Option K (APPROVED):**
- ✅ All 35 releases in chronological order
- ✅ Multi-step commits for schema changes (column add/remove/populate)
- ✅ Track Endorsed-Entities as separate file (NEW in 2.5)
- ✅ Reproducible via scripts

### Commit Strategy

**Simple transitions (within same version):**
- One commit per release stage
- Example: prd1-UBL-2.1 → prd2-UBL-2.1 (single commit)

**Schema changes (version transitions):**
- 6-step process for major schema changes:
  1. Add new columns (empty)
  2. Populate new columns with data
  3. Mark old columns as deprecated
  4. Remove references to old columns
  5. Remove deprecated columns
  6. Final cleanup/normalization

**Schema changes occur at:**
- 2.1 → 2.2 (6-step commit sequence)
- 2.4 → 2.5 (6-step commit sequence + add Endorsed file)

### Release Sequence (35 commits + multi-step transitions)

```
UBL 2.0 (8 commits):
prd → prd2 → prd3 → prd3r1 → cs → os → os-update → errata

UBL 2.1 (8 commits):
prd1 → prd2 → prd3 → prd4 → csd4 → cs1 → cos1 → os

2.1 → 2.2 Transition (6-step commit sequence)

UBL 2.2 (6 commits):
csprd01 → csprd02 → csprd03 → cs01 → cos01 → os

UBL 2.3 (7 commits):
csprd01 → csprd02 → csd03 → csd04 → cs01 → cs02 → os

UBL 2.4 (4 commits):
csd01 → csd02 → cs01 → os

2.4 → 2.5 Transition (6-step commit sequence + add Endorsed)

UBL 2.5 (2 commits):
csd01 → csd02
```

---

## 🔧 Scripts To Be Created

**Location:** `scripts/`

### Proposed Structure

```
scripts/
├── build-history.sh                 ← Master orchestrator
├── lib/
│   ├── common.sh                    ← Shared functions
│   └── commit-helpers.sh            ← Git commit creation
└── versions/
    ├── build-2.0.sh                 ← Process generated/ files
    ├── build-2.1.sh                 ← Process 2.1 releases
    ├── build-2.2.sh                 ← Multi-step schema + releases
    ├── build-2.3.sh                 ← Process 2.3 releases
    ├── build-2.4.sh                 ← Process 2.4 releases
    └── build-2.5.sh                 ← Multi-step + Endorsed file
```

### Key Principles

1. **Scripts in main branch** - version controlled, reviewable
2. **History branch is OUTPUT** - generated by scripts
3. **Fully reproducible** - delete history branch, re-run → identical result
4. **NO downloads in scripts** - all files already in history/
5. **Idempotent** - can re-run without breaking
6. **Documented** - each script explains what it does

---

## 🎯 Current Task

**Implement Option K:**

1. Create reproducible build scripts (scripts/)
2. Build git history branch with all 35 releases
3. Use multi-step commits for schema changes
4. Track Endorsed-Entities separately
5. Push to branch: `claude/git-history-exploration-bunUn`

---

## 💡 Important Notes

### DO:
- ✅ Read the documentation files listed above
- ✅ Use existing files from history/
- ✅ Create scripts that are reproducible
- ✅ Follow the 6-step process for schema changes
- ✅ Track all three file types (Entities, Signature, Endorsed)

### DON'T:
- ❌ Download files in scripts (already downloaded!)
- ❌ Make assumptions without reading docs
- ❌ Skip UBL 2.0 (we have generated .gc files!)
- ❌ Forget about Signature-Entities files
- ❌ Ignore the Endorsed-Entities file (new in 2.5!)

---

## 📚 Key Facts to Remember

1. **35 releases total** (not 28!)
   - UBL 2.0: 8 releases (all generated .gc files)
   - UBL 2.1-2.5: 27 releases

2. **65 GenericCode files** (not 55!)
   - Entities: 35 files (one per release)
   - Signature-Entities: 28 files (2.1-2.5, not all releases have them)
   - Endorsed-Entities: 2 files (NEW in 2.5!)

3. **UBL 2.0 GenericCode is generated**
   - Source: 30 .ods files per release
   - Tool: Crane-ods2obdgc + Saxon 9 HE
   - Location: history/generated/*-UBL-2.0/

4. **Schema changes occur twice**
   - 2.1 → 2.2: Column changes (6-step process)
   - 2.4 → 2.5: Column changes + Endorsed file (6-step + new file)

5. **Files are already here**
   - Don't download in scripts
   - Just process existing files in history/

---

## 🚀 Quick Start for Claude

```bash
# 1. Read the docs first!
cat README.md
cat ARCHITECTURE.md
cat docs/historical-releases.md

# 2. Verify all files are present
ls -1 history/generated/*/mod/*.gc  # Should show 8 UBL 2.0 files
ls -1 history/*/mod/*.gc | wc -l    # Should show 65 total files

# 3. Create scripts structure
mkdir -p scripts/{lib,versions}

# 4. Build history branch
./scripts/build-history.sh  # (to be created)

# 5. Push result
git push -u origin claude/git-history-exploration-bunUn
```

---

**Last Updated:** 2026-02-11
**Current Branch:** claude/git-history-exploration-bunUn
**Status:** Ready to build scripts and history
