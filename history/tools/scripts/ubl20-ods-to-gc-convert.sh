#!/bin/bash

# UBL 2.0 ODS to GenericCode Conversion Script
# Converts 30 ODS semantic model files to single unified GenericCode file
#
# Usage:
#   ./ubl20-ods-to-gc-convert.sh [output_directory] [input_directory]
#
# Defaults:
#   output_directory: current directory
#   input_directory: current directory (expects ODS files)

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="$(dirname "$SCRIPT_DIR")"
SAXON_JAR="$TOOLS_DIR/saxon9he/saxon9he.jar"
XSLT_STYLESHEET="$TOOLS_DIR/crane-ods2obdgc/Crane-ods2obdgc.xsl"

# Parameters
OUTPUT_DIR="${1:-.}"
INPUT_DIR="${2:-.}"
OUTPUT_FILE="$OUTPUT_DIR/UBL-Entities-2.0.gc"

# Check tools exist
if [ ! -f "$SAXON_JAR" ]; then
  echo "ERROR: Saxon9HE not found at $SAXON_JAR"
  exit 1
fi

if [ ! -f "$XSLT_STYLESHEET" ]; then
  echo "ERROR: Crane-ods2obdgc.xsl not found at $XSLT_STYLESHEET"
  exit 1
fi

echo "=== UBL 2.0 ODS to GenericCode Conversion ==="
echo ""
echo "Tools:"
echo "  Saxon: $SAXON_JAR"
echo "  XSLT:  $XSLT_STYLESHEET"
echo ""
echo "Input Directory:  $INPUT_DIR"
echo "Output Directory: $OUTPUT_DIR"
echo "Output File:      $OUTPUT_FILE"
echo ""

# Create temporary directory for workspace
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

echo "Temporary directory: $TMPDIR"
echo ""

# Copy ODS files to temporary directory
# (Crane-ods2obdgc expects local file paths, not URLs)
echo "Copying ODS files to temporary directory..."
if ! cp "$INPUT_DIR"/UBL-*.ods "$TMPDIR/" 2>/dev/null; then
  echo "ERROR: No UBL ODS files found in $INPUT_DIR"
  exit 1
fi

# List downloaded files
echo "Files found:"
ls -lh "$TMPDIR"/UBL-*.ods | awk '{print "  " $9 " (" $5 ")"}'

# Count ODS files
ODS_COUNT=$(ls -1 "$TMPDIR"/UBL-*.ods 2>/dev/null | wc -l)
echo ""
echo "Total ODS files: $ODS_COUNT"
echo ""

if [ "$ODS_COUNT" -lt 30 ]; then
  echo "WARNING: Expected 30 ODS files, found $ODS_COUNT"
  echo "Proceeding with available files..."
  echo ""
fi

# Create identification file
echo "Creating identification file..."
cat > "$TMPDIR/ident-UBL-2.0.xml" << 'IDENT'
<?xml version="1.0" encoding="UTF-8"?>
<gc:Identification xmlns:gc="http://docs.oasis-open.org/codelist/ns/genericode/1.0/">
  <gc:ShortName>UBL-2.0</gc:ShortName>
  <gc:Version>2.0</gc:Version>
</gc:Identification>
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

echo "ODS file list ready: $(echo "$ODS_LIST" | tr ',' '\n' | wc -l) files"
echo ""

# Run conversion
echo "Running XSLT transformation..."
echo ""

java -jar "$SAXON_JAR" \
  -xsl:"$XSLT_STYLESHEET" \
  -o:"$OUTPUT_FILE" \
  -it:ods-uri \
  ods-uri="$ODS_LIST" \
  identification-uri="$TMPDIR/ident-UBL-2.0.xml" \
  included-sheet-name-regex='^([Ll]($|[^o].*|o($|[^g].*|g($|[^s].*))))|^[^Ll].*'

echo ""
echo "=== Conversion Complete ==="
echo ""

# Verify output
if [ ! -f "$OUTPUT_FILE" ]; then
  echo "ERROR: Output file not created: $OUTPUT_FILE"
  exit 1
fi

SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
LINES=$(wc -l < "$OUTPUT_FILE")
ROWS=$(grep -c '<Row>' "$OUTPUT_FILE" 2>/dev/null || echo "?")

echo "Output File: $OUTPUT_FILE"
echo "  Size: $SIZE"
echo "  Lines: $LINES"
echo "  Data Rows: $ROWS"
echo ""

# Validate XML
echo "Validating XML..."
if xmllint --noout "$OUTPUT_FILE" 2>/dev/null; then
  echo "  ✓ Valid XML"
else
  echo "  ✗ XML validation failed"
  exit 1
fi

echo ""
echo "=== Conversion Successful ==="
echo ""
echo "GenericCode file ready: $OUTPUT_FILE"
echo ""
echo "To verify the file contents:"
echo "  grep -c '<Row>' $OUTPUT_FILE"
echo "  grep -A1 'ColumnRef=\"ModelName\"' $OUTPUT_FILE | grep '<SimpleValue>' | sort -u"
