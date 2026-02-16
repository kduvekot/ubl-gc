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
- **Total Files:** 62 GenericCode (.gc) files
- **Status:** All source files downloaded and organized

### Version Breakdown

| Version | Releases | Files | Source | Status |
|---------|----------|-------|--------|--------|
| **UBL 2.0** (2006) | 8 | 8 generated .gc | history/generated/ | ✅ Complete |
| **UBL 2.1** (2013) | 8 | 14 .gc (2 per release except prd1/prd2 which lack Signature) | history/*-UBL-2.1/ | ✅ Complete |
| **UBL 2.2** (2018) | 6 | 12 .gc (2 per release) | history/*-UBL-2.2/ | ✅ Complete |
| **UBL 2.3** (2021) | 7 | 14 .gc (2 per release) | history/*-UBL-2.3/ | ✅ Complete |
| **UBL 2.4** (2024) | 4 | 8 .gc (2 per release) | history/*-UBL-2.4/ | ✅ Complete |
| **UBL 2.5** (2025) | 2 | 6 .gc (3 per release: Entities + Signature + Endorsed) | history/*-UBL-2.5/ | ✅ Complete |
| **TOTAL** | **35** | **62 files** | | |

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

**Transitions occur at ALL major version bumps:**
- 2.0 → 2.1 (6-step: filename changes)
- 2.1 → 2.2 (6-step: filename + column structure changes)
- 2.2 → 2.3 (6-step: filename changes)
- 2.3 → 2.4 (6-step: filename changes)
- 2.4 → 2.5 (6-step: filename + column structure changes + add Endorsed file)

### Release Sequence (35 release commits + 30 transition commits = 60 total)

```
UBL 2.0 (8 commits):
prd → prd2 → prd3 → prd3r1 → cs → os → os-update → errata

2.0 → 2.1 Transition (6-step commit sequence)

UBL 2.1 (7 commits - prd1 done in transition step 6):
prd2 → prd3 → prd4 → csd4 → cs1 → cos1 → os

2.1 → 2.2 Transition (6-step commit sequence)

UBL 2.2 (5 commits - csprd01 done in transition step 6):
csprd02 → csprd03 → cs01 → cos01 → os

2.2 → 2.3 Transition (6-step commit sequence)

UBL 2.3 (6 commits - csprd01 done in transition step 6):
csprd02 → csd03 → csd04 → cs01 → cs02 → os

2.3 → 2.4 Transition (6-step commit sequence)

UBL 2.4 (3 commits - csd01 done in transition step 6):
csd02 → cs01 → os

2.4 → 2.5 Transition (6-step commit sequence + add Endorsed)

UBL 2.5 (1 commit - csd01 done in transition step 6):
csd02
```

---

## 🔧 Scripts To Be Created

**Location:** `scripts/`

### Actual Structure (Python-based)

```
scripts/
├── build_history.py                 ← Master orchestrator (Python)
├── lib/
│   ├── gc_diff.py                   ← GenericCode diff engine
│   ├── gc_analyzer.py               ← Column/row analysis
│   ├── gc_builder.py                ← File construction
│   ├── gc_commit_builder.py         ← Git commit creation
│   └── release_manifest.py          ← Release metadata
├── download-oasis-distributions.sh  ← OASIS file downloader
└── extract-xsd-from-reference.sh    ← XSD extraction
```

> **Note:** An earlier shell-based approach (`build-history.sh`, `common.sh`,
> `commit-helpers.sh`, `build-2.X.sh`) was planned but replaced by the Python
> system above. Some older docs may still reference the shell scripts.

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

2. **62 GenericCode files** (not 55!)
   - Entities: 35 files (one per release)
   - Signature-Entities: 25 files (2.1-2.5; prd1/prd2 of 2.1 lack Signature)
   - Endorsed-Entities: 2 files (NEW in 2.5!)

3. **UBL 2.0 GenericCode is generated**
   - Source: 30 .ods files per release
   - Tool: Crane-ods2obdgc + Saxon 9 HE
   - Location: history/generated/*-UBL-2.0/

4. **Transitions occur at every major version**
   - All version bumps use 6-step transition process
   - Tracks filename changes (e.g., 2.0.gc → 2.1.gc)
   - Column structure changes: 2.1→2.2 and 2.4→2.5
   - New file type: Endorsed-Entities in 2.5

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

# 6. Check workflow status (use --repo for this local git server)
gh run list --repo kduvekot/ubl-gc --workflow=build-history.yml --limit 5

# 7. View workflow logs if there are failures
gh run view --repo kduvekot/ubl-gc <run-id> --log
```

---

## 🧠 Session Memory Tool

A session data extraction tool is available at `.claude/scripts/claude-memory`.
Run it with `--help` for full usage, workflow, and examples.

```bash
.claude/scripts/claude-memory --help
```

**Common commands:**
```bash
# Search for specific discussions
.claude/scripts/claude-memory search "keyword"

# View conversation history (compact)
.claude/scripts/claude-memory conversation --last 20

# Quick session index
.claude/scripts/claude-memory topics

# Check token usage and costs
.claude/scripts/claude-memory tokens
```

**When to use:**
- After context compression to retrieve details lost in summary
- To recall specific decisions or discussions
- To find what was agreed upon about implementation details

---

## Task Subagents

### How to call them

The Task tool has TWO separate parameters — don't confuse them:

- **`subagent_type`** — which agent capability: `"general-purpose"`, `"Bash"`, `"Explore"`, `"Plan"`, `"claude-code-guide"`, `"statusline-setup"`
- **`model`** — which LLM to run it on: `"haiku"`, `"sonnet"`, `"opus"`

**Correct example:**
```
Task(subagent_type="general-purpose", model="haiku", prompt="Write a script that...")
```

**Wrong** (model is not a subagent_type):
```
Task(subagent_type="haiku", ...)  ← ERROR: 'haiku' is not an agent type
```

### Which model for what

| Model | Cost | Use for |
|-------|------|---------|
| **haiku** | Cheapest | File searches, grep, log parsing, clear-cut scripting, well-defined tasks |
| **sonnet** | Medium | Code analysis, moderate reasoning, multi-file changes |
| **opus** | Expensive | Complex debugging, architecture decisions, ambiguous investigations |

Default to **haiku** unless the task clearly needs more reasoning.

### Show prompts to the user

When delegating to a subagent, **always show the prompt** in your response text
before the tool call, so the user can see what you're asking and learn from it.
Format it as a brief quote, e.g.:

> Delegating to haiku: "Search for all .gc files in history/ and count them per version"

This makes the delegation visible and reviewable.

---

**Last Updated:** 2026-02-15
**Current Branch:** claude/google-sheets-history-cQ6AV
**Status:** Google Sheets discovery complete, revision content download next
