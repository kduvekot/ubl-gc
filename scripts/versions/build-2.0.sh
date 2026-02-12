#!/bin/bash
# Build UBL 2.0 evolution (8 releases from generated GenericCode files)
#
# UBL 2.0 was originally released as .ods files (OpenDocument Spreadsheet).
# GenericCode files were generated using Crane-ods2obdgc XSLT tool.
# All generated files are in history/generated/*-UBL-2.0/
#
# Evolution:
#   prd → prd2 → prd3 → prd3r1 → cs → os → os-update → errata

set -euo pipefail

# Load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"
source "$SCRIPT_DIR/../lib/commit-helpers.sh"

# UBL 2.0 releases in chronological order
readonly UBL_2_0_RELEASES=(
    "prd-UBL-2.0"
    "prd2-UBL-2.0"
    "prd3-UBL-2.0"
    "prd3r1-UBL-2.0"
    "cs-UBL-2.0"
    "os-UBL-2.0"
    "os-update-UBL-2.0"
    "errata-UBL-2.0"
)

readonly VERSION="2.0"

# Main function
main() {

    log_step "Building UBL 2.0 Evolution"

    log_info "Version: UBL $VERSION"
    log_info "Releases: ${#UBL_2_0_RELEASES[@]}"
    log_info "Source: history/generated/ (GenericCode synthesized from .ods files)"

    # Validate all release directories exist
    log_info "Validating release directories..."
    for release in "${UBL_2_0_RELEASES[@]}"; do
        local release_dir
        release_dir=$(get_release_dir "$release" "generated")
        check_dir_exists "$release_dir"

        # Verify GenericCode file exists
        local gc_file="$release_dir/mod/UBL-Entities-${VERSION}.gc"
        check_file_exists "$gc_file"

        log_success "  ✓ $release"
    done

    # Create commits for all releases
    log_step "Creating commits for UBL 2.0 releases"

    for release in "${UBL_2_0_RELEASES[@]}"; do
        local release_dir
        release_dir=$(get_release_dir "$release" "generated")

        # Create custom commit message for UBL 2.0 (mention it's generated)
        local stage_name
        stage_name=$(get_stage_name "$release")
        local stage_desc
        stage_desc=$(get_stage_description "$stage_name")

        local gc_file="$release_dir/mod/UBL-Entities-${VERSION}.gc"
        local row_count
        row_count=$(count_gc_rows "$gc_file")

        local commit_message="UBL $VERSION - $stage_name ($stage_desc)

Release: $release
File: UBL-Entities-$VERSION.gc ($row_count rows)

Note: UBL 2.0 was originally released as .ods (OpenDocument Spreadsheet)
files. This GenericCode representation was synthesized using the official
OASIS Crane-ods2obdgc XSLT tool to enable git-based version tracking.

Source: history/generated/$release/ (generated from OASIS .ods files)
Tool: Crane-ods2obdgc + Saxon 9 HE

$SESSION_URL"

        create_release_commit "$release" "$VERSION" "$release_dir" "$commit_message"
    done

    log_success "UBL 2.0 evolution complete! (${#UBL_2_0_RELEASES[@]} commits created)"
}

# Run main function
main "$@"
