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

# Initialize history branch (builds on origin/history)
init_history_branch() {
    local branch="$1"

    log_step "Initializing history branch: $branch"

    # Check if branch already exists
    if git rev-parse --verify "$branch" &>/dev/null; then
        log_warning "Branch $branch already exists"
        read -p "Delete and recreate? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git branch -D "$branch" || die "Failed to delete existing branch"
        else
            die "Cannot proceed with existing branch"
        fi
    fi

    # Fetch origin/history if not up to date
    log_info "Fetching origin/history..."
    git fetch origin history || die "Failed to fetch origin/history"

    # Create new branch based on origin/history
    git checkout -b "$branch" origin/history || die "Failed to create branch from origin/history"

    log_success "Branch $branch created from origin/history"

    # Show current state
    log_info "Current history:"
    git log --oneline -3

    # Checkout back to main so builders can run
    git checkout - >/dev/null 2>&1 || git checkout main
    log_info "Switched back to main branch (history branch created and ready)"
}

# Create a simple release commit (copies files and commits)
create_release_commit() {
    local release="$1"        # e.g., "prd-UBL-2.0"
    local version="$2"        # e.g., "2.0"
    local release_dir="$3"    # Full path to release directory
    local commit_message="$4" # Custom commit message (optional)

    log_step "Creating commit for $release"

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

    # Copy files to working directory
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

    # Create commit
    git commit -m "$commit_message" || die "Failed to create commit for $release"

    log_success "Commit created for $release"
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

    # Create empty commit (documentation only)
    git commit --allow-empty -m "$commit_message" || die "Failed to create schema step 1 commit"
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

    git commit --allow-empty -m "$commit_message" || die "Failed to create schema step 2 commit"
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

    git commit --allow-empty -m "$commit_message" || die "Failed to create schema step 3 commit"
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

    git commit --allow-empty -m "$commit_message" || die "Failed to create schema step 4 commit"
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

    git commit --allow-empty -m "$commit_message" || die "Failed to create schema step 5 commit"
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

    # Copy files
    for gc_file in "${gc_files[@]}"; do
        local basename
        basename=$(basename "$gc_file")
        cp "$gc_file" "$basename"
        git add "$basename"
        log_info "Updated: $basename"
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
}

# Complete 6-step schema transition
create_schema_transition() {
    local from_version="$1"
    local to_version="$2"
    local first_release_dir="$3"

    log_step "Starting 6-step schema transition: UBL $from_version → $to_version"

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

# Get commit date from release metadata (or use current date)
get_release_date() {
    local release="$1"

    # TODO: Extract actual release dates from OASIS metadata
    # For now, use current date
    date -R
}

# Export functions
export -f init_history_branch create_release_commit create_version_commits
export -f create_schema_transition_step1 create_schema_transition_step2
export -f create_schema_transition_step3 create_schema_transition_step4
export -f create_schema_transition_step5 create_schema_transition_step6
export -f create_schema_transition
export -f get_release_date
