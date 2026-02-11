#!/bin/bash

# UBL 2.0 All Stages ODS to GenericCode Conversion Script
# Converts 30 ODS semantic model files to GenericCode for all UBL 2.0 stage releases
#
# Usage:
#   ./ubl20-all-stages-convert.sh
#
# Converts all available UBL 2.0 stages:
#   - prd3-UBL-2.0
#   - prd3r1-UBL-2.0
#   - cs-UBL-2.0
#   - os-UBL-2.0

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="$(dirname "$SCRIPT_DIR")"
REPO_DIR="$(dirname "$(dirname "$TOOLS_DIR")")"
HISTORY_DIR="$REPO_DIR/history"

SAXON_JAR="$TOOLS_DIR/saxon9he/saxon9he.jar"
XSLT_STYLESHEET="$TOOLS_DIR/Crane-ods2obdgc/Crane-ods2obdgc.xsl"

# Check tools exist
if [ ! -f "$SAXON_JAR" ]; then
  echo "ERROR: Saxon9HE not found at $SAXON_JAR"
  exit 1
fi

if [ ! -f "$XSLT_STYLESHEET" ]; then
  echo "ERROR: Crane-ods2obdgc.xsl not found at $XSLT_STYLESHEET"
  exit 1
fi

echo "=== UBL 2.0 All Stages - ODS to GenericCode Conversion ==="
echo ""
echo "Tools:"
echo "  Saxon: $SAXON_JAR"
echo "  XSLT:  $XSLT_STYLESHEET"
echo ""

# List of stages to convert (in chronological order)
declare -a STAGES=("prd3-UBL-2.0" "prd3r1-UBL-2.0" "cs-UBL-2.0" "os-UBL-2.0")
declare -a STAGE_DATES=("2006-09-21" "2006-10-05" "2006-10-12" "2006-12-12")

# Process each stage
for idx in "${!STAGES[@]}"; do
  STAGE="${STAGES[$idx]}"
  STAGE_DATE="${STAGE_DATES[$idx]}"

  INPUT_DIR="$HISTORY_DIR/$STAGE/mod"

  # Check if input directory exists and has ODS files
  if [ ! -d "$INPUT_DIR" ]; then
    echo "WARNING: Input directory not found: $INPUT_DIR"
    continue
  fi

  ODS_COUNT=$(ls -1 "$INPUT_DIR"/UBL-*.ods 2>/dev/null | wc -l)
  if [ "$ODS_COUNT" -eq 0 ]; then
    echo "WARNING: No ODS files found in $INPUT_DIR"
    continue
  fi

  echo "=========================================="
  echo "Converting $STAGE ($STAGE_DATE)"
  echo "=========================================="
  echo ""

  # Create temporary directory
  TMPDIR=$(mktemp -d)
  trap "rm -rf $TMPDIR" EXIT

  echo "Temporary directory: $TMPDIR"

  # Copy ODS files to temporary directory
  echo "Copying ODS files..."
  cp "$INPUT_DIR"/UBL-*.ods "$TMPDIR/" 2>/dev/null || true

  echo "  ✓ $ODS_COUNT ODS files copied"
  echo ""

  # Create identification file
  echo "Creating identification file..."
  cat > "$TMPDIR/ident-UBL-2.0.xml" << 'IDENT'
<?xml version="1.0" encoding="UTF-8"?>
<Identification>
  <ShortName>UBL-2.0</ShortName>
  <LongName>UBL Version 2.0 Semantic Model</LongName>
  <Version>2.0</Version>
  <CanonicalUri>urn:oasis:names:specification:ubl:2.0</CanonicalUri>
  <CanonicalVersionUri>urn:oasis:names:specification:ubl:2.0</CanonicalVersionUri>
</Identification>
IDENT

  # Build ODS file list
  echo "Building ODS file list..."
  ODS_LIST=""
  for ods_file in "$TMPDIR"/UBL-*.ods; do
    if [ -z "$ODS_LIST" ]; then
      ODS_LIST="$ods_file"
    else
      ODS_LIST="$ODS_LIST,$ods_file"
    fi
  done

  # Create output directory in generated/
  OUTPUT_DIR="$HISTORY_DIR/generated/$STAGE/mod"
  mkdir -p "$OUTPUT_DIR"
  OUTPUT_FILE="$OUTPUT_DIR/UBL-Entities-2.0.gc"

  echo "Converting via Crane-ods2obdgc..."
  echo ""

  # Run conversion
  java -jar "$SAXON_JAR" \
    -xsl:"$XSLT_STYLESHEET" \
    -o:"$OUTPUT_FILE" \
    -it:ods-uri \
    ods-uri="$ODS_LIST" \
    identification-uri="$TMPDIR/ident-UBL-2.0.xml" \
    included-sheet-name-regex='^([Ll]($|[^o].*|o($|[^g].*|g($|[^s].*))))|^[^Ll].*' 2>&1 | head -5

  echo ""

  # Verify output
  if [ ! -f "$OUTPUT_FILE" ]; then
    echo "ERROR: Output file not created: $OUTPUT_FILE"
    continue
  fi

  SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
  LINES=$(wc -l < "$OUTPUT_FILE")
  ROWS=$(grep -c '<Row>' "$OUTPUT_FILE" 2>/dev/null || echo "?")

  echo "✓ Conversion complete"
  echo "  Output: $OUTPUT_FILE"
  echo "  Size: $SIZE, Lines: $LINES, Rows: $ROWS"
  echo ""

  # Validate XML
  if xmllint --noout "$OUTPUT_FILE" 2>/dev/null; then
    echo "  ✓ Valid XML"
  else
    echo "  ✗ XML validation failed"
  fi

  echo ""
done

echo "=========================================="
echo "=== All Conversions Complete ==="
echo "=========================================="
echo ""

# Summary
echo "Generated GenericCode files:"
for stage in "${STAGES[@]}"; do
  gc_file="$HISTORY_DIR/generated/$stage/mod/UBL-Entities-2.0.gc"
  if [ -f "$gc_file" ]; then
    size=$(du -h "$gc_file" | cut -f1)
    rows=$(grep -c '<Row>' "$gc_file" 2>/dev/null || echo "?")
    echo "  ✓ $stage ($size, $rows rows)"
  fi
done
