#!/bin/bash
#
# validate-gc-pipeline.sh - Replicate the UBL TC gc generation and validation pipeline
#
# This script mirrors the validation logic from the official oasis-tcs/ubl build.xml:
#   Step 1: ODS → gc conversion  (Saxon + Crane-ods2obdgc.xsl)
#   Step 2: XSD validation       (xjparse + genericode.xsd)
#   Step 3: NDR semantic check   (Saxon + Crane-checkgc4obdndr.xsl)
#   Step 4: Compare with official gc (optional, if reference file provided)
#
# Usage:
#   ./validate-gc-pipeline.sh \
#     --library-ods <path>       Library ODS file
#     --documents-ods <path>     Documents ODS file
#     --output-dir <path>        Output directory for generated files
#     --stage <stage>            Stage label (e.g. csd01, csd02)
#     --version <version>        UBL version (e.g. 2.5)
#     [--reference-gc <path>]    Official gc file to compare against
#     [--skip-ndr]               Skip NDR check
#     [--skip-xsd]               Skip XSD validation
#     [--ndr-old-gc <path>]      Previous version gc for NDR comparison
#     [--signature-ods <path>]   Signature ODS file (optional)
#

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Tool paths (relative to repo root)
SAXON_JAR="$REPO_ROOT/history/tools/saxon9he/saxon9he.jar"
ODS2GC_XSL="$REPO_ROOT/history/tools/Crane-ods2obdgc/Crane-ods2obdgc.xsl"
MASSAGE_XML="$REPO_ROOT/work-sheets/scripts/massageModelName.xml"
GENERICODE_XSD="$REPO_ROOT/history/tools/genericode/xsd/genericode.xsd"
XJPARSE_DIR="$REPO_ROOT/history/tools/xjparse"
NDR_CHECK_XSL="$REPO_ROOT/history/tools/Crane-gc2obdndr/Crane-checkgc4obdndr.xsl"
NDR_CONFIG="$REPO_ROOT/history/tools/Crane-gc2obdndr/config-UBL.xml"
GC2ENDORSED_XSL="$REPO_ROOT/history/tools/Crane-gc2obdndr/gc2endorsed.xsl"
SPELLCHECK_DICT="$REPO_ROOT/history/tools/Crane-gc2obdndr/spellcheck-UBL.txt"
IDENT_TEMPLATE="$REPO_ROOT/history/tools/Crane-gc2obdndr/ident-UBL.xml"
IDENT_ENDORSED_TEMPLATE="$REPO_ROOT/history/tools/Crane-gc2obdndr/ident-UBL-Endorsed.xml"
IDENT_SIGNATURE_TEMPLATE="$REPO_ROOT/history/tools/Crane-gc2obdndr/ident-UBL-Signature.xml"

# The regex that excludes "Logs" sheets from ODS processing
# Matches anything that does NOT start with "Logs" (case-insensitive first L)
SHEET_REGEX='^([Ll]($|[^o].*|o($|[^g].*|g($|[^s].*))))|^[^Ll].*'

# ============================================================================
# Parse arguments
# ============================================================================

LIBRARY_ODS=""
DOCUMENTS_ODS=""
SIGNATURE_ODS=""
OUTPUT_DIR=""
STAGE=""
VERSION=""
REFERENCE_GC=""
SKIP_NDR=false
SKIP_XSD=false
NDR_OLD_GC=""
GENERATE_ENDORSED=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --library-ods)     LIBRARY_ODS="$2"; shift 2 ;;
    --documents-ods)   DOCUMENTS_ODS="$2"; shift 2 ;;
    --signature-ods)   SIGNATURE_ODS="$2"; shift 2 ;;
    --output-dir)      OUTPUT_DIR="$2"; shift 2 ;;
    --stage)           STAGE="$2"; shift 2 ;;
    --version)         VERSION="$2"; shift 2 ;;
    --reference-gc)    REFERENCE_GC="$2"; shift 2 ;;
    --skip-ndr)        SKIP_NDR=true; shift ;;
    --skip-xsd)        SKIP_XSD=true; shift ;;
    --ndr-old-gc)      NDR_OLD_GC="$2"; shift 2 ;;
    --endorsed)        GENERATE_ENDORSED=true; shift ;;
    *)                 echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Validate required args
if [[ -z "$LIBRARY_ODS" || -z "$DOCUMENTS_ODS" || -z "$OUTPUT_DIR" || -z "$STAGE" || -z "$VERSION" ]]; then
  echo "Error: Required arguments missing"
  echo "Usage: $0 --library-ods <path> --documents-ods <path> --output-dir <dir> --stage <stage> --version <version>"
  exit 1
fi

# ============================================================================
# Verify tools exist
# ============================================================================

echo "=== Verifying tools ==="
errors=0
for tool in "$SAXON_JAR" "$ODS2GC_XSL" "$MASSAGE_XML"; do
  if [[ ! -f "$tool" ]]; then
    echo "ERROR: Missing tool: $tool"
    errors=$((errors + 1))
  fi
done
if [[ $SKIP_XSD != true ]]; then
  for tool in "$GENERICODE_XSD" "$XJPARSE_DIR/xjparse.jar" "$XJPARSE_DIR/resolver.jar"; do
    if [[ ! -f "$tool" ]]; then
      echo "ERROR: Missing tool: $tool"
      errors=$((errors + 1))
    fi
  done
fi
if [[ $SKIP_NDR != true ]]; then
  for tool in "$NDR_CHECK_XSL" "$NDR_CONFIG"; do
    if [[ ! -f "$tool" ]]; then
      echo "ERROR: Missing tool: $tool"
      errors=$((errors + 1))
    fi
  done
fi
if [[ $errors -gt 0 ]]; then
  echo "ERROR: $errors missing tools. Aborting."
  exit 1
fi
echo "All tools verified."

# Verify input files exist
for f in "$LIBRARY_ODS" "$DOCUMENTS_ODS"; do
  if [[ ! -f "$f" ]]; then
    echo "ERROR: Input file not found: $f"
    exit 1
  fi
done

# ============================================================================
# Setup output directory
# ============================================================================

mkdir -p "$OUTPUT_DIR"

# Map stage label to short/dir entity values
STAGE_UPPER=$(echo "$STAGE" | tr '[:lower:]' '[:upper:]')

# ============================================================================
# Step 0: Create identification XML for this stage
# ============================================================================

echo ""
echo "=== Step 0: Creating identification XML ==="

IDENT_FILE="$OUTPUT_DIR/ident-UBL.xml"
cat > "$IDENT_FILE" << IDENT_EOF
<!DOCTYPE Identification [
<!ENTITY short "${STAGE_UPPER}">
<!ENTITY dir   "${STAGE}">
<!ENTITY version "${VERSION}">
]>
<Identification>
  <ShortName>UBL-&version;-&short;</ShortName>
  <LongName>UBL &version; &short; Business Entity Summary</LongName>
  <Version>&version;</Version>
  <CanonicalUri>urn:oasis:names:specification:ubl:BIE</CanonicalUri>
  <CanonicalVersionUri>urn:oasis:names:specification:ubl:BIE:&version;</CanonicalVersionUri>
  <LocationUri>http://docs.oasis-open.org/ubl/&dir;-UBL-&version;/mod/UBL-Entities-&version;.gc</LocationUri>
  <Agency>
     <LongName xml:lang="en">OASIS Universal Business Language</LongName>
     <Identifier>UBL</Identifier>
  </Agency>
</Identification>
IDENT_EOF
echo "Created: $IDENT_FILE"

if [[ "$GENERATE_ENDORSED" == true ]]; then
  IDENT_ENDORSED_FILE="$OUTPUT_DIR/ident-UBL-Endorsed.xml"
  cat > "$IDENT_ENDORSED_FILE" << IDENT_END_EOF
<!DOCTYPE Identification [
<!ENTITY short "${STAGE_UPPER}">
<!ENTITY dir   "${STAGE}">
<!ENTITY version "${VERSION}">
]>
<Identification>
  <ShortName>UBL-&version;-&short;-Endorsed</ShortName>
  <LongName>UBL &version; &short; Endorsed Business Entity Summary</LongName>
  <Version>&version;</Version>
  <CanonicalUri>urn:oasis:names:specification:ubl:BIE:ENDORSED</CanonicalUri>
  <CanonicalVersionUri>urn:oasis:names:specification:ubl:BIE:ENDORSED:&version;</CanonicalVersionUri>
  <LocationUri>http://docs.oasis-open.org/ubl/&dir;-UBL-&version;/mod/UBL-Entities-&version;-Endorsed.gc</LocationUri>
  <Agency>
     <LongName xml:lang="en">OASIS Universal Business Language</LongName>
     <Identifier>UBL</Identifier>
  </Agency>
</Identification>
IDENT_END_EOF
  echo "Created: $IDENT_ENDORSED_FILE"
fi

# ============================================================================
# Step 1: ODS → gc conversion (Saxon + Crane-ods2obdgc.xsl)
# ============================================================================

echo ""
echo "=== Step 1: ODS → gc conversion ==="

GC_OUTPUT="$OUTPUT_DIR/UBL-Entities-${VERSION}.gc"

# The source parameter accepts comma-separated ODS paths (library + documents)
SOURCE_ODS="$LIBRARY_ODS,$DOCUMENTS_ODS"

# Convert absolute paths to file:// URIs for Saxon
IDENT_URI="file://$(cd "$(dirname "$IDENT_FILE")" && pwd)/$(basename "$IDENT_FILE")"
LENGTHEN_URI="file://$MASSAGE_XML"

echo "  Source ODS: $SOURCE_ODS"
echo "  Output gc:  $GC_OUTPUT"
echo "  Ident URI:  $IDENT_URI"
echo "  Massage:    $LENGTHEN_URI"

java -jar "$SAXON_JAR" \
  -xsl:"$ODS2GC_XSL" \
  -o:"$GC_OUTPUT" \
  -it:ods-uri \
  "ods-uri=$SOURCE_ODS" \
  "identification-uri=$IDENT_URI" \
  "included-sheet-name-regex=$SHEET_REGEX" \
  "lengthen-model-name-uri=$LENGTHEN_URI" \
  2>&1 | tee "$OUTPUT_DIR/step1-ods2gc.log"

if [[ ! -f "$GC_OUTPUT" ]]; then
  echo "FAIL: gc file was not generated: $GC_OUTPUT"
  exit 1
fi

GC_SIZE=$(wc -c < "$GC_OUTPUT")
echo "SUCCESS: Generated $GC_OUTPUT ($GC_SIZE bytes)"

# ============================================================================
# Step 2: XSD validation (xjparse + genericode.xsd)
# ============================================================================

if [[ $SKIP_XSD == true ]]; then
  echo ""
  echo "=== Step 2: XSD validation SKIPPED ==="
else
  echo ""
  echo "=== Step 2: XSD validation ==="

  CLASSPATH="${XJPARSE_DIR}/xjparse.jar:${XJPARSE_DIR}/resolver.jar:${XJPARSE_DIR}"

  echo "  Validating $GC_OUTPUT against $GENERICODE_XSD"

  set +e
  java -cp "$CLASSPATH" com.nwalsh.parsers.xjparse \
    -S "$GENERICODE_XSD" "$GC_OUTPUT" \
    2>&1 | tee "$OUTPUT_DIR/step2-xsd-validation.log"
  XSD_RC=${PIPESTATUS[0]}
  set -e

  if [[ $XSD_RC -eq 0 ]]; then
    echo "SUCCESS: XSD validation passed"
  else
    echo "FAIL: XSD validation failed (exit code: $XSD_RC)"
    echo "  See: $OUTPUT_DIR/step2-xsd-validation.log"
    exit 1
  fi
fi

# ============================================================================
# Step 3: NDR semantic check (Saxon + Crane-checkgc4obdndr.xsl)
# ============================================================================

if [[ $SKIP_NDR == true ]]; then
  echo ""
  echo "=== Step 3: NDR semantic check SKIPPED ==="
else
  echo ""
  echo "=== Step 3: NDR semantic check ==="

  NDR_REPORT="$OUTPUT_DIR/ndr-check-${VERSION}-${STAGE}.html"
  NDR_WORDLIST="$OUTPUT_DIR/wordlist-UBL-${VERSION}.txt"
  touch "$NDR_WORDLIST"

  NDR_TITLE="Universal Business Language (UBL) ${VERSION} ${STAGE}"
  NDR_LIBRARY="UBL-CommonLibrary-${VERSION}"

  # Build the NDR check command
  NDR_ARGS=(
    -xsl:"$NDR_CHECK_XSL"
    -o:"$NDR_REPORT"
    -s:"$GC_OUTPUT"
    "config-uri=$NDR_CONFIG"
    "title-suffix=$NDR_TITLE"
    "common-library-singleton-model-name=$NDR_LIBRARY"
    "version-column-name=CurrentVersion"
    "den-word-list-uri=$NDR_WORDLIST"
    "errors-are-fatal=no"
    "--suppressXsltNamespaceCheck:on"
  )

  # Add old gc for comparison if provided
  if [[ -n "$NDR_OLD_GC" && -f "$NDR_OLD_GC" ]]; then
    echo "  Comparing against: $NDR_OLD_GC"
    NDR_ARGS+=("old-uri=$NDR_OLD_GC")
    NDR_ARGS+=("change-suffix=UBL")
  fi

  echo "  Source gc:  $GC_OUTPUT"
  echo "  Config:     $NDR_CONFIG"
  echo "  Report:     $NDR_REPORT"

  set +e
  java -Djava.awt.headless=true -jar "$SAXON_JAR" \
    "${NDR_ARGS[@]}" \
    2>&1 | tee "$OUTPUT_DIR/step3-ndr-check.log"
  NDR_RC=${PIPESTATUS[0]}
  set -e

  if [[ $NDR_RC -eq 0 ]]; then
    echo "SUCCESS: NDR check passed"
  else
    echo "WARNING: NDR check returned non-zero (exit code: $NDR_RC)"
    echo "  This may indicate naming/design rule violations."
    echo "  Review the report: $NDR_REPORT"
    # Don't exit - NDR check in UBL TC uses errors-are-fatal=no for stage checks
  fi

  if [[ -f "$NDR_REPORT" ]]; then
    echo "  NDR report: $NDR_REPORT"
  fi
fi

# ============================================================================
# Step 3b: Generate Endorsed gc (optional, for UBL 2.5+)
# ============================================================================

if [[ "$GENERATE_ENDORSED" == true ]]; then
  echo ""
  echo "=== Step 3b: Generate Endorsed gc ==="

  ENDORSED_RAW="$OUTPUT_DIR/UBL-Endorsed-Entities-${VERSION}-raw.gc"
  ENDORSED_GC="$OUTPUT_DIR/UBL-Endorsed-Entities-${VERSION}.gc"
  IDENT_ENDORSED_URI="file://$(cd "$(dirname "$IDENT_ENDORSED_FILE")" && pwd)/$(basename "$IDENT_ENDORSED_FILE")"

  # First generate raw endorsed gc (same conversion, different ident)
  echo "  Generating raw endorsed gc..."
  java -jar "$SAXON_JAR" \
    -xsl:"$ODS2GC_XSL" \
    -o:"$ENDORSED_RAW" \
    -it:ods-uri \
    "ods-uri=$SOURCE_ODS" \
    "identification-uri=$IDENT_ENDORSED_URI" \
    "included-sheet-name-regex=$SHEET_REGEX" \
    "lengthen-model-name-uri=$LENGTHEN_URI" \
    2>&1 | tee "$OUTPUT_DIR/step3b-endorsed-raw.log"

  if [[ ! -f "$ENDORSED_RAW" ]]; then
    echo "FAIL: Raw endorsed gc was not generated"
    exit 1
  fi

  # Then apply gc2endorsed.xsl to filter out deprecated entries
  echo "  Filtering endorsed entries..."
  java -jar "$SAXON_JAR" \
    -o:"$ENDORSED_GC" \
    -s:"$ENDORSED_RAW" \
    -xsl:"$GC2ENDORSED_XSL" \
    2>&1 | tee "$OUTPUT_DIR/step3b-endorsed-filter.log"

  rm -f "$ENDORSED_RAW"

  if [[ -f "$ENDORSED_GC" ]]; then
    ENDORSED_SIZE=$(wc -c < "$ENDORSED_GC")
    echo "SUCCESS: Generated $ENDORSED_GC ($ENDORSED_SIZE bytes)"
  else
    echo "FAIL: Endorsed gc was not generated"
    exit 1
  fi

  # XSD validate endorsed gc too
  if [[ $SKIP_XSD != true ]]; then
    echo "  Validating endorsed gc against XSD..."
    set +e
    java -cp "$CLASSPATH" com.nwalsh.parsers.xjparse \
      -S "$GENERICODE_XSD" "$ENDORSED_GC" \
      2>&1 | tee "$OUTPUT_DIR/step3b-endorsed-xsd.log"
    ENDORSED_XSD_RC=${PIPESTATUS[0]}
    set -e

    if [[ $ENDORSED_XSD_RC -eq 0 ]]; then
      echo "SUCCESS: Endorsed gc XSD validation passed"
    else
      echo "FAIL: Endorsed gc XSD validation failed (exit code: $ENDORSED_XSD_RC)"
    fi
  fi
fi

# ============================================================================
# Step 4: Compare with official gc (optional)
# ============================================================================

if [[ -n "$REFERENCE_GC" ]]; then
  echo ""
  echo "=== Step 4: Compare with official gc ==="

  if [[ ! -f "$REFERENCE_GC" ]]; then
    echo "ERROR: Reference gc not found: $REFERENCE_GC"
    exit 1
  fi

  echo "  Generated: $GC_OUTPUT"
  echo "  Reference: $REFERENCE_GC"

  # Simple diff comparison
  set +e
  diff -u "$REFERENCE_GC" "$GC_OUTPUT" > "$OUTPUT_DIR/step4-diff.txt" 2>&1
  DIFF_RC=$?
  set -e

  if [[ $DIFF_RC -eq 0 ]]; then
    echo "SUCCESS: Generated gc matches official gc EXACTLY"
  else
    DIFF_LINES=$(wc -l < "$OUTPUT_DIR/step4-diff.txt")
    echo "MISMATCH: Generated gc differs from official gc ($DIFF_LINES diff lines)"
    echo "  See: $OUTPUT_DIR/step4-diff.txt"

    # Show a summary of differences
    echo ""
    echo "  First 30 lines of diff:"
    head -30 "$OUTPUT_DIR/step4-diff.txt" | sed 's/^/    /'
  fi
else
  echo ""
  echo "=== Step 4: Compare SKIPPED (no --reference-gc provided) ==="
fi

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "========================================="
echo "  Pipeline Summary"
echo "========================================="
echo "  Stage:    ${STAGE} (UBL ${VERSION})"
echo "  Output:   $OUTPUT_DIR/"
echo "  Files:"
ls -la "$OUTPUT_DIR"/*.gc 2>/dev/null | sed 's/^/    /'
echo ""
echo "  Logs:"
ls -la "$OUTPUT_DIR"/step*.log 2>/dev/null | sed 's/^/    /'
echo "========================================="
echo "Done."
