# GitHub Actions Workflows

This document describes the GitHub Actions workflows and build scripts that power the automated generation of UBL semantic model history branches.

## Table of Contents

- [Overview](#overview)
- [CI/CD Strategy](#cicd-strategy)
- [Workflows](#workflows)
  - [build-history.yml](#build-historyyml)
  - [build-poc-granular.yml](#build-poc-granularyml)
- [Build Scripts Architecture](#build-scripts-architecture)
- [Script Library](#script-library)
- [Workflow Triggers](#workflow-triggers)
- [Troubleshooting](#troubleshooting)

---

## Overview

This repository uses GitHub Actions to automatically build git history branches that show the complete evolution of UBL GenericCode semantic models from UBL 2.0 (2006) through UBL 2.5 (2025).

**Key principle:** The workflows and scripts are **reproducible**. Delete the history branch and re-run → identical result.

**Two approaches:**

1. **Standard History** (`history` branch) - 60 commits across 35 releases with schema transitions
2. **Ultra-Granular PoC** (`poc-granular-history` branch) - 232+ commits showing element-by-element evolution for one release

---

## CI/CD Strategy

### Design Principles

1. **Scripts in main branch** - All build scripts are version controlled and reviewable
2. **History branch is OUTPUT** - Generated branches are build artifacts, not source code
3. **Fully reproducible** - Scripts use only files in `history/` directory (no downloads)
4. **Idempotent** - Can re-run workflows without breaking
5. **Isolated execution** - Uses `/tmp` directory to avoid branch-switching issues

### Workflow Execution Model

```
┌─────────────────────────────────────────────────────────────┐
│ Main Branch (source)                                        │
│ ├── scripts/                  ← Build scripts               │
│ ├── history/                  ← Source data (65 .gc files) │
│ └── .github/workflows/        ← Workflow definitions        │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ Trigger (push/manual)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ GitHub Actions Runner                                        │
│ ├── Checkout main branch                                    │
│ ├── Create temp dir: /tmp/ubl-history-$$                   │
│ ├── Initialize orphan branch in temp dir                   │
│ ├── Run build scripts from main (operate on temp dir)      │
│ └── Push history branch back to repo                       │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ Output
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ History Branch (output)                                      │
│ └── 60 commits showing UBL evolution                        │
└─────────────────────────────────────────────────────────────┘
```

**Why `/tmp`?**
- Avoids branch switching in main repo (can cause file disappearance)
- Allows clean, reproducible builds from scratch
- Isolates build environment from development environment

---

## Workflows

### build-history.yml

**Purpose:** Builds the complete UBL semantic model evolution with 35 releases and multi-step schema transitions.

**Location:** `.github/workflows/build-history.yml`

**Output:** Creates/updates `history` branch with 60 commits:
- 35 release commits (one per UBL release stage)
- 25 schema transition commits (5 transitions × 5 steps each, final step includes first release)

#### Triggers

```yaml
# Manual trigger with custom branch name
workflow_dispatch:
  inputs:
    target_branch:
      default: 'history'

# Automatic trigger on changes to scripts or source data
push:
  branches:
    - main
    - 'claude/git-history-exploration-bunUn'
  paths:
    - 'scripts/**'
    - 'history/**'
    - '.github/workflows/build-history.yml'
```

#### Workflow Steps

1. **Checkout repository** - Full history (`fetch-depth: 0`) for proper git operations

2. **Configure Git**
   ```bash
   user.name: "OASIS UBL TC"
   user.email: "ubl-tc@oasis-open.org"
   commit.gpgsign: false
   ```

3. **Set up environment**
   - `REPO_ROOT` - Main repository path
   - `HISTORY_BRANCH` - Target branch name (default: `history`)

4. **Verify GenericCode files** - Ensures at least 60 .gc files present

5. **Set up working directory**
   - Create temp dir: `/tmp/ubl-history-$$`
   - Initialize fresh git repo with orphan branch
   - Configure authentication (copy GitHub token from main repo)

6. **Build UBL versions** (6 sequential steps)
   - UBL 2.0: 8 commits (prd → errata)
   - UBL 2.1: 13 commits (6 transition steps + 7 releases)
   - UBL 2.2: 11 commits (6 transition steps + 5 releases)
   - UBL 2.3: 12 commits (6 transition steps + 6 releases)
   - UBL 2.4: 9 commits (6 transition steps + 3 releases)
   - UBL 2.5: 7 commits (6 transition steps + 1 release)

7. **Generate summary** - Create build metadata (commit count, timestamp, workflow info)

8. **Push history branch** - Force push with retry logic (exponential backoff: 2s, 4s, 8s, 16s)

9. **Post summary** (on PR only) - Add build summary as PR comment

10. **Cleanup** - Remove temp directory

#### Runtime

- **Average duration:** 3-5 minutes
- **Timeout:** 60 minutes (default)
- **Retry strategy:** Up to 5 push attempts with exponential backoff

---

### build-poc-granular.yml

**Purpose:** Proof-of-concept showing ultra-granular history with one commit per semantic element addition.

**Location:** `.github/workflows/build-poc-granular.yml`

**Output:** Creates/updates `claude/poc-granular-history-bunUn` branch with 232+ commits showing incremental build of UBL 2.0 PRD.

#### Triggers

```yaml
# Manual trigger with option to clean start
workflow_dispatch:
  inputs:
    clean_start:
      default: true
      type: boolean

# Automatic trigger on PoC script changes
push:
  branches:
    - 'claude/git-history-exploration-bunUn'
  paths:
    - '.github/workflows/build-poc-granular.yml'
    - 'scripts/lib/gc_*.py'
```

#### Workflow Steps

1. **Checkout repository** - Full history with GitHub token

2. **Set up Python** - Python 3.11 for analyzer/builder scripts

3. **Configure Git** - Same as build-history (OASIS UBL TC)

4. **Set up environment**
   - `POC_BRANCH` - Branch name with session ID
   - `SOURCE_FILE` - UBL 2.0 PRD GenericCode file
   - `TARGET_FILE` - Output filename

5. **Delete existing PoC branch** (if `clean_start: true`)
   - Deletes remote branch to start fresh

6. **Set up working directory**
   - Create temp dir: `/tmp/ubl-poc-$$`
   - Initialize fresh orphan branch
   - Configure authenticated remote

7. **Create initial README** - Embedded documentation explaining the PoC

8. **Copy Python scripts** - Analyzer, builder, and commit builder

9. **Run PoC builder** - Python script creates 232+ commits:
   - **Phase 1:** 34 commits - Leaf ABIEs (no dependencies) with all BBIEs + ASBIEs
   - **Phase 2:** 99 commits - Non-leaf ABIEs with BBIEs only (defer ASBIEs)
   - **Phase 3:** 99 commits - Add deferred ASBIEs (all references now valid)

10. **Push PoC branch** - Retry up to 4 times with exponential backoff

11. **Summary** - Print commit count and view instructions

#### Runtime

- **Average duration:** 8-12 minutes
- **Timeout:** 90 minutes
- **Retry strategy:** Up to 4 push attempts with exponential backoff

#### Incremental Build Strategy

The PoC demonstrates dependency-aware incremental building:

```
Step 1: 🌱 Add leaf ABIE: Address Line
  ├─ Add ABIE definition
  ├─ Add all BBIEs (attributes)
  └─ Add all ASBIEs (associations) ← Safe because no dependencies

Step 35: 🏗️ Add ABIE+BBIEs: Application Response
  ├─ Add ABIE definition
  ├─ Add all BBIEs (attributes)
  └─ Skip ASBIEs (would create forward references)

Step 134: 🔗 Add ASBIEs: Application Response
  └─ Add all ASBIEs (now safe, dependencies exist)
```

**Result:** File is valid XML at every commit, no forward references.

---

## Build Scripts Architecture

### Directory Structure

```
scripts/
├── build-history.sh              # Master orchestrator
├── build-poc-granular.sh         # PoC manual runner (local)
├── run-poc-granular.py           # PoC Python runner
├── lib/                          # Shared libraries
│   ├── common.sh                 # Utility functions
│   ├── commit-helpers.sh         # Git commit creation
│   ├── gc_analyzer.py            # GenericCode parser
│   ├── gc_builder.py             # Build planner
│   └── gc_commit_builder.py      # Incremental commit creator
└── versions/                     # Version-specific builders
    ├── build-2.0.sh              # UBL 2.0 (8 commits)
    ├── build-2.1.sh              # UBL 2.1 (6 transitions + 7 releases)
    ├── build-2.2.sh              # UBL 2.2 (6 transitions + 5 releases)
    ├── build-2.3.sh              # UBL 2.3 (6 transitions + 6 releases)
    ├── build-2.4.sh              # UBL 2.4 (6 transitions + 3 releases)
    └── build-2.5.sh              # UBL 2.5 (6 transitions + 1 release)
```

### build-history.sh

**Master orchestrator** that runs all version builders in sequence.

**Responsibilities:**
- Validate repository structure
- Initialize history branch in `/tmp`
- Run version builders (2.0 → 2.5)
- Push history branch back to main repo
- Clean up temp directory

**Key features:**
- Ensures execution from `main` branch
- Sets up trap for cleanup on exit
- Validates all files before building
- Provides detailed progress logging

**Usage:**
```bash
./scripts/build-history.sh
```

### Version Builders

Each version builder (`build-X.X.sh`) handles one UBL version:

**UBL 2.0 (build-2.0.sh):**
- Simplest: 8 sequential commits
- Source: `history/generated/*-UBL-2.0/` (generated from .ods)
- No transitions (first version)

**UBL 2.1-2.5 (build-2.X.sh):**
- Start with 6-step schema transition from previous version
- Then create commits for remaining releases
- Source: `history/*-UBL-X.X/` (OASIS official releases)

**Example: build-2.1.sh**
```bash
# 1. Schema transition (UBL 2.0 → 2.1)
create_schema_transition "2.0" "2.1" "$first_release_dir"
  # Creates 6 commits:
  #   1. Prepare for new columns
  #   2. Populate new columns
  #   3. Deprecate old columns
  #   4. Remove references to old columns
  #   5. Remove deprecated columns
  #   6. Final cleanup + first release (prd1-UBL-2.1)

# 2. Remaining releases (prd2 through os)
for release in "${UBL_2_1_RELEASES[@]:1}"; do
  create_release_commit "$release" "2.1" "$release_dir"
done
```

### 6-Step Schema Transition Process

Major version transitions (2.0→2.1, 2.1→2.2, 2.2→2.3, 2.3→2.4, 2.4→2.5) use a multi-step process:

| Step | Action | Example Commit Message |
|------|--------|----------------------|
| 1 | **Prepare columns** | "Schema transition 1/6: Prepare for UBL 2.1 columns" |
| 2 | **Populate data** | "Schema transition 2/6: Populate UBL 2.1 columns with data" |
| 3 | **Deprecate old** | "Schema transition 3/6: Deprecate UBL 2.0 columns" |
| 4 | **Remove references** | "Schema transition 4/6: Remove references to deprecated columns" |
| 5 | **Remove columns** | "Schema transition 5/6: Remove deprecated columns" |
| 6 | **Finalize + first release** | "UBL 2.1 - PRD1 + Schema Transition 6/6" |

**Why 6 steps?**
- Documents the migration process
- Shows intermediate states
- Makes schema changes auditable
- Demonstrates backward compatibility period

**Note:** Steps 1-5 are documentation-only (empty commits). Step 6 performs actual file transition:
- Renames files: `UBL-Entities-2.0.gc` → `UBL-Entities-2.1.gc`
- Updates content with new version data
- Represents first release of new version

---

## Script Library

### lib/common.sh

**Core utilities** used by all build scripts.

**Key Functions:**

| Function | Purpose | Example |
|----------|---------|---------|
| `log_info()` | Blue informational messages | `log_info "Processing UBL 2.1"` |
| `log_success()` | Green success messages | `log_success "Build complete"` |
| `log_error()` | Red error messages | `log_error "File not found"` |
| `log_step()` | Section headers | `log_step "Building UBL 2.0"` |
| `die()` | Exit with error | `die "Invalid state"` |
| `validate_repo_structure()` | Check directories exist | Validates `history/`, `history/tools/` |
| `get_release_dir()` | Get full path to release | `get_release_dir "prd-UBL-2.0" "generated"` |
| `get_gc_files()` | Find GenericCode files | Returns array of .gc file paths |
| `count_gc_rows()` | Count rows in file | `count_gc_rows "UBL-Entities-2.1.gc"` |
| `verify_gc_file()` | Validate XML structure | Checks well-formed XML, row count |
| `get_stage_name()` | Extract stage name | `"prd1-UBL-2.1"` → `"PRD1"` |
| `get_stage_description()` | Full stage name | `"prd"` → `"Proposed Recommendation Draft"` |

**Constants:**
- `REPO_ROOT` - Repository root directory
- `HISTORY_DIR` - `$REPO_ROOT/history`
- `SESSION_SUFFIX` - Branch naming suffix (`bunUn`)
- `HISTORY_BRANCH` - Output branch name

### lib/commit-helpers.sh

**Git operations** for creating commits with proper metadata.

**Key Functions:**

| Function | Purpose | Example |
|----------|---------|---------|
| `get_release_date()` | Look up publication date | `get_release_date "prd-UBL-2.0"` → `"2006-01-19"` |
| `set_commit_date()` | Set git commit timestamp | `set_commit_date "2006-01-19"` |
| `init_history_branch()` | Create history branch in /tmp | Initializes orphan branch |
| `create_release_commit()` | Create commit for a release | Copies .gc files, commits |
| `create_schema_transition()` | Run 6-step transition | Creates 6 commits |
| `create_version_commits()` | Batch release commits | Loops over release array |

**Git Configuration:**
- Author: `OASIS UBL TC <ubl-tc@oasis-open.org>`
- Dates: Historical publication dates from `docs/historical-releases.md`
- Signing: Disabled (`commit.gpgsign false`)

**Commit Message Format:**
```
UBL 2.1 - PRD1 (Proposed Recommendation Draft)

Release: prd1-UBL-2.1
Files: 2 GenericCode file(s)
- UBL-Entities-2.1.gc: 1234 rows
- UBL-Signature-Entities-2.1.gc: 567 rows

Source: history/prd1-UBL-2.1/ (OASIS official release)

https://claude.ai/code/session_01DootdmjSDVpY6qQJprMW84
```

### lib/gc_analyzer.py

**Python GenericCode parser** for analyzing semantic model structure.

**Purpose:** Parse XML GenericCode files and build dependency graph for incremental building.

**Key Classes:**

- `GCAnalyzer` - Main parser class
  - `parse()` - Load and parse XML
  - `build_abies()` - Extract ABIE definitions
  - `build_dependency_graph()` - Analyze ASBIE references
  - `get_leaf_abies()` - Find ABIEs with no dependencies

**Data Structures:**
```python
abies = {
    "Application Response. Details": {
        "name": "Application Response",
        "object_class_term_name": "Application Response",
        "bbies": [...],     # Basic Business Information Entities (attributes)
        "asbies": [...],    # Association BIEs (references to other ABIEs)
        "deps": {...}       # Dependency set
    }
}
```

**Usage:**
```python
analyzer = GCAnalyzer("UBL-Entities-2.0.gc")
analyzer.parse()
analyzer.build_abies()
analyzer.build_dependency_graph()

leaf_abies = analyzer.get_leaf_abies()  # ABIEs with no dependencies
```

### lib/gc_builder.py

**Build planner** for incremental GenericCode construction.

**Purpose:** Plan the order of element additions to avoid forward references.

**Key Classes:**

- `GCBuilder` - Build planner
  - `plan_build()` - Create 3-phase build plan
  - `generate_build_plan_summary()` - Human-readable plan

**Build Phases:**

1. **Phase 1: Leaf ABIEs** (complete)
   - Add ABIEs with no dependencies
   - Include all BBIEs and ASBIEs
   - Safe: no forward references possible

2. **Phase 2: Non-leaf ABIEs + BBIEs** (partial)
   - Add ABIEs with dependencies
   - Include BBIEs only
   - Skip ASBIEs (would create forward references)

3. **Phase 3: ASBIEs** (complete associations)
   - Add deferred ASBIEs
   - Now safe: all referenced ABIEs exist

**Output:**
```python
[
  {"phase": 1, "abie": "Address Line", "add_bbies": True, "add_asbies": True},
  {"phase": 2, "abie": "Application Response", "add_bbies": True, "add_asbies": False},
  {"phase": 3, "abie": "Application Response", "add_bbies": False, "add_asbies": True}
]
```

### lib/gc_commit_builder.py

**Incremental commit creator** using the build plan.

**Purpose:** Execute build plan and create git commits for each step.

**Key Classes:**

- `GCCommitBuilder` - Commit creator
  - `create_empty_gc_file()` - Initialize empty XML structure
  - `build_incremental()` - Execute build plan with commits
  - `_git_add_and_commit()` - Create git commit

**Commit Emojis:**
- 🌱 Phase 1 - Leaf ABIEs
- 🏗️ Phase 2 - Non-leaf ABIEs + BBIEs
- 🔗 Phase 3 - ASBIEs

**Usage:**
```python
builder = GCCommitBuilder(source_file, target_file, work_dir)
builder.create_empty_gc_file()
builder._git_add_and_commit("Initialize empty structure")
builder.build_incremental(build_steps)
```

---

## Workflow Triggers

### Automatic Triggers

**build-history.yml** runs automatically when:
- Changes pushed to `main` branch affecting:
  - `scripts/**`
  - `history/**`
  - `.github/workflows/build-history.yml`
- Changes pushed to `claude/git-history-exploration-bunUn` (feature branch testing)

**build-poc-granular.yml** runs automatically when:
- Changes pushed to `claude/git-history-exploration-bunUn` affecting:
  - `.github/workflows/build-poc-granular.yml`
  - `scripts/lib/gc_*.py`

### Manual Triggers

Both workflows support manual dispatch via GitHub UI or CLI:

```bash
# Trigger build-history workflow
gh workflow run build-history.yml \
  --repo kduvekot/ubl-gc \
  --field target_branch=history

# Trigger PoC workflow with fresh start
gh workflow run build-poc-granular.yml \
  --repo kduvekot/ubl-gc \
  --field clean_start=true
```

### Checking Workflow Status

```bash
# List recent workflow runs
gh run list --repo kduvekot/ubl-gc --workflow=build-history.yml --limit 5

# View specific run
gh run view --repo kduvekot/ubl-gc <run-id>

# View logs
gh run view --repo kduvekot/ubl-gc <run-id> --log
```

---

## Troubleshooting

### Common Issues

#### 1. Workflow fails at "Verify all GenericCode files present"

**Symptom:** File count < 60

**Cause:** GenericCode files not committed to repository

**Solution:**
```bash
# Check file count
find history -name "*.gc" | wc -l

# Should show 65 files
# If missing, re-run download/generation scripts
```

#### 2. Push fails with "403 Forbidden"

**Symptom:** `git push` returns 403

**Cause:** GitHub token not properly configured

**Solution:** Workflow automatically copies auth from main repo. If still fails:
```yaml
# Check workflow has proper permissions
permissions:
  contents: write
```

#### 3. Schema transition fails on file rename

**Symptom:** `git mv` fails with "destination exists"

**Cause:** Previous run left files in temp directory

**Solution:** Workflow always creates fresh temp dir (`/tmp/ubl-history-$$`). If running locally:
```bash
rm -rf /tmp/ubl-history-*
```

#### 4. Build runs but produces wrong commit count

**Symptom:** Expected 60 commits, got different number

**Cause:** Version builder not executing or skipping releases

**Solution:**
```bash
# Check logs for which builders ran
# Verify all release directories exist
ls -1 history/*-UBL-*/mod/*.gc | wc -l
```

#### 5. Commits have wrong dates

**Symptom:** All commits show current date

**Cause:** `docs/historical-releases.md` not found or malformed

**Solution:**
```bash
# Verify dates file exists
cat docs/historical-releases.md | grep "| prd-UBL-2.0"

# Should show: | ... | prd-UBL-2.0 | 2006-01-19 | ...
```

#### 6. Python PoC workflow fails

**Symptom:** `ModuleNotFoundError` or import errors

**Cause:** Python scripts not in path

**Solution:** Workflow copies scripts to temp dir. Check:
```yaml
# Ensure copy step succeeded
- name: Copy Python scripts
  run: |
    mkdir -p scripts/lib
    cp "$REPO_ROOT"/scripts/lib/gc_*.py scripts/lib/
```

### Debug Mode

For detailed debugging, add to workflow:

```yaml
- name: Debug environment
  run: |
    echo "PWD: $(pwd)"
    echo "REPO_ROOT: $REPO_ROOT"
    echo "HISTORY_WORK_DIR: $HISTORY_WORK_DIR"
    ls -la
    git status
    git log --oneline -5
```

### Local Testing

Test workflows locally before pushing:

```bash
# Test build-history workflow
./scripts/build-history.sh

# Test specific version builder
export HISTORY_WORK_DIR="/tmp/test-history-$$"
mkdir -p "$HISTORY_WORK_DIR"
cd "$HISTORY_WORK_DIR"
git init
git checkout --orphan history
bash /path/to/ubl-gc/scripts/versions/build-2.0.sh

# Test PoC builder
./scripts/build-poc-granular.sh
```

### Checking Output

Verify history branch contents:

```bash
# Clone history branch
git fetch origin history
git checkout history

# Check commit count
git rev-list --count HEAD

# View commit history
git log --oneline --graph

# Check file evolution
git log --follow -- UBL-Entities-2.1.gc

# Compare releases
git diff <commit1> <commit2> -- UBL-Entities-2.1.gc
```

---

## Additional Resources

- **Architecture:** [ARCHITECTURE.md](../ARCHITECTURE.md) - System design decisions
- **Build Analysis:** [build-analysis.md](../build-analysis.md) - Detailed build process analysis
- **Transition Analysis:** [transition-analysis.md](../transition-analysis.md) - Schema transition design
- **Historical Releases:** [historical-releases.md](historical-releases.md) - All 35 UBL releases with dates
- **Claude Guide:** [CLAUDE.md](../CLAUDE.md) - Repository guide for Claude Code sessions

---

**Last Updated:** 2026-02-12
**Maintainer:** UBL GenericCode History Project
**License:** See repository LICENSE file
