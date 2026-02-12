#!/bin/bash
#
# Download complete OASIS UBL distributions for all 35 releases
#
# This script downloads the full ZIP distributions from OASIS for all
# UBL releases (2.0-2.5), extracting XSD schemas, code lists, examples,
# and all other artifacts to preserve the complete historical record.
#
# Usage: ./scripts/download-oasis-distributions.sh [options]
#
# Options:
#   --version VERSION   Download only specific version (2.0, 2.1, etc.)
#   --release RELEASE   Download only specific release (prd-UBL-2.0, etc.)
#   --dry-run          Show what would be downloaded without downloading
#   --skip-existing    Skip releases that already have xsd/ directory
#   --verify-only      Only verify existing downloads
#
# Directory structure created:
#   history/{release}/
#   ├─ mod/      ← GenericCode files (already present)
#   ├─ xsd/      ← XML Schema files (NEW)
#   ├─ cl/       ← Code lists (NEW)
#   ├─ val/      ← Validation resources (NEW)
#   └─ ...       ← All other OASIS distribution contents
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
HISTORY_DIR="${REPO_ROOT}/history"
TEMP_DIR="${REPO_ROOT}/.temp/downloads"

# Options
DRY_RUN=false
SKIP_EXISTING=false
VERIFY_ONLY=false
FILTER_VERSION=""
FILTER_RELEASE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            FILTER_VERSION="$2"
            shift 2
            ;;
        --release)
            FILTER_RELEASE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-existing)
            SKIP_EXISTING=true
            shift
            ;;
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        --help)
            grep '^#' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create temp directory
mkdir -p "$TEMP_DIR"

# OASIS base URL
OASIS_BASE="https://docs.oasis-open.org/ubl"

# All 35 releases
declare -a RELEASES=(
    # UBL 2.0 (8 releases)
    "prd-UBL-2.0"
    "prd2-UBL-2.0"
    "prd3-UBL-2.0"
    "prd3r1-UBL-2.0"
    "cs-UBL-2.0"
    "os-UBL-2.0"
    "os-update-UBL-2.0"
    "errata-UBL-2.0"

    # UBL 2.1 (8 releases)
    "prd1-UBL-2.1"
    "prd2-UBL-2.1"
    "prd3-UBL-2.1"
    "prd4-UBL-2.1"
    "csd4-UBL-2.1"
    "cs1-UBL-2.1"
    "cos1-UBL-2.1"
    "os-UBL-2.1"

    # UBL 2.2 (6 releases)
    "csprd01-UBL-2.2"
    "csprd02-UBL-2.2"
    "csprd03-UBL-2.2"
    "cs01-UBL-2.2"
    "cos01-UBL-2.2"
    "os-UBL-2.2"

    # UBL 2.3 (7 releases)
    "csprd01-UBL-2.3"
    "csprd02-UBL-2.3"
    "csd03-UBL-2.3"
    "csd04-UBL-2.3"
    "cs01-UBL-2.3"
    "cs02-UBL-2.3"
    "os-UBL-2.3"

    # UBL 2.4 (4 releases)
    "csd01-UBL-2.4"
    "csd02-UBL-2.4"
    "cs01-UBL-2.4"
    "os-UBL-2.4"

    # UBL 2.5 (2 releases)
    "csd01-UBL-2.5"
    "csd02-UBL-2.5"
)

# Extract version from release name (e.g., "prd-UBL-2.0" -> "2.0")
get_version() {
    local release="$1"
    echo "$release" | grep -oP 'UBL-\K[0-9.]+$'
}

# Get ZIP filename for a release
get_zip_filename() {
    local release="$1"
    local version
    version=$(get_version "$release")
    echo "UBL-${version}.zip"
}

# Download a single release
download_release() {
    local release="$1"
    local version
    local zip_name
    local url
    local target_dir
    local zip_path

    version=$(get_version "$release")
    zip_name=$(get_zip_filename "$release")
    url="${OASIS_BASE}/${release}/${zip_name}"

    # Determine target directory
    if [[ "$release" =~ ^(prd|prd2|prd3|prd3r1|cs|os|os-update|errata)-UBL-2\.0$ ]]; then
        target_dir="${HISTORY_DIR}/generated/${release}"
    else
        target_dir="${HISTORY_DIR}/${release}"
    fi

    zip_path="${TEMP_DIR}/${release}.zip"

    # Check if should skip
    if [[ "$SKIP_EXISTING" == "true" ]] && [[ -d "${target_dir}/xsd" ]]; then
        echo -e "${YELLOW}⊘${NC} Skipping ${release} (already has xsd/)"
        return 0
    fi

    # Dry run
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}[DRY RUN]${NC} ${release}"
        echo -e "  ${BLUE}→${NC} URL: $url"
        echo -e "  ${BLUE}↳${NC} Target: $target_dir"
        return 0
    fi

    # Verify only mode
    if [[ "$VERIFY_ONLY" == "true" ]]; then
        if [[ -d "${target_dir}/xsd" ]]; then
            local xsd_count
            xsd_count=$(find "${target_dir}/xsd" -name "*.xsd" 2>/dev/null | wc -l)
            echo -e "${GREEN}✓${NC} ${release}: ${xsd_count} XSD files"
        else
            echo -e "${RED}✗${NC} ${release}: Missing xsd/ directory"
        fi
        return 0
    fi

    echo -e "${BLUE}↓${NC} Downloading ${release}..."

    # Download ZIP
    if ! curl -fsSL -o "$zip_path" "$url"; then
        echo -e "${RED}✗${NC} Failed to download: $url"
        return 1
    fi

    # Create target directory
    mkdir -p "$target_dir"

    # Extract ZIP
    echo -e "${BLUE}↓${NC} Extracting to ${target_dir}..."

    # UBL ZIPs typically have a top-level directory like "UBL-2.4/"
    # We want to extract the contents directly into our target directory
    local temp_extract="${TEMP_DIR}/extract_${release}"
    mkdir -p "$temp_extract"

    if ! unzip -q "$zip_path" -d "$temp_extract"; then
        echo -e "${RED}✗${NC} Failed to extract: $zip_path"
        rm -rf "$temp_extract"
        return 1
    fi

    # Find the actual content directory (usually "UBL-{version}/")
    local content_dir
    content_dir=$(find "$temp_extract" -maxdepth 1 -type d -name "UBL-*" | head -1)

    if [[ -z "$content_dir" ]]; then
        echo -e "${RED}✗${NC} Could not find content directory in ZIP"
        rm -rf "$temp_extract"
        return 1
    fi

    # Copy all directories EXCEPT mod/ (we already have our generated/downloaded .gc files)
    for dir in "$content_dir"/*; do
        local dirname
        dirname=$(basename "$dir")

        if [[ "$dirname" == "mod" ]]; then
            # Skip mod/ directory to preserve our existing .gc files
            echo -e "${YELLOW}⊘${NC} Skipping mod/ (preserving existing GenericCode files)"
            continue
        fi

        if [[ -d "$dir" ]]; then
            echo -e "${BLUE}→${NC} Copying ${dirname}/"
            cp -r "$dir" "$target_dir/"
        elif [[ -f "$dir" ]]; then
            echo -e "${BLUE}→${NC} Copying ${dirname}"
            cp "$dir" "$target_dir/"
        fi
    done

    # Count what we got
    local xsd_count=0
    local cl_count=0

    if [[ -d "${target_dir}/xsd" ]]; then
        xsd_count=$(find "${target_dir}/xsd" -name "*.xsd" 2>/dev/null | wc -l)
    fi

    if [[ -d "${target_dir}/cl" ]]; then
        cl_count=$(find "${target_dir}/cl" -name "*.gc" 2>/dev/null | wc -l)
    fi

    echo -e "${GREEN}✓${NC} ${release}: ${xsd_count} XSD files, ${cl_count} code lists"

    # Cleanup
    rm -rf "$temp_extract"
    rm -f "$zip_path"

    return 0
}

# Main execution
main() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} OASIS UBL Distribution Downloader                         ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}⚠${NC}  DRY RUN MODE - No files will be downloaded"
        echo ""
    fi

    if [[ "$VERIFY_ONLY" == "true" ]]; then
        echo -e "${BLUE}ℹ${NC}  VERIFY MODE - Checking existing downloads"
        echo ""
    fi

    local total=0
    local success=0
    local skipped=0
    local failed=0

    echo -e "${BLUE}Processing ${#RELEASES[@]} releases...${NC}"
    echo ""

    for release in "${RELEASES[@]}"; do
        # Apply filters
        if [[ -n "$FILTER_VERSION" ]]; then
            local version
            version=$(get_version "$release")
            if [[ "$version" != "$FILTER_VERSION" ]]; then
                continue
            fi
        fi

        if [[ -n "$FILTER_RELEASE" ]]; then
            if [[ "$release" != "$FILTER_RELEASE" ]]; then
                continue
            fi
        fi

        total=$((total + 1))

        if download_release "$release"; then
            success=$((success + 1))
        else
            failed=$((failed + 1))
            echo -e "${RED}✗${NC} Failed: $release"
        fi

        # Small delay to be nice to OASIS servers
        if [[ "$DRY_RUN" == "false" ]] && [[ "$VERIFY_ONLY" == "false" ]]; then
            sleep 1
        fi
    done

    # Summary
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Summary:${NC}"
    echo -e "  Total releases processed: ${total}"
    echo -e "  ${GREEN}✓${NC} Successful: ${success}"
    if [[ $skipped -gt 0 ]]; then
        echo -e "  ${YELLOW}⊘${NC} Skipped: ${skipped}"
    fi
    if [[ $failed -gt 0 ]]; then
        echo -e "  ${RED}✗${NC} Failed: ${failed}"
    fi
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

    # Cleanup temp directory if empty
    if [[ -d "$TEMP_DIR" ]] && [[ -z "$(ls -A "$TEMP_DIR")" ]]; then
        rmdir "$TEMP_DIR"
        rmdir "$(dirname "$TEMP_DIR")" 2>/dev/null || true
    fi

    if [[ $failed -gt 0 ]]; then
        exit 1
    fi
}

# Run
main
