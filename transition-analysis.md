# UBL Version Transition Analysis

**Date:** 2026-02-12
**Issue:** Files are accumulating instead of being renamed/transitioned
**Impact:** CRITICAL - History branch doesn't show evolution, just accumulation

---

## 🔴 **The Problem**

### Current State (WRONG):
The `origin/history-test` branch has **ALL** version files coexisting:
```
UBL-Entities-2.0.gc          ← From UBL 2.0 releases
UBL-Entities-2.1.gc          ← Added in 2.1, NEVER removed
UBL-Entities-2.2.gc          ← Added in 2.2, NEVER removed
UBL-Entities-2.3.gc          ← Added in 2.3, NEVER removed
UBL-Entities-2.4.gc          ← Added in 2.4, NEVER removed
UBL-Entities-2.5.gc          ← Added in 2.5, NEVER removed
UBL-Signature-Entities-2.1.gc
UBL-Signature-Entities-2.2.gc
UBL-Signature-Entities-2.3.gc
UBL-Signature-Entities-2.4.gc
UBL-Signature-Entities-2.5.gc
UBL-Endorsed-Entities-2.5.gc
```

**This is wrong!** At any point in time, the branch should only have the CURRENT version files.

### Expected State (CORRECT):
```
After UBL 2.0 ERRATA commit:
  └─ UBL-Entities-2.0.gc

After UBL 2.1 PRD1 commit:
  └─ UBL-Entities-2.1.gc          ← RENAMED from 2.0

After UBL 2.1 PRD3 commit:
  ├─ UBL-Entities-2.1.gc
  └─ UBL-Signature-Entities-2.1.gc  ← ADDED (new file type)

After 2.1→2.2 transition (step 6):
  ├─ UBL-Entities-2.2.gc          ← RENAMED from 2.1
  └─ UBL-Signature-Entities-2.2.gc ← RENAMED from 2.1

After 2.4→2.5 transition (step 6):
  ├─ UBL-Entities-2.5.gc          ← RENAMED from 2.4
  ├─ UBL-Signature-Entities-2.5.gc ← RENAMED from 2.4
  └─ UBL-Endorsed-Entities-2.5.gc  ← ADDED (new file type in 2.5)
```

---

## 🔍 **Root Cause Analysis**

### Issue 1: No 2.0 → 2.1 Transition

**File:** `scripts/versions/build-2.1.sh`

**What it does:**
```bash
for release in "${UBL_2_1_RELEASES[@]}"; do
    create_release_commit "$release" "$VERSION" "$release_dir"
done
```

**What it SHOULD do:**
```bash
# First, transition from 2.0 to 2.1
create_schema_transition "2.0" "2.1" "$first_release_dir"

# Then create commits for remaining releases
for release in "${UBL_2_1_RELEASES[@]:1}"; do
    create_release_commit "$release" "$VERSION" "$release_dir"
done
```

**Result:** UBL-Entities-2.1.gc was ADDED alongside 2.0, not renamed from it.

---

### Issue 2: Schema Transition Step 6 Doesn't Remove Old Files

**File:** `scripts/lib/commit-helpers.sh`
**Function:** `create_schema_transition_step6()`
**Lines:** 278-355

**What the code INTENDS to do:**
```bash
# Line 310-314: Rename old file to new name
if [ -f "$old_basename" ]; then
    git mv "$old_basename" "$new_basename"
    log_info "  Renamed: $old_basename → $new_basename"
fi

# Line 317-319: Update content
cp "$gc_file" "$new_basename"
git add "$new_basename"
```

**What ACTUALLY happens (from git log):**
```
commit 2f3f4c5 (2.1→2.2 step 6)
  create mode 100644 UBL-Entities-2.2.gc
  create mode 100644 UBL-Signature-Entities-2.2.gc
```

The files were **created** (not renamed), meaning `git mv` never executed!

**Why `git mv` didn't execute:**

Checking the commit before step 6:
```bash
$ git ls-tree b795d9b --name-only | grep ".gc$"
UBL-Entities-2.0.gc
UBL-Entities-2.1.gc
UBL-Signature-Entities-2.1.gc
```

The files DO exist! So why no rename?

**Hypothesis:** The `git mv` command might have failed silently, OR there's a logic error in the script where the condition `[ -f "$old_basename" ]` evaluates to false.

---

### Issue 3: No Cleanup of Old Version Files

Even if `git mv` worked correctly for the "main" files (Entities-2.1 → Entities-2.2), what about the OLDER versions?

After the 2.1→2.2 transition, we should have:
- ✅ UBL-Entities-2.2.gc (renamed from 2.1)
- ✅ UBL-Signature-Entities-2.2.gc (renamed from 2.1)
- ❌ UBL-Entities-2.0.gc (ORPHAN - should be removed!)

The script has NO logic to remove orphaned old version files!

---

## 📋 **What the Script Does vs What It Should Do**

### Current Behavior:

| Transition | What Happens | Files After |
|------------|--------------|-------------|
| 2.0 ERRATA → 2.1 PRD1 | ADD 2.1 file | 2.0 + 2.1 |
| 2.1 OS → 2.2 step 6 | ADD 2.2 file | 2.0 + 2.1 + 2.2 |
| 2.2 OS → 2.3 step 1-6 | (no schema transition!) | 2.0 + 2.1 + 2.2 + 2.3 |
| 2.3 OS → 2.4 step 1-6 | (no schema transition!) | 2.0 + 2.1 + 2.2 + 2.3 + 2.4 |
| 2.4 OS → 2.5 step 6 | ADD 2.5 + Endorsed | All versions! |

### Expected Behavior:

| Transition | What Should Happen | Files After |
|------------|-------------------|-------------|
| 2.0 ERRATA → 2.1 PRD1 | RENAME 2.0 → 2.1 | 2.1 only |
| 2.1 PRD3 | ADD Signature-2.1 | 2.1 + Sig-2.1 |
| 2.1 OS → 2.2 step 6 | RENAME 2.1 → 2.2 (both files) | 2.2 + Sig-2.2 |
| 2.2 OS → 2.3 first release | RENAME 2.2 → 2.3 (both files) | 2.3 + Sig-2.3 |
| 2.3 OS → 2.4 first release | RENAME 2.3 → 2.4 (both files) | 2.4 + Sig-2.4 |
| 2.4 OS → 2.5 step 6 | RENAME 2.4 → 2.5, ADD Endorsed | 2.5 + Sig-2.5 + End-2.5 |

---

## 🔧 **Required Fixes**

### Fix 1: Add 2.0 → 2.1 Transition

**File:** `scripts/versions/build-2.1.sh`

**Current (line 61-69):**
```bash
# Create commits for all releases
log_step "Creating commits for UBL 2.1 releases"

for release in "${UBL_2_1_RELEASES[@]}"; do
    local release_dir
    release_dir=$(get_release_dir "$release" ".")
    create_release_commit "$release" "$VERSION" "$release_dir"
done
```

**Should be:**
```bash
# SCHEMA TRANSITION: UBL 2.0 → 2.1 (6-step process)
log_step "Schema Transition: UBL 2.0 → 2.1"
log_info "This is a major version transition requiring 6-step commit process"

local first_release_dir
first_release_dir=$(get_release_dir "${UBL_2_1_RELEASES[0]}" ".")

create_schema_transition "2.0" "$VERSION" "$first_release_dir"

# Create commits for remaining releases (first release already done in step 6)
log_step "Creating commits for remaining UBL 2.1 releases"

for release in "${UBL_2_1_RELEASES[@]:1}"; do
    local release_dir
    release_dir=$(get_release_dir "$release" ".")
    create_release_commit "$release" "$VERSION" "$release_dir"
done
```

---

### Fix 2: Add 2.2 → 2.3 Transition

**File:** `scripts/versions/build-2.3.sh`

Currently missing schema transition! Should add the same 6-step process.

---

### Fix 3: Add 2.3 → 2.4 Transition

**File:** `scripts/versions/build-2.4.sh`

Currently missing schema transition! Should add the same 6-step process.

---

### Fix 4: Debug Why `git mv` Isn't Working

**File:** `scripts/lib/commit-helpers.sh`
**Function:** `create_schema_transition_step6()`

**Add debug logging:**
```bash
# First, identify which files need to be renamed
for gc_file in "${gc_files[@]}"; do
    local new_basename
    new_basename=$(basename "$gc_file")

    # Derive old filename by replacing version number
    local old_basename
    old_basename=$(echo "$new_basename" | sed "s/-${to_version}\.gc$/-${from_version}.gc/")

    # DEBUG: Show what we're checking
    log_info "DEBUG: Checking for old file: $old_basename"
    log_info "DEBUG: Current directory: $(pwd)"
    log_info "DEBUG: Files in directory: $(ls -1 *.gc 2>/dev/null || echo 'none')"

    if [ -f "$old_basename" ]; then
        # Rename old file to new name (preserves history)
        log_info "DEBUG: File exists, attempting git mv..."
        git mv "$old_basename" "$new_basename" || log_error "git mv failed!"
        log_info "  Renamed: $old_basename → $new_basename"
    else
        log_warning "  Old file not found: $old_basename (will create new)"
    fi

    # Update content with new version data
    cp "$gc_file" "$new_basename"
    git add "$new_basename"
    log_info "  Updated: $new_basename (content from $to_version)"
done
```

---

### Fix 5: Remove Orphaned Old Version Files

After renaming 2.1 → 2.2, we need to remove any leftover older version files!

**Add to `create_schema_transition_step6()` after the rename loop:**
```bash
# Remove any orphaned old version files (versions older than from_version)
log_info "Checking for orphaned old version files..."

# List all .gc files
for old_file in *.gc; do
    # Extract version from filename (e.g., "2.0" from "UBL-Entities-2.0.gc")
    local file_version
    file_version=$(echo "$old_file" | grep -oP '\d+\.\d+(?=\.gc$)' || echo "")

    if [[ -n "$file_version" ]]; then
        # Compare versions: if file_version < from_version, remove it
        if [[ "$file_version" != "$from_version" && "$file_version" != "$to_version" ]]; then
            log_info "  Removing orphaned file: $old_file (version $file_version)"
            git rm "$old_file"
        fi
    fi
done
```

---

## 🎯 **Expected Commit Count After Fixes**

### Current (WRONG):
- UBL 2.0: 8 commits ✅
- 2.0→2.1: 0 commits ❌ (should be 6)
- UBL 2.1: 8 commits ✅
- 2.1→2.2: 6 commits ✅
- UBL 2.2: 5 commits ✅ (first release in step 6)
- 2.2→2.3: 0 commits ❌ (should be 6)
- UBL 2.3: 7 commits ✅
- 2.3→2.4: 0 commits ❌ (should be 6)
- UBL 2.4: 4 commits ✅
- 2.4→2.5: 6 commits ✅
- UBL 2.5: 1 commit ❌ (should be 2)
- **Total:** 45 commits

### After Fixes (CORRECT):
- UBL 2.0: 8 commits
- 2.0→2.1: 6 commits ← ADDED
- UBL 2.1: 7 commits (first release done in transition step 6)
- 2.1→2.2: 6 commits
- UBL 2.2: 5 commits
- 2.2→2.3: 6 commits ← ADDED
- UBL 2.3: 6 commits (first release done in transition step 6)
- 2.3→2.4: 6 commits ← ADDED
- UBL 2.4: 3 commits (first release done in transition step 6)
- 2.4→2.5: 6 commits
- UBL 2.5: 2 commits ← FIXED (add CSD01)
- **Total:** 61 commits (not 47!)

**Wait, the original plan said 47 commits total!**

Let me recalculate based on Option K discussion:
- 35 release commits
- 12 schema transition commits (4 transitions × 6 steps - 4 releases included in step 6)
- = 47 commits

But we have 4 transitions (2.0→2.1, 2.1→2.2, 2.2→2.3, 2.3→2.4, 2.4→2.5)... that's 5 transitions!

No wait, checking CLAUDE.md:
> Schema changes occur at:
> - 2.1 → 2.2 (6-step commit sequence)
> - 2.4 → 2.5 (6-step commit sequence + add Endorsed file)

**So only TWO schema transitions were planned!**

---

## 💡 **Key Decision Needed**

### Question: How many schema transitions should there be?

**Option A: Only 2 transitions (as documented)**
- 2.1 → 2.2 (6 steps)
- 2.4 → 2.5 (6 steps)
- All other version bumps are simple file renames

**Option B: Transition at EVERY major version**
- 2.0 → 2.1 (6 steps)
- 2.1 → 2.2 (6 steps)
- 2.2 → 2.3 (6 steps)
- 2.3 → 2.4 (6 steps)
- 2.4 → 2.5 (6 steps)

**Recommendation:** Ask the user which approach they want!

The current implementation is inconsistent:
- ❌ 2.0→2.1: No transition (just adds files)
- ✅ 2.1→2.2: Has 6-step transition (but doesn't rename properly)
- ❌ 2.2→2.3: No transition
- ❌ 2.3→2.4: No transition
- ✅ 2.4→2.5: Has 6-step transition

---

## 📊 **Summary**

### Issues Found:
1. ❌ Files accumulate instead of being renamed
2. ❌ `git mv` not executing in schema transition step 6
3. ❌ No cleanup of orphaned old version files
4. ❌ Missing schema transitions for 2.0→2.1, 2.2→2.3, 2.3→2.4
5. ❌ Inconsistent strategy (some transitions, some not)

### Immediate Actions Needed:
1. **Clarify**: Which versions should have schema transitions?
2. **Debug**: Why isn't `git mv` working?
3. **Add**: Logic to remove orphaned files
4. **Fix**: Make transitions consistent

### Critical Question for User:
**"Should EVERY major version transition (2.0→2.1, 2.1→2.2, etc.) have a 6-step schema transition, or only the ones where the actual schema changed (2.1→2.2 and 2.4→2.5)?"**
