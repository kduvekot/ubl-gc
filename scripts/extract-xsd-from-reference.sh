#!/bin/bash
#
# Extract XSD files from ubl-release-package git history
#
# This script extracts XSD schema files from the kduvekot/ubl-release-package
# repository's git history and copies them to our history/ directories.
# We only need the xsd/common/ files (data type definitions), not all files.

set -e -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REFERENCE_REPO="/tmp/ubl-reference"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if reference repo exists
if [[ ! -d "$REFERENCE_REPO/.git" ]]; then
    echo "Error: Reference repository not found at $REFERENCE_REPO"
    echo "Please clone it first:"
    echo "  cd /tmp && git clone https://github.com/kduvekot/ubl-release-package.git ubl-reference"
    exit 1
fi

# Mapping of commit hash -> our directory name
# Format: "commit_hash|stage|version|our_dir_name"
# NOTE: UBL 2.0 releases don't have XSD files (only .ods source files)
declare -a RELEASE_MAP=(
    # UBL 2.1 (8 releases)
    "05e930f15fec1817434c1d6fe26087fc40f34ca5|prd1|2.1|prd1-UBL-2.1"
    "abb10bfeab1820f74a81dd5dbd69ecf29390fbda|prd2|2.1|prd2-UBL-2.1"
    "cf626a997c5b374777fe1e993b98efea54e1eef4|prd3|2.1|prd3-UBL-2.1"
    "d6bae4f2a964afda667771d7e47d168c3f443817|prd4|2.1|prd4-UBL-2.1"
    "abcad32b7543608f23794206ad6b9de9497aeb04|csd4|2.1|csd4-UBL-2.1"
    "42ce55a422e259db58b9c98cb2f4db76787e29e1|cs1|2.1|cs1-UBL-2.1"
    "bddd3cf272b1267058a22d40ec8983fef7aed43e|cos1|2.1|cos1-UBL-2.1"
    "69d9f20189fe7fa551dcc59f17d8480e70cda970|os|2.1|os-UBL-2.1"

    # UBL 2.2 (6 releases)
    "0d0570de65e07dca295755ddd44de39ae5c7a916|csprd01|2.2|csprd01-UBL-2.2"
    "c020d41dc4c928451cb783d38f64e69ac9c3b9cd|csprd02|2.2|csprd02-UBL-2.2"
    "0444edd7e3a2ec7123763dd021f9165fefa84de3|csprd03|2.2|csprd03-UBL-2.2"
    "4357854bb72c2fd7eba8a42b29e4b8889b157eb0|cs01|2.2|cs01-UBL-2.2"
    "fa6a949c4ec94a21f372fe7444f0ea98bb74976f|cos01|2.2|cos01-UBL-2.2"
    "de9dc72dbff019516c78c5bc43cb3f742bd289c5|os|2.2|os-UBL-2.2"

    # UBL 2.3 (7 releases)
    "b85ae89f859046e1635c97020e1135c69c29919f|csprd02|2.3|csprd02-UBL-2.3"
    "8d5943cc9a5d43ddcbd259c23d407966d8085967|csprd01|2.3|csprd01-UBL-2.3"
    "254a4cfc8a04241a0394c000d66fa21424ef1ca5|csd03|2.3|csd03-UBL-2.3"
    "072db7d20a46c06a59d1f542f5381fc5b533dec5|csd04|2.3|csd04-UBL-2.3"
    "6ab1c948dd849829cfed933632cf0d955d36197e|cs01|2.3|cs01-UBL-2.3"
    "aa130e83db39f0ab07f2e0c8d1c94f92765cb6ee|cs02|2.3|cs02-UBL-2.3"
    "6d2a358b72ab311c49b88a851e5674f850cbb399|os|2.3|os-UBL-2.3"

    # UBL 2.4 (4 releases)
    "995fa52ff24529686a469f9ad5f56555c16e4039|csd01|2.4|csd01-UBL-2.4"
    "3831bb90dca59771e0083213b2ab56324d31309f|csd02|2.4|csd02-UBL-2.4"
    "d59634502c46a73c9e1f97caeee2dc71b499eb76|cs01|2.4|cs01-UBL-2.4"
    "c5835668592940c503cc235d8b39414cbd1f93e3|os|2.4|os-UBL-2.4"

    # UBL 2.5 (1 release - missing csd02)
    "83a9d5a47967863723340c84917b36e8fac2b5a7|csd01|2.5|csd01-UBL-2.5"
)

echo -e "${BLUE}Extracting XSD files from ubl-release-package commits...${NC}"
echo

cd "$REFERENCE_REPO"

extracted_count=0
skipped_count=0

for entry in "${RELEASE_MAP[@]}"; do
    IFS='|' read -r commit stage version dir_name <<< "$entry"

    target_dir="$REPO_ROOT/history/$dir_name/xsd/common"

    # Check if we already have XSD files (skip if we do)
    if [[ -d "$target_dir" ]]; then
        xsd_count=$(find "$target_dir" -name "*.xsd" 2>/dev/null | wc -l)
        if [[ "$xsd_count" -gt 0 ]]; then
            echo -e "${YELLOW}⊘${NC} $dir_name (XSD already present)"
            skipped_count=$((skipped_count + 1))
            continue
        fi
    fi

    echo -e "${BLUE}→${NC} Extracting XSD from $dir_name..."

    # Create target directory
    mkdir -p "$target_dir"

    # Get list of XSD files in xsd/common/ at this commit
    xsd_files=$(git ls-tree -r --name-only "$commit" xsd/common/ 2>/dev/null | grep '\.xsd$' || true)

    if [[ -z "$xsd_files" ]]; then
        echo -e "  ${YELLOW}⚠${NC}  No XSD files found in commit $commit"
        continue
    fi

    # Extract each XSD file
    file_count=0
    while IFS= read -r xsd_path; do
        filename=$(basename "$xsd_path")
        git show "$commit:$xsd_path" > "$target_dir/$filename" 2>/dev/null || {
            echo -e "  ${YELLOW}⚠${NC}  Failed to extract: $filename"
            continue
        }
        file_count=$((file_count + 1))
    done <<< "$xsd_files"

    echo -e "  ${GREEN}✓${NC} Extracted $file_count XSD files"
    extracted_count=$((extracted_count + 1))
done

echo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Extraction complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo "  Extracted: $extracted_count releases"
echo "  Skipped:   $skipped_count releases (already present)"
echo

# Verify what we extracted
echo -e "${BLUE}Verification:${NC}"
for version in 2.0 2.1 2.2 2.3 2.4 2.5; do
    count=$(find "$REPO_ROOT/history" -path "*/UBL-$version/xsd/common/*.xsd" 2>/dev/null | wc -l)
    releases=$(find "$REPO_ROOT/history" -path "*-UBL-$version/xsd" -type d 2>/dev/null | wc -l)
    echo "  UBL $version: $releases releases, $count XSD files"
done

echo
echo -e "${GREEN}Done!${NC} XSD files are ready in history/*/xsd/common/"
