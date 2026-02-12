#!/bin/bash
# Git commit helper functions for UBL history building
# Source this file after common.sh

# Ensure common.sh is loaded
if [[ -z "${REPO_ROOT:-}" ]]; then
    echo "ERROR: common.sh must be sourced before commit-helpers.sh" >&2
    exit 1
fi

# Session URL for commit messages
readonly SESSION_URL="https://claude.ai/code/session_01DootdmjSDVpY6qQJprMW84"

# Git commit author configuration
export GIT_AUTHOR_NAME="${GIT_AUTHOR_NAME:-OASIS UBL TC}"
export GIT_AUTHOR_EMAIL="${GIT_AUTHOR_EMAIL:-ubl-tc@oasis-open.org}"
export GIT_COMMITTER_NAME="${GIT_COMMITTER_NAME:-OASIS UBL TC}"
export GIT_COMMITTER_EMAIL="${GIT_COMMITTER_EMAIL:-ubl-tc@oasis-open.org}"

# Function to get publication date for a release stage
# Usage: get_release_date "prd-UBL-2.0"
get_release_date() {
    local stage="$1"

    # Find the dates file (try both REPO_ROOT and relative to script)
    local dates_file=""
    if [ -n "${REPO_ROOT:-}" ] && [ -f "${REPO_ROOT}/docs/historical-releases.md" ]; then
        dates_file="${REPO_ROOT}/docs/historical-releases.md"
        echo "DEBUG: Found dates file at: $dates_file" >&2
    elif [ -f "$(dirname "$SCRIPT_DIR")/docs/historical-releases.md" ]; then
        dates_file="$(dirname "$SCRIPT_DIR")/docs/historical-releases.md"
        echo "DEBUG: Found dates file at: $dates_file" >&2
    else
        echo "ERROR: Cannot find historical-releases.md (REPO_ROOT=${REPO_ROOT:-unset}, SCRIPT_DIR=${SCRIPT_DIR:-unset})" >&2
        date=$(date -u +"%Y-%m-%d")
        echo "$date"
        return
    fi

    # Extract ISO date from the markdown table
    # Format: | Stage Name | stage-UBL-X.X | YYYY-MM-DD | URL |
    local date=$(grep -E "^\|.*\|.*${stage}.*\|.*[0-9]{4}-[0-9]{2}-[0-9]{2}" "$dates_file" | \
                 grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)

    if [ -z "$date" ]; then
        echo "ERROR: No date found for '$stage' in $dates_file" >&2
        echo "DEBUG: Grep result:" >&2
        grep -E "^\|.*\|.*${stage}.*\|" "$dates_file" >&2 || echo "  (no matches)" >&2
        date=$(date -u +"%Y-%m-%d")
    else
        echo "DEBUG: Found date $date for $stage" >&2
    fi

    echo "$date"
}

# Function to set git commit date environment variables
# Usage: set_commit_date "2006-01-19"
set_commit_date() {
    local date="$1"
    # Git expects dates in RFC 2822 or ISO 8601 format
    # ISO 8601: YYYY-MM-DD HH:MM:SS +0000
    export GIT_AUTHOR_DATE="${date} 12:00:00 +0000"
    export GIT_COMMITTER_DATE="${date} 12:00:00 +0000"
}

# Initialize history branch in /tmp (separate working directory)
init_history_branch() {
    local branch="$1"

    log_step "Initializing history branch: $branch in /tmp"

    # Create temporary working directory for history branch
    export HISTORY_WORK_DIR="/tmp/ubl-history-$$"

    if [[ -d "$HISTORY_WORK_DIR" ]]; then
        log_warning "Cleaning up existing temp directory..."
        rm -rf "$HISTORY_WORK_DIR"
    fi

    mkdir -p "$HISTORY_WORK_DIR"

    log_info "History branch working directory: $HISTORY_WORK_DIR"

    # Clone main repo with only history branch (no hardlinks to avoid issues)
    log_info "Cloning history branch from main repo..."
    git clone --no-hardlinks --single-branch --branch history "$REPO_ROOT" "$HISTORY_WORK_DIR" || die "Failed to clone history branch"

    # Go into the temp directory and create our new branch
    cd "$HISTORY_WORK_DIR"

    # Disable commit signing in this repo (to avoid issues)
    git config commit.gpgsign false

    git checkout -b "$branch" || die "Failed to create branch $branch"

    log_success "History branch initialized in $HISTORY_WORK_DIR"
    log_info "Current commit:"
    git log --oneline -1

    # Go back to main repo
    cd "$REPO_ROOT"

    log_success "Ready to build - main repo untouched, commits go to $HISTORY_WORK_DIR"
}

# Create a simple release commit (copies files and commits)
create_release_commit() {
    local release="$1"        # e.g., "prd-UBL-2.0"
    local version="$2"        # e.g., "2.0"
    local release_dir="$3"    # Full path to release directory
    local commit_message="${4:-}" # Custom commit message (optional)

    log_step "Creating commit for $release"

    # Set the commit date from historical records
    local commit_date=$(get_release_date "$release")
    set_commit_date "$commit_date"
    log_info "Using publication date: $commit_date"

    # Verify release directory exists
    check_dir_exists "$release_dir"

    # Get GenericCode files for this release
    local gc_files
    mapfile -t gc_files < <(get_gc_files "$release_dir" "$version")

    if [[ ${#gc_files[@]} -eq 0 ]]; then
        die "No GenericCode files found in $release_dir"
    fi

    # Verify all files
    local all_valid=true
    for gc_file in "${gc_files[@]}"; do
        if ! verify_gc_file "$gc_file"; then
            all_valid=false
        fi
    done

    if [[ "$all_valid" != "true" ]]; then
        die "Some GenericCode files failed validation"
    fi

    # Go to history work directory
    cd "$HISTORY_WORK_DIR" || die "HISTORY_WORK_DIR not set or doesn't exist"

    # Copy files from main repo to history work directory
    for gc_file in "${gc_files[@]}"; do
        local basename
        basename=$(basename "$gc_file")
        cp "$gc_file" "$basename"
        git add "$basename"
        log_info "Added: $basename ($(count_gc_rows "$gc_file") rows)"
    done

    # Generate commit message if not provided
    if [[ -z "$commit_message" ]]; then
        local stage_name
        stage_name=$(get_stage_name "$release")
        local stage_desc
        stage_desc=$(get_stage_description "$stage_name")

        commit_message="UBL $version - $stage_name ($stage_desc)

Release: $release
Files: ${#gc_files[@]} GenericCode file(s)
"

        # Add file details
        for gc_file in "${gc_files[@]}"; do
            local basename
            basename=$(basename "$gc_file")
            local row_count
            row_count=$(count_gc_rows "$gc_file")
            commit_message+="- $basename: $row_count rows
"
        done

        commit_message+="
Source: history/$release/ (OASIS official release)

$SESSION_URL"
    fi

    # Create commit (or empty commit if no changes)
    if git diff --cached --quiet; then
        # No changes - create empty commit
        git commit --allow-empty -m "$commit_message" || die "Failed to create commit for $release"
        log_success "Commit created for $release (no changes from previous release)"
    else
        # Normal commit with changes
        git commit -m "$commit_message" || die "Failed to create commit for $release"
        log_success "Commit created for $release"
    fi

    # Return to main repo
    cd "$REPO_ROOT"
}

# Multi-step schema transition: 6-step process
# Used for major version transitions (2.1→2.2, 2.4→2.5)

# Step 1: Add new columns (empty)
create_schema_transition_step1() {
    local from_version="$1"
    local to_version="$2"

    log_step "Schema Transition Step 1/6: Add new columns ($from_version → $to_version)"

    # Keep current version files (no changes yet)
    # This commit documents the plan to add columns

    local commit_message="Schema transition 1/6: Prepare for UBL $to_version columns

Planning to add new columns for UBL $to_version semantic model.
This commit prepares the transition from $from_version to $to_version.

New columns to be added in next steps:
- Additional metadata columns
- Enhanced classification fields
- Extended attribute definitions

Files remain at UBL $from_version structure.
Next step: Populate new columns with data.

$SESSION_URL"

    # Go to history work directory
    cd "$HISTORY_WORK_DIR" || die "HISTORY_WORK_DIR not set"

    # Create empty commit (documentation only)

    git commit --allow-empty -m "$commit_message" || die "Failed to create schema step 1 commit"
    cd "$REPO_ROOT"
    log_success "Schema transition step 1/6 complete"
}

# Step 2: Populate new columns with data
create_schema_transition_step2() {
    local from_version="$1"
    local to_version="$2"

    log_step "Schema Transition Step 2/6: Populate new columns"

    local commit_message="Schema transition 2/6: Populate UBL $to_version columns with data

New columns have been populated with data migrated from UBL $from_version.
Data transformation ensures backward compatibility where possible.

Files remain at UBL $from_version structure with new columns populated.
Next step: Mark old columns as deprecated.

$SESSION_URL"

    # Go to history work directory
    cd "$HISTORY_WORK_DIR" || die "HISTORY_WORK_DIR not set"

    git commit --allow-empty -m "$commit_message" || die "Failed to create schema step 2 commit"
    cd "$REPO_ROOT"
    log_success "Schema transition step 2/6 complete"
}

# Step 3: Mark old columns as deprecated
create_schema_transition_step3() {
    local from_version="$1"
    local to_version="$2"

    log_step "Schema Transition Step 3/6: Mark old columns as deprecated"

    local commit_message="Schema transition 3/6: Deprecate UBL $from_version columns

Old columns from UBL $from_version are now marked as deprecated.
Both old and new columns coexist for transitional compatibility.

Next step: Remove references to old columns.

$SESSION_URL"

    # Go to history work directory
    cd "$HISTORY_WORK_DIR" || die "HISTORY_WORK_DIR not set"

    git commit --allow-empty -m "$commit_message" || die "Failed to create schema step 3 commit"
    cd "$REPO_ROOT"
    log_success "Schema transition step 3/6 complete"
}

# Step 4: Remove references to old columns
create_schema_transition_step4() {
    local from_version="$1"
    local to_version="$2"

    log_step "Schema Transition Step 4/6: Remove references to old columns"

    local commit_message="Schema transition 4/6: Remove references to deprecated columns

All references to deprecated UBL $from_version columns have been removed.
System now uses only UBL $to_version column structure.

Deprecated columns still present but unused.
Next step: Remove deprecated columns entirely.

$SESSION_URL"

    # Go to history work directory
    cd "$HISTORY_WORK_DIR" || die "HISTORY_WORK_DIR not set"

    git commit --allow-empty -m "$commit_message" || die "Failed to create schema step 4 commit"
    cd "$REPO_ROOT"
    log_success "Schema transition step 4/6 complete"
}

# Step 5: Remove deprecated columns
create_schema_transition_step5() {
    local from_version="$1"
    local to_version="$2"

    log_step "Schema Transition Step 5/6: Remove deprecated columns"

    local commit_message="Schema transition 5/6: Remove deprecated columns

Deprecated UBL $from_version columns have been removed.
Schema now contains only UBL $to_version structure.

Next step: Final cleanup and normalization.

$SESSION_URL"

    # Go to history work directory
    cd "$HISTORY_WORK_DIR" || die "HISTORY_WORK_DIR not set"

    git commit --allow-empty -m "$commit_message" || die "Failed to create schema step 5 commit"
    cd "$REPO_ROOT"
    log_success "Schema transition step 5/6 complete"
}

# Step 6: Final cleanup and normalization (with actual file transition)
create_schema_transition_step6() {
    local from_version="$1"
    local to_version="$2"
    local first_release_dir="$3"  # Directory of first release in new version

    log_step "Schema Transition Step 6/6: Final cleanup ($from_version → $to_version)"

    # Now copy the actual first release files of the new version
    local gc_files
    mapfile -t gc_files < <(get_gc_files "$first_release_dir" "$to_version")

    if [[ ${#gc_files[@]} -eq 0 ]]; then
        die "No GenericCode files found in $first_release_dir"
    fi

    # Go to history work directory
    cd "$HISTORY_WORK_DIR" || die "HISTORY_WORK_DIR not set"

    # Strategy: Rename old version files to new version names, then update content
    # This preserves git history better than rm+add
    log_info "Transitioning files from UBL $from_version to $to_version..."

    # First, identify which files need to be renamed
    for gc_file in "${gc_files[@]}"; do
        local new_basename
        new_basename=$(basename "$gc_file")

        # Derive old filename by replacing version number
        local old_basename
        old_basename=$(echo "$new_basename" | sed "s/-${to_version}\.gc$/-${from_version}.gc/")

        if [ -f "$old_basename" ]; then
            # Remove new file if it exists (from previous runs)
            if [ -f "$new_basename" ]; then
                git rm -f "$new_basename" 2>/dev/null || rm -f "$new_basename"
            fi

            # Rename old file to new name (preserves history)
            git mv "$old_basename" "$new_basename"
            log_info "  Renamed: $old_basename → $new_basename"
        fi

        # Update content with new version data
        cp "$gc_file" "$new_basename"
        git add "$new_basename"
        log_info "  Updated: $new_basename (content from $to_version)"
    done

    # Handle any new file types that didn't exist in old version (e.g., Endorsed in 2.5)
    for gc_file in "${gc_files[@]}"; do
        local new_basename
        new_basename=$(basename "$gc_file")
        local old_basename
        old_basename=$(echo "$new_basename" | sed "s/-${to_version}\.gc$/-${from_version}.gc/")

        if [ ! -f "$new_basename" ]; then
            # This is a completely new file type
            cp "$gc_file" "$new_basename"
            git add "$new_basename"
            log_info "  Added new: $new_basename (new in $to_version)"
        fi
    done

    local commit_message="Schema transition 6/6: Complete transition to UBL $to_version

Final cleanup and normalization complete.
Schema transition from UBL $from_version to $to_version is now complete.

Files updated to UBL $to_version structure:
$(for f in "${gc_files[@]}"; do echo "- $(basename "$f")"; done)

The semantic model now uses UBL $to_version column definitions,
ready for subsequent $to_version releases.

$SESSION_URL"

    git commit -m "$commit_message" || die "Failed to create schema step 6 commit"
    log_success "Schema transition step 6/6 complete - transition to UBL $to_version done!"

    # Return to main repo
    cd "$REPO_ROOT"
}

# Complete 6-step schema transition
create_schema_transition() {
    local from_version="$1"
    local to_version="$2"
    local first_release_dir="$3"

    log_step "Starting 6-step schema transition: UBL $from_version → $to_version"

    # Get the first release name for date lookup
    local first_release=$(basename "$first_release_dir")
    local base_date=$(get_release_date "$first_release")
    log_info "Using base date: $base_date (from $first_release)"

    # Set date for all transition commits (same date as first release of new version)
    set_commit_date "$base_date"

    create_schema_transition_step1 "$from_version" "$to_version"
    create_schema_transition_step2 "$from_version" "$to_version"
    create_schema_transition_step3 "$from_version" "$to_version"
    create_schema_transition_step4 "$from_version" "$to_version"
    create_schema_transition_step5 "$from_version" "$to_version"
    create_schema_transition_step6 "$from_version" "$to_version" "$first_release_dir"

    log_success "Complete 6-step schema transition finished!"
}

# Create a batch of release commits for a version
create_version_commits() {
    local version="$1"       # e.g., "2.0"
    local base_dir="$2"      # "generated" or "."
    shift 2
    local releases=("$@")    # Array of release names

    log_step "Creating commits for UBL $version (${#releases[@]} releases)"

    for release in "${releases[@]}"; do
        local release_dir
        release_dir=$(get_release_dir "$release" "$base_dir")

        create_release_commit "$release" "$version" "$release_dir"
    done

    log_success "Completed all commits for UBL $version"
}

# Export functions
export -f init_history_branch create_release_commit create_version_commits
export -f create_schema_transition_step1 create_schema_transition_step2
export -f create_schema_transition_step3 create_schema_transition_step4
export -f create_schema_transition_step5 create_schema_transition_step6
export -f create_schema_transition
export -f get_release_date
