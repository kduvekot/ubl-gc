# ODS to GenericCode Conversion Guide

📍 **Navigation:** [Main](../../README.md) › [History](../README.md) › [Tools](README.md) › Conversion Guide

This guide explains how to use the tools in this directory to convert UBL ODS (OpenDocument Spreadsheet) files to GenericCode (GC) format.

**Related Documentation:**
- 🛠️ **[Tools Overview](README.md)** - Tool descriptions, provenance, and verification
- 📊 **[Tool Verification](TOOL_VERIFICATION.md)** - Known issues, performance, maintenance

## Quick Start

### For UBL 2.0 (Fastest Way)

If you have ODS files for a UBL 2.0 stage, use the automated script:

```bash
cd /home/user/ubl-gc
./history/tools/scripts/ubl20-ods-to-gc-convert.sh \
  /home/user/ubl-gc/history/generated/my-stage/mod \
  /home/user/ubl-gc/history/my-stage/mod
```

This will:
- Copy your ODS files
- Run the Crane-ods2obdgc transformation
- Validate the XML output
- Generate a GC file with proper statistics

### Manual Conversion (All UBL Versions)

```bash
# 1. Set up directories
WORK_DIR=$(mktemp -d)
ODS_DIR="/path/to/ods/files"
OUTPUT_DIR="/path/to/output"

# 2. Copy ODS files
cp $ODS_DIR/*.ods $WORK_DIR/

# 3. Create identification file
cat > $WORK_DIR/ident.xml << 'IDENT'
<?xml version="1.0" encoding="UTF-8"?>
<Identification>
  <ShortName>UBL-2.0</ShortName>
  <LongName>UBL Version 2.0 Semantic Model</LongName>
  <Version>2.0</Version>
  <CanonicalUri>urn:oasis:names:specification:ubl:2.0</CanonicalUri>
  <CanonicalVersionUri>urn:oasis:names:specification:ubl:2.0</CanonicalVersionUri>
</Identification>
IDENT

# 4. Build ODS file list
ODS_LIST=""
for f in $WORK_DIR/*.ods; do
  if [ -z "$ODS_LIST" ]; then
    ODS_LIST="$f"
  else
    ODS_LIST="$ODS_LIST,$f"
  fi
done

# 5. Run conversion
mkdir -p $OUTPUT_DIR
java -jar history/tools/saxon9he/saxon9he.jar \
  -xsl:history/tools/Crane-ods2obdgc/Crane-ods2obdgc.xsl \
  -o:$OUTPUT_DIR/UBL-Entities-2.0.gc \
  -it:ods-uri \
  ods-uri="$ODS_LIST" \
  identification-uri=$WORK_DIR/ident.xml \
  included-sheet-name-regex='^([Ll]($|[^o].*|o($|[^g].*|g($|[^s].*))))|^[^Ll].*'

# 6. Verify output
xmllint --noout $OUTPUT_DIR/UBL-Entities-2.0.gc
grep -c '<Row>' $OUTPUT_DIR/UBL-Entities-2.0.gc
```

## Understanding the Tools

### Saxon9HE (`saxon9he/`)
- **What it is**: XSLT 2.0 processor (Java application)
- **What it does**: Executes XSL stylesheets to transform XML/ODS data
- **How to use**: Call via `java -jar` command
- **License**: Mozilla Public License

### Crane-ods2obdgc (`Crane-ods2obdgc/`)
- **What it is**: OASIS official XSLT stylesheet
- **What it does**: Converts ODS spreadsheet structure to GenericCode XML format
- **How to use**: Pass to Saxon as `-xsl:` parameter
- **License**: OASIS license (see source repository)
- **Documentation**: See `Crane-ods2obdgc/readme-Crane-ods2obdgc.txt`

### Conversion Scripts (`scripts/`)
- **ubl20-ods-to-gc-convert.sh**: Single-stage conversion (handles all ODS directory structures)
- **ubl20-all-stages-convert.sh**: Batch conversion (handles prd3, prd3r1, cs, os only)

## Conversion Parameters Explained

When running the conversion, key parameters are:

- **ods-uri**: Comma-separated list of ODS file paths to convert
- **identification-uri**: XML file with metadata (ShortName, LongName, Version, URIs)
- **included-sheet-name-regex**: Regular expression to filter which worksheets to include
  - Current: `^([Ll]($|[^o].*|o($|[^g].*|g($|[^s].*))))|^[^Ll].*`
  - This includes ABIE, BBIE, and code list worksheets, but excludes "logs" sheets

## Step-by-Step Example: Converting prd-UBL-2.0

```bash
#!/bin/bash
set -e

# Set up paths
REPO_ROOT="/home/user/ubl-gc"
SOURCE_DIR="$REPO_ROOT/history/prd-UBL-2.0"
OUTPUT_DIR="$REPO_ROOT/history/generated/prd-UBL-2.0/mod"
WORK_DIR=$(mktemp -d)
trap "rm -rf $WORK_DIR" EXIT

echo "Converting prd-UBL-2.0..."

# Step 1: Copy ODS files from both subdirectories
echo "Copying ODS files..."
cp $SOURCE_DIR/mod/maindoc/*.ods $WORK_DIR/ 2>/dev/null || true
cp $SOURCE_DIR/mod/lib/*.ods $WORK_DIR/ 2>/dev/null || true
FILE_COUNT=$(ls -1 $WORK_DIR/*.ods | wc -l)
echo "  Found $FILE_COUNT ODS files"

# Step 2: Create identification metadata
echo "Creating identification file..."
cat > $WORK_DIR/ident.xml << 'IDENT'
<?xml version="1.0" encoding="UTF-8"?>
<Identification>
  <ShortName>UBL-2.0-PRD</ShortName>
  <LongName>UBL Version 2.0 Proposed Recommendation</LongName>
  <Version>2.0</Version>
  <CanonicalUri>urn:oasis:names:specification:ubl:2.0:prd</CanonicalUri>
  <CanonicalVersionUri>urn:oasis:names:specification:ubl:2.0:prd</CanonicalVersionUri>
</Identification>
IDENT

# Step 3: Build file list
echo "Building file list..."
ODS_LIST=""
for f in $WORK_DIR/*.ods; do
  if [ -z "$ODS_LIST" ]; then
    ODS_LIST="$f"
  else
    ODS_LIST="$ODS_LIST,$f"
  fi
done

# Step 4: Create output directory
mkdir -p $OUTPUT_DIR

# Step 5: Run transformation
echo "Running Crane-ods2obdgc transformation..."
java -jar $REPO_ROOT/history/tools/saxon9he/saxon9he.jar \
  -xsl:$REPO_ROOT/history/tools/Crane-ods2obdgc/Crane-ods2obdgc.xsl \
  -o:$OUTPUT_DIR/UBL-Entities-2.0.gc \
  -it:ods-uri \
  ods-uri="$ODS_LIST" \
  identification-uri=$WORK_DIR/ident.xml \
  included-sheet-name-regex='^([Ll]($|[^o].*|o($|[^g].*|g($|[^s].*))))|^[^Ll].*'

# Step 6: Verify output
echo "Verifying output..."
OUTPUT_FILE="$OUTPUT_DIR/UBL-Entities-2.0.gc"

if [ ! -f "$OUTPUT_FILE" ]; then
  echo "ERROR: Output file not created!"
  exit 1
fi

SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
ROWS=$(grep -c '<Row>' "$OUTPUT_FILE")

echo "✓ Conversion successful!"
echo "  File: $OUTPUT_FILE"
echo "  Size: $SIZE"
echo "  Rows: $ROWS"

# Validate XML
if xmllint --noout "$OUTPUT_FILE" 2>/dev/null; then
  echo "  ✓ Valid XML"
else
  echo "  ✗ XML validation failed!"
  exit 1
fi
```

## Troubleshooting

### "Java: command not found"
- Install Java: `apt-get install openjdk-11-jre`

### "No ODS files found"
- Check that ODS files exist in your source directory
- For prd/prd2, they may be in subdirectories (`mod/lib/`, `mod/common/`, etc.)
- Copy all ODS files to a single directory before conversion

### "Processing terminated by xsl:message"
- This usually means the ODS files couldn't be read as ZIP packages
- Verify files are actual ODS files (not corrupted)
- Copy files to local directory instead of using remote paths

### "XML validation failed"
- The transformation may have completed but produced invalid XML
- Check the generated file for malformed tags
- Look at the XSL transformation output for error messages

## Verification Checklist

After conversion, verify:

- ✓ Output file exists and is not empty
- ✓ File size is reasonable (>2MB for UBL 2.0)
- ✓ XML is valid: `xmllint --noout output.gc`
- ✓ Row count is expected: `grep -c '<Row>' output.gc`
- ✓ Identification metadata is present: `grep '<Identification>' output.gc`
- ✓ Column structure is correct: `grep '<ColumnRef' output.gc`

## Current Status

**Tested and Verified:**
- ✅ All 8 UBL 2.0 stages (prd, prd2, prd3, prd3r1, cs, os, os-update, errata)
- ✅ Handles multiple ODS directory structures (flat, subdirectories)
- ✅ Tools work with 30-33 ODS files per stage

**Not Tested:**
- ❌ UBL 2.1-2.5 conversions (no ODS files available for these versions)

## References

- Crane-ods2obdgc documentation: `Crane-ods2obdgc/readme-Crane-ods2obdgc.txt`
- GenericCode specification: https://docs.oasis-open.org/codelist/genericode/
- OASIS UBL repository: https://github.com/oasis-tcs/ubl
- Saxon documentation: https://www.saxonica.com/

## Questions or Issues?

See the main repository documentation:
- `/README.md` - Complete project overview
- `/history/README.md` - Archive structure and semantic evolution
- `/docs/historical-releases.md` - Release timeline and OASIS URLs
