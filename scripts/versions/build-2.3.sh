#!/bin/bash
# Build UBL 2.3 evolution (7 releases)
#
# UBL 2.3 includes both UBL-Entities and UBL-Signature-Entities files.
#
# Evolution:
#   csprd01 → csprd02 → csd03 → csd04 → cs01 → cs02 → os

set -euo pipefail

# Load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../lib/commit-helpers.sh"

# UBL 2.3 releases in chronological order
readonly UBL_2_3_RELEASES=(
    "csprd01-UBL-2.3"
    "csprd02-UBL-2.3"
    "csd03-UBL-2.3"
    "csd04-UBL-2.3"
    "cs01-UBL-2.3"
    "cs02-UBL-2.3"
    "os-UBL-2.3"
)

readonly VERSION="2.3"

# Main function
main() {
    # Switch to history branch for committing
    git checkout "$HISTORY_BRANCH" >/dev/null 2>&1 || die "Failed to checkout $HISTORY_BRANCH"

    log_step "Building UBL 2.3 Evolution"

    log_info "Version: UBL $VERSION"
    log_info "Releases: ${#UBL_2_3_RELEASES[@]}"
    log_info "Source: history/*-UBL-2.3/ (OASIS official releases)"
    log_info "Files: UBL-Entities + UBL-Signature-Entities"

    # Validate all release directories exist
    log_info "Validating release directories..."
    for release in "${UBL_2_3_RELEASES[@]}"; do
        local release_dir
        release_dir=$(get_release_dir "$release" ".")
        check_dir_exists "$release_dir"

        # Verify at least Entities file exists
        local entities_file="$release_dir/mod/UBL-Entities-${VERSION}.gc"
        check_file_exists "$entities_file"

        # Check if Signature-Entities exists
        local signature_file="$release_dir/mod/UBL-Signature-Entities-${VERSION}.gc"
        if [[ -f "$signature_file" ]]; then
            log_success "  ✓ $release (with Signature-Entities)"
        else
            log_success "  ✓ $release (Entities only)"
        fi
    done

    # Create commits for all releases
    log_step "Creating commits for UBL 2.3 releases"

    for release in "${UBL_2_3_RELEASES[@]}"; do
        local release_dir
        release_dir=$(get_release_dir "$release" ".")

        create_release_commit "$release" "$VERSION" "$release_dir"
    done

    log_success "UBL 2.3 evolution complete! (${#UBL_2_3_RELEASES[@]} commits created)"
}

# Run main function
main "$@"
