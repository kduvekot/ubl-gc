#!/bin/bash
# Common functions for UBL history building scripts
# Source this file in other scripts: source "$(dirname "$0")/../lib/common.sh"

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Repository root (calculated from script location)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly REPO_ROOT

# History directory
readonly HISTORY_DIR="$REPO_ROOT/history"

# Session ID for branch naming (extracted from commit messages or environment)
readonly SESSION_SUFFIX="bunUn"

# History branch name (output branch)
readonly HISTORY_BRANCH="claude/history-${SESSION_SUFFIX}"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_step() {
    echo -e "\n${BLUE}===${NC} $* ${BLUE}===${NC}\n" >&2
}

# Exit with error
die() {
    log_error "$@"
    exit 1
}

# Check if file exists
check_file_exists() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        die "Required file not found: $file"
    fi
}

# Check if directory exists
check_dir_exists() {
    local dir="$1"
    if [[ ! -d "$dir" ]]; then
        die "Required directory not found: $dir"
    fi
}

# Validate repository structure
validate_repo_structure() {
    log_info "Validating repository structure..."

    check_dir_exists "$HISTORY_DIR"
    check_dir_exists "$HISTORY_DIR/tools"
    check_dir_exists "$HISTORY_DIR/generated"

    log_success "Repository structure validated"
}

# Get full path to a release directory
get_release_dir() {
    local release="$1"  # e.g., "prd-UBL-2.0" or "prd1-UBL-2.1"
    local base_dir="$2" # "generated" or "."

    if [[ "$base_dir" == "generated" ]]; then
        echo "$HISTORY_DIR/generated/$release"
    else
        echo "$HISTORY_DIR/$release"
    fi
}

# Get the GenericCode files for a release
get_gc_files() {
    local release_dir="$1"
    local version="$2"  # e.g., "2.0", "2.1"

    local entities_file="$release_dir/mod/UBL-Entities-${version}.gc"
    local signature_file="$release_dir/mod/UBL-Signature-Entities-${version}.gc"
    local endorsed_file="$release_dir/endorsed/mod/UBL-Endorsed-Entities-${version}.gc"

    # Return files that exist
    local files=()
    [[ -f "$entities_file" ]] && files+=("$entities_file")
    [[ -f "$signature_file" ]] && files+=("$signature_file")
    [[ -f "$endorsed_file" ]] && files+=("$endorsed_file")

    printf '%s\n' "${files[@]}"
}

# Count rows in a GenericCode file
count_gc_rows() {
    local gc_file="$1"
    grep -c '<Row>' "$gc_file" 2>/dev/null || echo "0"
}

# Get file size in human-readable format
get_file_size() {
    local file="$1"
    du -h "$file" | cut -f1
}

# Verify GenericCode file is valid XML
verify_gc_file() {
    local gc_file="$1"

    # Check file exists
    if [[ ! -f "$gc_file" ]]; then
        log_error "File not found: $gc_file"
        return 1
    fi

    # Check XML is well-formed (ends with </gc:CodeList>)
    if ! tail -1 "$gc_file" | grep -q '</gc:CodeList>'; then
        log_error "File appears incomplete (missing closing tag): $gc_file"
        return 1
    fi

    # Check has content (at least one Row)
    local row_count
    row_count=$(count_gc_rows "$gc_file")
    if [[ "$row_count" -eq 0 ]]; then
        log_error "File has no rows: $gc_file"
        return 1
    fi

    log_success "Valid GenericCode file: $(basename "$gc_file") ($row_count rows, $(get_file_size "$gc_file"))"
    return 0
}

# Extract version from filename (e.g., "UBL-Entities-2.1.gc" -> "2.1")
extract_version_from_filename() {
    local filename="$1"
    echo "$filename" | grep -oP 'UBL-.*-\K[0-9]+\.[0-9]+' | head -1
}

# Get release stage name (e.g., "prd1-UBL-2.1" -> "PRD1")
get_stage_name() {
    local release="$1"
    echo "$release" | sed 's/-UBL-.*$//' | tr '[:lower:]' '[:upper:]'
}

# Get full stage description
get_stage_description() {
    local stage="$1"  # e.g., "prd", "csd01", "os"

    case "${stage,,}" in
        prd*)  echo "Proposed Recommendation Draft" ;;
        csd*)  echo "Committee Specification Draft" ;;
        csprd*) echo "Committee Specification Proposed Recommendation Draft" ;;
        cs*)   echo "Committee Specification" ;;
        cos*)  echo "Candidate OASIS Standard" ;;
        os*)   echo "Official Standard" ;;
        errata) echo "Errata Release" ;;
        *)     echo "Release Stage" ;;
    esac
}

# Print summary of release
print_release_summary() {
    local release="$1"
    local release_dir="$2"
    local version="$3"

    log_step "Release: $release"
    log_info "Directory: $release_dir"
    log_info "Version: $version"
    log_info "Stage: $(get_stage_name "$release") - $(get_stage_description "$(get_stage_name "$release")")"

    # List GenericCode files
    local gc_files
    mapfile -t gc_files < <(get_gc_files "$release_dir" "$version")

    if [[ ${#gc_files[@]} -eq 0 ]]; then
        log_warning "No GenericCode files found"
        return 1
    fi

    log_info "GenericCode files:"
    for gc_file in "${gc_files[@]}"; do
        local basename
        basename=$(basename "$gc_file")
        local row_count
        row_count=$(count_gc_rows "$gc_file")
        local size
        size=$(get_file_size "$gc_file")
        echo "  - $basename ($row_count rows, $size)"
    done

    return 0
}

# Export functions
export -f log_info log_success log_warning log_error log_step die
export -f check_file_exists check_dir_exists validate_repo_structure
export -f get_release_dir get_gc_files count_gc_rows get_file_size
export -f verify_gc_file extract_version_from_filename
export -f get_stage_name get_stage_description print_release_summary
