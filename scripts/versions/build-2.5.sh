#!/bin/bash
# Build UBL 2.5 evolution (2 releases)
#
# UBL 2.5 introduces UBL-Endorsed-Entities files in addition to the standard
# UBL-Entities and UBL-Signature-Entities files. Endorsed files are located
# in endorsed/mod/ subdirectory.
#
# Evolution:
#   csd01 → csd02

set -euo pipefail

# Load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../lib/commit-helpers.sh"

# UBL 2.5 releases in chronological order
readonly UBL_2_5_RELEASES=(
    "csd01-UBL-2.5"
    "csd02-UBL-2.5"
)

readonly VERSION="2.5"

# Main function
main() {
    log_step "Building UBL 2.5 Evolution"

    log_info "Version: UBL $VERSION"
    log_info "Releases: ${#UBL_2_5_RELEASES[@]}"
    log_info "Source: history/*-UBL-2.5/ (OASIS official releases)"
    log_info "Files: UBL-Entities + UBL-Signature-Entities + UBL-Endorsed-Entities (new!)"

    # Validate all release directories exist
    log_info "Validating release directories..."
    for release in "${UBL_2_5_RELEASES[@]}"; do
        local release_dir
        release_dir=$(get_release_dir "$release" ".")
        check_dir_exists "$release_dir"

        # Verify at least Entities file exists
        local entities_file="$release_dir/mod/UBL-Entities-${VERSION}.gc"
        check_file_exists "$entities_file"

        # Check if Signature-Entities exists
        local signature_file="$release_dir/mod/UBL-Signature-Entities-${VERSION}.gc"
        local has_signature=""
        if [[ -f "$signature_file" ]]; then
            has_signature=" + Signature-Entities"
        fi

        # Check if Endorsed-Entities exists
        local endorsed_file="$release_dir/endorsed/mod/UBL-Endorsed-Entities-${VERSION}.gc"
        local has_endorsed=""
        if [[ -f "$endorsed_file" ]]; then
            has_endorsed=" + Endorsed-Entities"
        fi

        log_success "  ✓ $release (Entities${has_signature}${has_endorsed})"
    done

    # Create commits for all releases
    log_step "Creating commits for UBL 2.5 releases"

    for release in "${UBL_2_5_RELEASES[@]}"; do
        local release_dir
        release_dir=$(get_release_dir "$release" ".")

        create_release_commit "$release" "$VERSION" "$release_dir"
    done

    log_success "UBL 2.5 evolution complete! (${#UBL_2_5_RELEASES[@]} commits created)"
}

# Run main function
main "$@"
