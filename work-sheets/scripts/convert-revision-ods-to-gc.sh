#!/bin/bash
#
# Convert Google Sheets revision ODS exports to GenericCode (.gc)
# using the existing Crane-ods2obdgc XSLT + Saxon tools (unmodified).
#
# For each workflow version (V1-V10), combines the matching library +
# documents revision ODS files into a single UBL-Entities-2.5.gc,
# exactly as the official UBL build does.
#
# Usage:
#   ./work-sheets/scripts/convert-revision-ods-to-gc.sh
#
# Prerequisites:
#   - Java (for Saxon)
#   - ODS files in work-sheets/revision-ods/
#
# Output:
#   work-sheets/gc-from-revisions/{version}/UBL-Entities-2.5.gc

set -e

# Paths (relative to repo root)
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOLS_DIR="$REPO_DIR/history/tools"
SAXON_JAR="$TOOLS_DIR/saxon9he/saxon9he.jar"
XSLT_STYLESHEET="$TOOLS_DIR/Crane-ods2obdgc/Crane-ods2obdgc.xsl"

ODS_DIR="$REPO_DIR/work-sheets/revision-ods"
OUTPUT_BASE="$REPO_DIR/work-sheets/gc-from-revisions"

# Check tools
if [ ! -f "$SAXON_JAR" ]; then
  echo "ERROR: Saxon not found at $SAXON_JAR"
  exit 1
fi
if [ ! -f "$XSLT_STYLESHEET" ]; then
  echo "ERROR: Crane-ods2obdgc.xsl not found at $XSLT_STYLESHEET"
  exit 1
fi

echo "=== Convert Revision ODS → GenericCode ==="
echo ""
echo "Tools (unmodified):"
echo "  Saxon: $SAXON_JAR"
echo "  XSLT:  $XSLT_STYLESHEET"
echo ""

# Revision-to-workflow mapping
# Each version maps to a (library_rev, documents_rev) pair
# These are the last revision saved BEFORE the workflow ran
declare -a VERSIONS=( "V1" "V2" "V3" "V4" "V5" "V6" "V7" "V8" "V9" "V10" )
declare -A LIB_REV=(
  [V1]=1843  [V2]=1843  [V3]=1868  [V4]=1868  [V5]=1999
  [V6]=1999  [V7]=2005  [V8]=2005  [V9]=2005  [V10]=2005
)
declare -A DOC_REV=(
  [V1]=1793  [V2]=1793  [V3]=1803  [V4]=1983  [V5]=2190
  [V6]=2190  [V7]=2190  [V8]=2200  [V9]=2204  [V10]=2204
)

# Deduplicate: some versions share the same (lib,doc) pair
declare -A DONE_COMBOS

TOTAL_OK=0
TOTAL_SKIP=0

for ver in "${VERSIONS[@]}"; do
  lib_rev="${LIB_REV[$ver]}"
  doc_rev="${DOC_REV[$ver]}"
  combo="${lib_rev}_${doc_rev}"

  lib_ods="$ODS_DIR/ubl25_library/rev-${lib_rev}.ods"
  doc_ods="$ODS_DIR/ubl25_documents/rev-${doc_rev}.ods"
  out_dir="$OUTPUT_BASE/$ver"
  out_file="$out_dir/UBL-Entities-2.5.gc"

  echo "--- $ver (library=rev-${lib_rev}, documents=rev-${doc_rev}) ---"

  # Skip if output already exists
  if [ -f "$out_file" ]; then
    rows=$(grep -c '<Row>' "$out_file" 2>/dev/null || echo "?")
    echo "  [skip] already exists ($rows rows)"
    TOTAL_SKIP=$((TOTAL_SKIP + 1))
    echo ""
    continue
  fi

  # If same combo already converted, symlink
  if [ -n "${DONE_COMBOS[$combo]}" ]; then
    src_ver="${DONE_COMBOS[$combo]}"
    src_file="$OUTPUT_BASE/$src_ver/UBL-Entities-2.5.gc"
    mkdir -p "$out_dir"
    cp "$src_file" "$out_file"
    rows=$(grep -c '<Row>' "$out_file" 2>/dev/null || echo "?")
    echo "  [copy from $src_ver] same revision pair ($rows rows)"
    TOTAL_OK=$((TOTAL_OK + 1))
    echo ""
    continue
  fi

  # Check ODS files exist
  if [ ! -f "$lib_ods" ]; then
    echo "  ERROR: library ODS not found: $lib_ods"
    continue
  fi
  if [ ! -f "$doc_ods" ]; then
    echo "  ERROR: documents ODS not found: $doc_ods"
    continue
  fi

  # Create temp dir
  TMPDIR=$(mktemp -d)
  trap "rm -rf $TMPDIR" EXIT

  # Copy ODS files to temp (Crane needs local paths)
  cp "$lib_ods" "$TMPDIR/library.ods"
  cp "$doc_ods" "$TMPDIR/documents.ods"

  # Create identification file (uses actual Google Sheets revision IDs for traceability)
  cat > "$TMPDIR/ident.xml" << IDENT
<?xml version="1.0" encoding="UTF-8"?>
<Identification>
  <ShortName>UBL-2.5-${ver}-lib${lib_rev}-doc${doc_rev}</ShortName>
  <LongName>UBL 2.5 ${ver} Business Entity Summary (Google Sheets library rev-${lib_rev} + documents rev-${doc_rev})</LongName>
  <Version>2.5</Version>
  <CanonicalUri>urn:oasis:names:specification:ubl:BIE</CanonicalUri>
  <CanonicalVersionUri>urn:oasis:names:specification:ubl:BIE:2.5</CanonicalVersionUri>
</Identification>
IDENT

  # Build ODS comma-separated list
  ODS_LIST="$TMPDIR/library.ods,$TMPDIR/documents.ods"

  # Run conversion
  mkdir -p "$out_dir"
  echo "  Converting..."

  if java -jar "$SAXON_JAR" \
    -xsl:"$XSLT_STYLESHEET" \
    -o:"$out_file" \
    -it:ods-uri \
    ods-uri="$ODS_LIST" \
    identification-uri="$TMPDIR/ident.xml" \
    included-sheet-name-regex='^([Ll]($|[^o].*|o($|[^g].*|g($|[^s].*))))|^[^Ll].*' \
    2>&1 | tail -3; then

    if [ -f "$out_file" ]; then
      size=$(du -h "$out_file" | cut -f1)
      rows=$(grep -c '<Row>' "$out_file" 2>/dev/null || echo "?")
      echo "  ✓ OK: $size, $rows rows"
      DONE_COMBOS[$combo]="$ver"
      TOTAL_OK=$((TOTAL_OK + 1))
    else
      echo "  ✗ Output file not created"
    fi
  else
    echo "  ✗ Saxon conversion failed"
  fi

  rm -rf "$TMPDIR"
  echo ""
done

echo "=========================================="
echo "=== Summary ==="
echo "=========================================="
echo "  Converted: $TOTAL_OK"
echo "  Skipped:   $TOTAL_SKIP"
echo ""
echo "Output files:"
for ver in "${VERSIONS[@]}"; do
  gc="$OUTPUT_BASE/$ver/UBL-Entities-2.5.gc"
  if [ -f "$gc" ]; then
    size=$(du -h "$gc" | cut -f1)
    rows=$(grep -c '<Row>' "$gc" 2>/dev/null || echo "?")
    echo "  $ver: $size, $rows rows"
  else
    echo "  $ver: MISSING"
  fi
done
