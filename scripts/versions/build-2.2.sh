#!/bin/bash
# Build UBL 2.2 evolution (6 releases)
#
# UBL 2.2 includes both UBL-Entities and UBL-Signature-Entities files.
#
# Evolution:
#   csprd01 → csprd02 → csprd03 → cs01 → cos01 → os

set -euo pipefail

# Load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../lib/commit-helpers.sh"

# UBL 2.2 releases in chronological order
readonly UBL_2_2_RELEASES=(
    "csprd01-UBL-2.2"
    "csprd02-UBL-2.2"
    "csprd03-UBL-2.2"
    "cs01-UBL-2.2"
    "cos01-UBL-2.2"
    "os-UBL-2.2"
)

readonly VERSION="2.2"

# Main function
main() {
    log_step "Building UBL 2.2 Evolution"

    log_info "Version: UBL $VERSION"
    log_info "Releases: ${#UBL_2_2_RELEASES[@]}"
    log_info "Source: history/*-UBL-2.2/ (OASIS official releases)"
    log_info "Files: UBL-Entities + UBL-Signature-Entities"

    # Validate all release directories exist
    log_info "Validating release directories..."
    for release in "${UBL_2_2_RELEASES[@]}"; do
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

    # SCHEMA TRANSITION: UBL 2.1 → 2.2 (6-step process)
    log_step "Schema Transition: UBL 2.1 → 2.2"
    log_info "This is a major version transition requiring 6-step commit process"

    local first_release_dir
    first_release_dir=$(get_release_dir "${UBL_2_2_RELEASES[0]}" ".")

    create_schema_transition "2.1" "$VERSION" "$first_release_dir"

    # Create commits for remaining releases (first release already done in step 6)
    log_step "Creating commits for remaining UBL 2.2 releases"

    for release in "${UBL_2_2_RELEASES[@]:1}"; do
        local release_dir
        release_dir=$(get_release_dir "$release" ".")

        create_release_commit "$release" "$VERSION" "$release_dir"
    done

    log_success "UBL 2.2 evolution complete! (6 schema transition + ${#UBL_2_2_RELEASES[@]} release commits)"
}

# Run main function
main "$@"
