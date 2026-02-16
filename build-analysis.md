# UBL History Build - Analysis & Recommendations

> **Note (2026-02-13):** The shell-based build scripts analyzed in this document
> (`build-history.sh`, `lib/common.sh`, `lib/commit-helpers.sh`,
> `versions/build-2.0.sh` through `build-2.5.sh`, `build-poc-granular.sh`,
> `run-poc-granular.py`, and `.github/workflows/build-poc-granular.yml`) were
> **removed in commit `76e0538`** on 2026-02-13 and replaced by
> `scripts/build_history.py` with supporting Python modules in `scripts/lib/`.
> The issues and recommendations below were addressed in the Python rewrite.
> This document is retained as historical context for the design decisions that
> shaped the current implementation.

**Date:** 2026-02-12
**Branch:** claude/git-history-exploration-bunUn
**Analyzed:** Scripts, workflow, and actual output (origin/history-test)

---

## 📊 **What Was Actually Built**

### ✅ **SUCCESS: Workflow Created Complete History**

The GitHub Actions workflow successfully created a complete UBL history:
- **Branch:** `origin/history-test`
- **Total commits:** 46 (1 init + 45 UBL evolution commits)
- **Versions covered:** UBL 2.0 through UBL 2.5
- **File types:** Entities, Signature-Entities, Endorsed-Entities

### Commit Breakdown:
```
UBL 2.0: 8 commits (prd → prd2 → prd3 → prd3r1 → cs → os → os-update → errata)
UBL 2.1: 8 commits (prd1 → prd2 → prd3 → prd4 → csd4 → cs1 → cos1 → os)
2.1→2.2: 6 schema transition commits
UBL 2.2: 5 commits (csprd01 → csprd02 → csprd03 → cs01 → cos01 → os)
UBL 2.3: 7 commits (csprd01 → csprd02 → csd03 → csd04 → cs01 → cs02 → os)
UBL 2.4: 4 commits (csd01 → csd02 → cs01 → os)
2.4→2.5: 6 schema transition commits
UBL 2.5: 1 commit (csd02 only - MISSING csd01!)
```

**Expected:** 47 commits (35 releases + 12 schema transitions + 1 init)
**Actual:** 46 commits
**Missing:** UBL 2.5 CSD01

---

## ✅ **What Was Good**

### 1. **Excellent Script Organization**
```
scripts/
├── build-history.sh          # Master orchestrator
├── lib/
│   ├── common.sh            # Shared utilities (logging, validation)
│   └── commit-helpers.sh    # Git operations
└── versions/
    ├── build-2.0.sh         # Clean, focused builders
    ├── build-2.1.sh
    ├── build-2.2.sh (with schema transition)
    ├── build-2.3.sh
    ├── build-2.4.sh
    └── build-2.5.sh (with schema transition)
```

**Strengths:**
- ✅ Modular design (each version = one builder)
- ✅ Reusable functions in lib/
- ✅ Clear separation of concerns
- ✅ Well-documented with inline comments
- ✅ Follows bash best practices (set -euo pipefail, readonly vars)

### 2. **Multi-Step Schema Transitions**
The 6-step commit process for major version changes is **brilliant**:
1. Plan new columns
2. Populate columns
3. Deprecate old columns
4. Remove references
5. Remove deprecated columns
6. Final cleanup + actual file transition

**Why this is good:**
- Shows evolution, not just before/after
- Documents migration path
- Enables git bisect across schema changes
- Mirrors real-world database migrations

### 3. **/tmp Isolation Strategy**
Building history in `/tmp/ubl-history-$$` instead of in-place:
- ✅ Keeps main repo clean
- ✅ Avoids branch switching issues
- ✅ Treats history as "compiled artifact"
- ✅ Scripts = source code (main branch), history = output (separate branch)

### 4. **GitHub Actions Workflow**
The workflow (`.github/workflows/build-history.yml`) works correctly:
- ✅ Manual trigger + auto trigger on script changes
- ✅ Proper /tmp isolation
- ✅ Authentication handling for push
- ✅ Retry logic for network failures
- ✅ Build summary generation

### 5. **Documentation**
- ✅ CLAUDE.md provides clear context for AI
- ✅ README.md explains the project
- ✅ ARCHITECTURE.md documents decisions
- ✅ docs/historical-releases.md lists all 35 releases

---

## ❌ **What Needs To Change**

### 1. **🔴 CRITICAL: Master Script Never Executes Builders**

**File:** `scripts/build-history.sh`
**Line:** 63-76
**Bug:** Prints "Total builders: 6" then stops

**Problem:**
```bash
for builder in "${BUILDERS[@]}"; do
    ((builder_count++))
    log_step "Builder $builder_count/${#BUILDERS[@]}: $builder"

    # Run the builder from main repo
    local builder_path="$REPO_ROOT/$builder"
    if ! bash "$builder_path"; then
        die "Builder failed: $builder"
    fi
done
```

The code looks correct, but there's a hidden issue: the `init_history_branch` function (line 56) clones from the `history` branch, which may not exist yet!

**Fix needed:**
```bash
# In commit-helpers.sh, init_history_branch() should:
# 1. Check if history branch exists
# 2. If not, create orphan branch with initial commit
# 3. If yes, clone it
```

### 2. **🟡 REDUNDANCY: Two Build Systems**

**Problem:** We have BOTH:
1. `scripts/build-history.sh` - Local execution (orchestrates builders)
2. `.github/workflows/build-history.yml` - Workflow execution (calls builders directly)

**Issues:**
- Workflow duplicates orchestration logic
- Two different execution paths to maintain
- Workflow worked, script didn't (because of init_history_branch bug)

**Recommendation:** Pick ONE approach:

**Option A (Recommended): Workflow calls master script**
```yaml
- name: Build complete history
  run: bash scripts/build-history.sh
```
- ✅ Single source of truth
- ✅ Can test locally with same command
- ✅ Workflow just handles environment setup

**Option B: Delete master script, keep workflow**
- ❌ Can't test locally easily
- ❌ Workflow becomes complex
- ❌ Loses modularity

### 3. **🟡 Missing UBL 2.5 CSD01 Release**

**Expected:** 2 UBL 2.5 releases (csd01 + csd02)
**Actual:** Only csd02 present in history-test branch

**File:** `scripts/versions/build-2.5.sh`
**Check:** Does it define both releases?

### 4. **🟡 File Naming Doesn't Reflect Release Stage**

**Current behavior:**
- All UBL 2.0 releases use: `UBL-Entities-2.0.gc`
- All UBL 2.1 releases use: `UBL-Entities-2.1.gc`
- Git tracks changes to same filename

**What was discussed (Option K):**
> "Flat like option A but with name changes to reflect the name at that moment in time"

**Expected:** Files renamed per release stage:
- prd-UBL-2.0: `UBL-Entities-2.0-prd.gc`
- prd2-UBL-2.0: `UBL-Entities-2.0-prd2.gc`
- etc.

**Current pros:**
- ✅ Git diff shows actual changes between releases
- ✅ Simpler file structure

**Option K pros:**
- ✅ Each release has unique filename
- ✅ Can checkout any commit and see the release stage in filename
- ✅ Better for archaeological browsing

**Recommendation:** Keep current approach OR clarify in CLAUDE.md that Option K means "version number changes" not "stage name changes"

### 5. **🟡 No Git Tags for Stable References**

**What was discussed:**
> "if someone wanted to regenerate the UBL XSDs from the GC as it was at a certain moment in time .. can they pinpoint to that moment in time with a 'string' (so .. prd2-UBL-2.1) or a specific date/time .. instead of a 'possibly' changing SHA hash?"

**Answer:** Use git tags!

**Missing:** No tags created for releases

**Needed:**
```bash
git tag "prd2-UBL-2.1" <commit-sha>
git tag "os-UBL-2.3" <commit-sha>
# etc for all 35 releases
```

**Benefits:**
- ✅ Stable references even if history is rewritten
- ✅ Easy to checkout: `git checkout prd2-UBL-2.1`
- ✅ Tags can include metadata (annotated tags with release dates)

### 6. **🟡 No Historical Commit Dates**

**Current:** All commits timestamped when workflow ran (Feb 11, 2026)

**Desired:** Commits should use actual OASIS release dates

**File:** `scripts/lib/commit-helpers.sh`
**Line:** 395-401 (get_release_date function)

```bash
# TODO: Extract actual release dates from OASIS metadata
# For now, use current date
date -R
```

**What's needed:**
1. Add release date metadata (maybe `scripts/release-dates.json`)
2. Update `create_release_commit` to set GIT_AUTHOR_DATE and GIT_COMMITTER_DATE
3. Parse dates from OASIS URLs or docs/historical-releases.md

**Example:**
```bash
GIT_AUTHOR_DATE="2006-04-03T10:00:00Z" \
GIT_COMMITTER_DATE="2006-04-03T10:00:00Z" \
git commit -m "..."
```

### 7. **🟡 Unclear Local vs Workflow Execution Strategy**

**Questions:**
- Should users run `build-history.sh` locally?
- Should workflow be the ONLY way to build?
- What's the developer workflow for testing changes?

**Recommendation:** Document in README:
```markdown
## Building History Branch

### Production (Recommended):
Push to main branch → Workflow auto-builds → Check history-test branch

### Development/Testing:
1. Modify scripts locally
2. Run: `bash scripts/build-history.sh`
3. Review output in /tmp/ubl-history-$$
4. Push to feature branch to test workflow
```

---

## 📋 **Recommended Action Plan**

### Priority 1 (CRITICAL):
1. ✅ **Fix init_history_branch** to handle missing history branch
2. ✅ **Add missing UBL 2.5 CSD01** commit
3. ✅ **Test build-history.sh locally** to verify it works

### Priority 2 (Important):
4. ✅ **Simplify workflow** to call build-history.sh instead of duplicating logic
5. ✅ **Add git tags** for all 35 releases
6. ✅ **Document execution strategy** in README

### Priority 3 (Nice to have):
7. ⏸️ **Add historical commit dates** (requires research of OASIS dates)
8. ⏸️ **Clarify Option K** file naming in CLAUDE.md
9. ⏸️ **Add validation tests** (check commit count, file count, etc.)

---

## 🎯 **Bottom Line**

### ✅ **Successes:**
- Workflow builds complete history (46/47 commits)
- Script architecture is excellent
- Multi-step schema transitions work perfectly
- /tmp isolation prevents branch switching issues
- Documentation is comprehensive

### ❌ **Issues:**
- Master script has init bug (never executes)
- Missing 1 UBL 2.5 commit
- Redundant build systems (script vs workflow)
- No git tags for stable references
- No historical dates on commits

### 💡 **Key Insight:**
**The workflow succeeded where the script failed** - but both should work! The workflow bypasses the master orchestrator and calls builders directly. This works but creates maintenance burden.

**Recommended path forward:**
1. Fix the init_history_branch bug
2. Make workflow call the master script
3. Add missing UBL 2.5 commit
4. Add git tags
5. Push to `claude/history-bunUn` branch

---

## 📊 **Stats**

- **Lines of script code:** ~800 (well-organized!)
- **Lines of workflow code:** ~220 (could be reduced to ~50 if calling master script)
- **Commits created:** 46/47 (98% complete!)
- **File types tracked:** 3 (Entities, Signature, Endorsed)
- **Version coverage:** 2.0 → 2.5 ✅
- **Schema transitions:** 2 (2.1→2.2, 2.4→2.5) ✅

**Overall assessment:** 🌟🌟🌟🌟 (4/5 stars)
- Solid architecture, minor execution bugs, one missing commit
