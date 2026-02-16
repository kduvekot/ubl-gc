#!/bin/bash
#
# Convert Google Sheets revision ODS exports to GenericCode (.gc)
# using the EXACT same pipeline as the official oasis-tcs/ubl CI workflow.
#
# Pipeline per version:
#   1. Generate ident-UBL.xml (matching official format with stage/dir)
#   2. Generate ident-UBL-Endorsed.xml (same pattern, endorsed URIs)
#   3. Saxon + Crane-ods2obdgc.xsl + massageModelName.xml → UBL-Entities-2.5.gc
#   4. Saxon + Crane-ods2obdgc.xsl + massageModelName.xml → UBL-Endorsed-Entities-2.5-raw.gc
#   5. Saxon + gc2endorsed.xsl: raw → UBL-Endorsed-Entities-2.5.gc
#
# Key difference from previous script: passes lengthen-model-name-uri
# (massageModelName.xml) so ODS worksheet short names get expanded to
# proper UBL names (e.g., "Invoice" → "UBL-Invoice-2.5").
#
# Usage:
#   ./work-sheets/scripts/convert-revision-ods-to-gc.sh [--force]
#
# Prerequisites:
#   - Java (for Saxon)
#   - ODS files in work-sheets/revision-ods/
#
# Output per version:
#   work-sheets/gc-from-revisions/{version}/UBL-Entities-2.5.gc
#   work-sheets/gc-from-revisions/{version}/UBL-Endorsed-Entities-2.5.gc

set -e

FORCE=false
if [ "$1" = "--force" ]; then
  FORCE=true
fi

# Paths (relative to repo root)
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOLS_DIR="$REPO_DIR/history/tools"
SAXON_JAR="$TOOLS_DIR/saxon9he/saxon9he.jar"
XSLT_STYLESHEET="$TOOLS_DIR/Crane-ods2obdgc/Crane-ods2obdgc.xsl"
SCRIPTS_DIR="$REPO_DIR/work-sheets/scripts"
MASSAGE_MODEL_NAME="$SCRIPTS_DIR/massageModelName.xml"
GC2ENDORSED_XSL="$SCRIPTS_DIR/gc2endorsed.xsl"

ODS_DIR="$REPO_DIR/work-sheets/revision-ods"
OUTPUT_BASE="$REPO_DIR/work-sheets/gc-from-revisions"

# Check tools
for f in "$SAXON_JAR" "$XSLT_STYLESHEET" "$MASSAGE_MODEL_NAME" "$GC2ENDORSED_XSL"; do
  if [ ! -f "$f" ]; then
    echo "ERROR: Required file not found: $f"
    exit 1
  fi
done

# Sheet name filter regex (excludes "Logs" sheets) — same as official build.xml
SHEET_REGEX='^([Ll]($|[^o].*|o($|[^g].*|g($|[^s].*))))|^[^Ll].*'

echo "=== Convert Revision ODS → GenericCode (official pipeline match) ==="
echo ""
echo "Tools:"
echo "  Saxon:              $SAXON_JAR"
echo "  Crane-ods2obdgc:    $XSLT_STYLESHEET"
echo "  massageModelName:   $MASSAGE_MODEL_NAME"
echo "  gc2endorsed:        $GC2ENDORSED_XSL"
echo ""

# ---------------------------------------------------------------------------
# Version definitions: (version, library_rev, documents_rev, stage_short, stage_dir)
#
# Stage labels match what the oasis-tcs/ubl repo had when each CI run happened:
#   V1-V5: CSD02 / csd02  (pre-CSD02 development + published CSD02)
#   V6-V10: CSD03 / csd03 (post-CSD02 / pre-CSD03 development)
# ---------------------------------------------------------------------------

declare -a VERSIONS=( "V1" "V2" "V3" "V4" "V5" "V6" "V7" "V8" "V9" "V10" )

declare -A LIB_REV=(
  [V1]=1843  [V2]=1843  [V3]=1868  [V4]=1868  [V5]=1999
  [V6]=1999  [V7]=2005  [V8]=2005  [V9]=2005  [V10]=2005
)
declare -A DOC_REV=(
  [V1]=1793  [V2]=1793  [V3]=1803  [V4]=1983  [V5]=2190
  [V6]=2190  [V7]=2190  [V8]=2200  [V9]=2204  [V10]=2204
)
declare -A STAGE_SHORT=(
  [V1]=CSD02  [V2]=CSD02  [V3]=CSD02  [V4]=CSD02  [V5]=CSD02
  [V6]=CSD03  [V7]=CSD03  [V8]=CSD03  [V9]=CSD03  [V10]=CSD03
)
declare -A STAGE_DIR=(
  [V1]=csd02  [V2]=csd02  [V3]=csd02  [V4]=csd02  [V5]=csd02
  [V6]=csd03  [V7]=csd03  [V8]=csd03  [V9]=csd03  [V10]=csd03
)

TOTAL_OK=0
TOTAL_SKIP=0
TOTAL_FAIL=0

for ver in "${VERSIONS[@]}"; do
  lib_rev="${LIB_REV[$ver]}"
  doc_rev="${DOC_REV[$ver]}"
  short="${STAGE_SHORT[$ver]}"
  sdir="${STAGE_DIR[$ver]}"

  lib_ods="$ODS_DIR/ubl25_library/rev-${lib_rev}.ods"
  doc_ods="$ODS_DIR/ubl25_documents/rev-${doc_rev}.ods"
  out_dir="$OUTPUT_BASE/$ver"
  entities_file="$out_dir/UBL-Entities-2.5.gc"
  endorsed_file="$out_dir/UBL-Endorsed-Entities-2.5.gc"

  echo "--- $ver (lib=rev-${lib_rev}, doc=rev-${doc_rev}, stage=${short}) ---"

  # Skip if both outputs already exist (unless --force)
  if [ "$FORCE" = false ] && [ -f "$entities_file" ] && [ -f "$endorsed_file" ]; then
    e_rows=$(grep -c '<Row>' "$entities_file" 2>/dev/null || echo "?")
    n_rows=$(grep -c '<Row>' "$endorsed_file" 2>/dev/null || echo "?")
    echo "  [skip] already exists (Entities: $e_rows rows, Endorsed: $n_rows rows)"
    TOTAL_SKIP=$((TOTAL_SKIP + 1))
    echo ""
    continue
  fi

  # Check ODS files exist
  if [ ! -f "$lib_ods" ]; then
    echo "  ERROR: library ODS not found: $lib_ods"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
    echo ""
    continue
  fi
  if [ ! -f "$doc_ods" ]; then
    echo "  ERROR: documents ODS not found: $doc_ods"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
    echo ""
    continue
  fi

  # Create temp dir for this version
  TMPDIR=$(mktemp -d)

  # Copy ODS files to temp (Crane XSLT resolves relative to working dir)
  cp "$lib_ods" "$TMPDIR/UBL-Library-Google.ods"
  cp "$doc_ods" "$TMPDIR/UBL-Documents-Google.ods"

  # Copy massageModelName.xml to temp (Saxon resolves URI relative to base)
  cp "$MASSAGE_MODEL_NAME" "$TMPDIR/massageModelName.xml"

  # --- Generate ident-UBL.xml (matching official format exactly) ---
  cat > "$TMPDIR/ident-UBL.xml" << IDENT_UBL
<?xml version="1.0" encoding="UTF-8"?>
<Identification>
  <ShortName>UBL-2.5-${short}</ShortName>
  <LongName>UBL 2.5 ${short} Business Entity Summary</LongName>
  <Version>2.5</Version>
  <CanonicalUri>urn:oasis:names:specification:ubl:BIE</CanonicalUri>
  <CanonicalVersionUri>urn:oasis:names:specification:ubl:BIE:2.5</CanonicalVersionUri>
  <LocationUri>http://docs.oasis-open.org/ubl/${sdir}-UBL-2.5/mod/UBL-Entities-2.5.gc</LocationUri>
  <Agency>
     <LongName xml:lang="en">OASIS Universal Business Language</LongName>
     <Identifier>UBL</Identifier>
  </Agency>
</Identification>
IDENT_UBL

  # --- Generate ident-UBL-Endorsed.xml (matching official format exactly) ---
  cat > "$TMPDIR/ident-UBL-Endorsed.xml" << IDENT_END
<?xml version="1.0" encoding="UTF-8"?>
<Identification>
  <ShortName>UBL-2.5-${short}-Endorsed</ShortName>
  <LongName>UBL 2.5 ${short} Endorsed Business Entity Summary</LongName>
  <Version>2.5</Version>
  <CanonicalUri>urn:oasis:names:specification:ubl:BIE:ENDORSED</CanonicalUri>
  <CanonicalVersionUri>urn:oasis:names:specification:ubl:BIE:ENDORSED:2.5</CanonicalVersionUri>
  <LocationUri>http://docs.oasis-open.org/ubl/${sdir}-UBL-2.5/mod/UBL-Entities-2.5-Endorsed.gc</LocationUri>
  <Agency>
     <LongName xml:lang="en">OASIS Universal Business Language</LongName>
     <Identifier>UBL</Identifier>
  </Agency>
</Identification>
IDENT_END

  mkdir -p "$out_dir"
  ODS_LIST="$TMPDIR/UBL-Library-Google.ods,$TMPDIR/UBL-Documents-Google.ods"

  # ===== Step 1: Generate UBL-Entities-2.5.gc =====
  echo "  [1/3] Generating UBL-Entities-2.5.gc..."

  if java -jar "$SAXON_JAR" \
    -xsl:"$XSLT_STYLESHEET" \
    -o:"$entities_file" \
    -it:ods-uri \
    ods-uri="$ODS_LIST" \
    identification-uri="$TMPDIR/ident-UBL.xml" \
    included-sheet-name-regex="$SHEET_REGEX" \
    lengthen-model-name-uri="$TMPDIR/massageModelName.xml" \
    2>&1 | tail -3; then

    if [ -f "$entities_file" ]; then
      e_size=$(du -h "$entities_file" | cut -f1)
      e_rows=$(grep -c '<Row>' "$entities_file" 2>/dev/null || echo "?")
      echo "       OK: $e_size, $e_rows rows"
    else
      echo "       FAIL: output file not created"
      TOTAL_FAIL=$((TOTAL_FAIL + 1))
      rm -rf "$TMPDIR"
      echo ""
      continue
    fi
  else
    echo "       FAIL: Saxon conversion failed"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
    rm -rf "$TMPDIR"
    echo ""
    continue
  fi

  # ===== Step 2: Generate UBL-Endorsed-Entities-2.5-raw.gc =====
  echo "  [2/3] Generating endorsed raw GC..."

  RAW_ENDORSED="$TMPDIR/UBL-Endorsed-Entities-2.5-raw.gc"

  if java -jar "$SAXON_JAR" \
    -xsl:"$XSLT_STYLESHEET" \
    -o:"$RAW_ENDORSED" \
    -it:ods-uri \
    ods-uri="$ODS_LIST" \
    identification-uri="$TMPDIR/ident-UBL-Endorsed.xml" \
    included-sheet-name-regex="$SHEET_REGEX" \
    lengthen-model-name-uri="$TMPDIR/massageModelName.xml" \
    2>&1 | tail -3; then

    if [ ! -f "$RAW_ENDORSED" ]; then
      echo "       FAIL: raw endorsed file not created"
      TOTAL_FAIL=$((TOTAL_FAIL + 1))
      rm -rf "$TMPDIR"
      echo ""
      continue
    fi
  else
    echo "       FAIL: Saxon conversion for endorsed failed"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
    rm -rf "$TMPDIR"
    echo ""
    continue
  fi

  # ===== Step 3: Filter endorsed via gc2endorsed.xsl =====
  echo "  [3/3] Filtering endorsed via gc2endorsed.xsl..."

  if java -jar "$SAXON_JAR" \
    -o:"$endorsed_file" \
    -s:"$RAW_ENDORSED" \
    -xsl:"$GC2ENDORSED_XSL" \
    2>&1 | tail -3; then

    if [ -f "$endorsed_file" ]; then
      n_size=$(du -h "$endorsed_file" | cut -f1)
      n_rows=$(grep -c '<Row>' "$endorsed_file" 2>/dev/null || echo "?")
      echo "       OK: $n_size, $n_rows rows"
    else
      echo "       FAIL: endorsed output file not created"
      TOTAL_FAIL=$((TOTAL_FAIL + 1))
      rm -rf "$TMPDIR"
      echo ""
      continue
    fi
  else
    echo "       FAIL: gc2endorsed.xsl conversion failed"
    TOTAL_FAIL=$((TOTAL_FAIL + 1))
    rm -rf "$TMPDIR"
    echo ""
    continue
  fi

  TOTAL_OK=$((TOTAL_OK + 1))
  rm -rf "$TMPDIR"
  echo ""
done

echo "=========================================="
echo "=== Summary ==="
echo "=========================================="
echo "  Converted: $TOTAL_OK"
echo "  Skipped:   $TOTAL_SKIP"
echo "  Failed:    $TOTAL_FAIL"
echo ""
echo "Output files:"
for ver in "${VERSIONS[@]}"; do
  ent="$OUTPUT_BASE/$ver/UBL-Entities-2.5.gc"
  end="$OUTPUT_BASE/$ver/UBL-Endorsed-Entities-2.5.gc"
  if [ -f "$ent" ] && [ -f "$end" ]; then
    e_rows=$(grep -c '<Row>' "$ent" 2>/dev/null || echo "?")
    n_rows=$(grep -c '<Row>' "$end" 2>/dev/null || echo "?")
    echo "  $ver: Entities=$e_rows rows, Endorsed=$n_rows rows"
  elif [ -f "$ent" ]; then
    e_rows=$(grep -c '<Row>' "$ent" 2>/dev/null || echo "?")
    echo "  $ver: Entities=$e_rows rows, Endorsed=MISSING"
  else
    echo "  $ver: MISSING"
  fi
done
