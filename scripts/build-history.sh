#!/bin/bash
# Master orchestrator for building complete UBL history branch
#
# This script initializes the git history branch and calls each version builder
# in sequence to create the complete evolution of UBL GenericCode semantic models
# from UBL 2.0 (2006) through UBL 2.5 (2025).
#
# Usage:
#   ./scripts/build-history.sh
#
# The script will:
#   1. Validate repository structure
#   2. Initialize history branch (claude/history-bunUn)
#   3. Run UBL 2.0 builder (8 commits)
#   4. Run UBL 2.1 builder (8 commits)
#   5. Run UBL 2.2 builder (6 commits)
#   6. Run UBL 2.3 builder (7 commits)
#   7. Run UBL 2.4 builder (4 commits)
#   8. Run UBL 2.5 builder (2 commits)
#   Result: 35 commits total across all versions

set -euo pipefail

# Load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
source "$SCRIPT_DIR/lib/commit-helpers.sh"

# Version builders
readonly BUILDERS=(
    "scripts/versions/build-2.0.sh"
    "scripts/versions/build-2.1.sh"
    "scripts/versions/build-2.2.sh"
    "scripts/versions/build-2.3.sh"
    "scripts/versions/build-2.4.sh"
    "scripts/versions/build-2.5.sh"
)

# Main function
main() {
    log_step "UBL History Branch Builder"
    log_info "Building complete evolution from UBL 2.0 through UBL 2.5"

    # Validate repository structure
    validate_repo_structure

    # Check we're on main branch
    log_info "Checking git state..."
    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$current_branch" != "main" ]]; then
        die "Must be on 'main' branch to build history, currently on: $current_branch"
    fi

    # Initialize the history branch in /tmp
    init_history_branch "$HISTORY_BRANCH"

    # Clean up temp directory on exit
    trap "rm -rf '$HISTORY_WORK_DIR'" EXIT

    # Run each version builder in sequence
    log_step "Building version-specific evolution"
    log_info "Total builders: ${#BUILDERS[@]}"

    local builder_count=0
    for builder in "${BUILDERS[@]}"; do
        ((builder_count++))

        log_step "Builder $builder_count/${#BUILDERS[@]}: $builder"

        # Run the builder from main repo
        local builder_path="$REPO_ROOT/$builder"
        if ! bash "$builder_path"; then
            die "Builder failed: $builder"
        fi
    done

    # Push history branch back to main repo
    log_step "Pushing history branch to main repo"
    cd "$HISTORY_WORK_DIR"
    git push "$REPO_ROOT" "$HISTORY_BRANCH:$HISTORY_BRANCH" || die "Failed to push history branch"
    cd "$REPO_ROOT"

    # Final summary
    log_step "History Branch Build Complete"

    log_info "Summary:"
    log_info "  Branch: $HISTORY_BRANCH"
    log_info "  Total commits created: 35 (8+8+6+7+4+2)"
    log_info "  Versions: UBL 2.0 through UBL 2.5"

    log_info "View the history:"
    log_info "  git log --oneline --graph"
    log_info "  git log --oneline $HISTORY_BRANCH"

    log_info "Switch to history branch:"
    log_info "  git checkout $HISTORY_BRANCH"

    log_success "All done! History branch is ready."
}

# Run main function
main "$@"
