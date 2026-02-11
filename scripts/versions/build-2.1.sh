#!/bin/bash
# Build UBL 2.1 evolution (8 releases)
#
# UBL 2.1 includes both UBL-Entities and UBL-Signature-Entities files.
# Note: prd1 and prd2 do not have Signature-Entities files.
#
# Evolution:
#   prd1 → prd2 → prd3 → prd4 → csd4 → cs1 → cos1 → os

set -euo pipefail

# Load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../lib/commit-helpers.sh"

# UBL 2.1 releases in chronological order
readonly UBL_2_1_RELEASES=(
    "prd1-UBL-2.1"
    "prd2-UBL-2.1"
    "prd3-UBL-2.1"
    "prd4-UBL-2.1"
    "csd4-UBL-2.1"
    "cs1-UBL-2.1"
    "cos1-UBL-2.1"
    "os-UBL-2.1"
)

readonly VERSION="2.1"

# Main function
main() {

    log_step "Building UBL 2.1 Evolution"

    log_info "Version: UBL $VERSION"
    log_info "Releases: ${#UBL_2_1_RELEASES[@]}"
    log_info "Source: history/*-UBL-2.1/ (OASIS official releases)"
    log_info "Files: UBL-Entities + UBL-Signature-Entities (where available)"

    # Validate all release directories exist
    log_info "Validating release directories..."
    for release in "${UBL_2_1_RELEASES[@]}"; do
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
    log_step "Creating commits for UBL 2.1 releases"

    for release in "${UBL_2_1_RELEASES[@]}"; do
        local release_dir
        release_dir=$(get_release_dir "$release" ".")

        create_release_commit "$release" "$VERSION" "$release_dir"
    done

    log_success "UBL 2.1 evolution complete! (${#UBL_2_1_RELEASES[@]} commits created)"
}

# Run main function
main "$@"
