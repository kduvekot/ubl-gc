# ODS Revision Diff Analysis: ubl25_library & ubl25_documents

**Date:** 2026-02-17
**Source:** Google Drive public folder, slow-validation ODS exports
**Revisions analyzed:**
- **Library:** 92 files (rev 1-100 consecutive, samples at 150, 200, 500, 1000, 1500, 1843, 1999, 2005)
- **Documents:** 132 files (rev 1-50, 146-194, 1719-1751)

---

## Part 1: ubl25_library (2,005 revisions)

### Summary

The Google Sheets revision history for ubl25_library contains **2,005 revisions**.
Analysis of the first 100 consecutive revisions reveals that:

1. **Real edits are tiny** — typically 0-2 cells changed per revision
2. **"Massive" diffs are artifacts** of column/row insertion shifting data positions
3. **One worksheet** ("CommonLibrary") for rev 1-~1200, then a **second sheet** ("Logs-sheet") appears
4. **Formulas** use OpenFormula syntax with absolute column references that shift on insert

### 1. Column Structure Changes (header additions/removals/renames)

The editor iteratively designed the column structure:

| Revision | Change | Notes |
|----------|--------|-------|
| 3→4 | +`Deprecated cardinality` | New column inserted after Cardinality |
| 8→9 | Renamed → `Future cardinality` | |
| 9→10 | Renamed → `Endorsed cardinality` | Final name |
| 13→14 | +`Deprecated definition` | New column after Definition |
| 16→17 | +`Deprecated` | Column A (before Component Name) |
| 17→18 | −`Deprecated` | Immediately removed |
| 20→21 | +`Deprecated` | Re-added |
| 21→22 | +`Depracion rational` | **Typo!** |
| 22→23 | → `Depracion rationale` | Partial fix (still misspelled) |
| ~35 | → `Deprecation rationale` | Spelling fixed |
| 42 | → `Endorsed cardinality rationale` | Renamed to match column purpose |
| ~75 | Capitalization: `Endorsed Cardinality`, etc. | Title case applied |

### 2. Single-Cell Data Edits (the real editorial work)

Most revisions change 0-2 cells:

| Revision | Cell Changed | Old → New |
|----------|-------------|-----------|
| 5→6 | Cardinality row 4 | "0..1" → "1" |
| 6→7 | Cardinality row 4 | "1" → "0..1" (undo!) |
| 28→29 | Endorsed cardinality row 5 | "_" → "0" |
| 42→43 | Endorsed cardinality rationale row 5 | "SellerSupplierParty will be removed..." → "...has been deprecated since UBL..." |
| 45-50 | Various Endorsed cardinality cells | Adding values one at a time |
| 78→79 | Definition row 907 | "environmental emission" → "environmental impact" |
| 82→83 | Cardinality row 909 | "1" → "0..1" |
| 83→84 | Cardinality row 908 | "1" → "0..1" |
| 91→92 | Component Name row 907 | "EnvironmentalEmission" → "EnvironmentalImpact" |
| 92→93 | Component Name row 907 | "EnvironmentalImpact" → "EnvironmentalEmission" (undo!) |
| 96→97 | Cardinality row 908 | "0..1" → "1" |
| 97→98 | Cardinality row 909 | "0..1" → "1" |

### 3. Row Insertions (rare, produce massive position-shift diffs)

| Revision | Real Change | Apparent Changes |
|----------|-------------|------------------|
| 79→80 | 1 empty row inserted at ~row 913 | 17,573 "changes" (all just shifted down) |
| 88→89 | 1 empty row inserted | 17,573 "changes" |
| 95→96 | 1 empty row removed | 17,573 "changes" |

Evidence: Component Names are identical multisets; 2,085 rows shift position;
only 1 row is truly added/removed.

### 4. Formula Reference Shifts (automatic, not user edits)

All ~11,434 formulas reference columns by letter (e.g., `[.H2]`).
When a column is inserted, ALL formula references shift by +1 letter:
- `of:=SUBSTITUTE(CONCATENATE([.H2];[.I2]);" ";"")` (rev-1)
- `of:=SUBSTITUTE(CONCATENATE([.I2];[.J2]);" ";"")` (rev-2, after column D insert)

The **computed values are identical** — only the formula text differs.

### 5. Style-Only Changes (rare)

Occasional cell formatting changes without any text or formula change.
Example: rev 11→12 (style change on Endorsed cardinality cell).

### Quantitative Summary (rev 1-100, positional diff)

| Metric | Count |
|--------|-------|
| Total transitions analyzed | 85 |
| Transitions with zero changes (text-only) | 39 (46%) |
| Transitions with 1-2 cell changes | 40 (47%) |
| Transitions with row/col insertion artifacts | 6 (7%) |
| **Real text edits** (across all 100 revisions) | **~50 cells** |

### Full Semantic Diff (rev 1-1000)

A complete cell-level diff using **semantic matching** (columns matched by header
name, rows by Dictionary Entry Name) across all 999 consecutive transitions:

| Metric | Count |
|--------|-------|
| Total transitions analyzed | 999 |
| Identical transitions (no changes at all) | 246 (24.6%) |
| Style-only transitions (formatting noise) | 41 (4.1%) |
| Changed transitions | 712 (71.3%) |
| Total cell-level changes | 717,424 |
| **Formula reference shifts** (row insertion artifacts) | **717,068 (99.95%)** |
| **Real user edits** | **219 (0.03%)** |
| Rows added (new components) | ~120 |
| Rows removed | ~90 |
| Column structure changes | 22 (all in rev 1-75) |

**Key finding:** 99.95% of all detected cell changes are formula reference shifts —
when a row is inserted, all ~1,700 formulas in the sheet update their row
references (e.g., `[.H2]` → `[.H3]`), producing ~1,700 `formula_change` records
per row insertion even though the computed values are identical. The actual editorial
work is just **219 user edits across 1,000 revisions** — almost always exactly
1 cell change per revision.

#### Editing Pattern

- **207 transitions** contain at least 1 user edit
- **Almost always 1 cell per revision** — extremely granular editing
- Common pattern: edit Cardinality, Endorsed Cardinality, Definition, or
  Component Name in a single row, then move to next item
- Multi-edit transitions (2-3 user edits) appear when related fields in the same
  row change together (e.g., Component Name + Dictionary Entry Name rename)

#### Row Growth (rev 1-1000)

~120 rows added across 1,000 revisions, representing new UBL components being
defined. The row count grows from 3,010 (rev 1) to 3,099 (rev 1000). Rows are
occasionally removed and re-added as components are reorganized.

### Worksheet Evolution (full range)

| Revision | Sheets | CommonLibrary Rows | Cols | Notes |
|----------|--------|-------------------|------|-------|
| 1 | 1 | 3,010 | 22 | Original (pre-CSD02) |
| 50 | 1 | 3,010 | 26 | +4 cols (Endorsed, Deprecated, Last Changed) |
| 100 | 1 | 3,011 | 26 | +1 row |
| 200 | 1 | 3,012 | 26 | |
| 500 | 1 | 3,051 | 26 | +40 rows (new components) |
| 1000 | 1 | 3,099 | 26 | +48 rows |
| **~1200-1500** | **2** | 3,187 | 26 | **+"Logs-sheet"** (script execution logs) |
| 1843 | 2 | 3,185 | 26 | Maps to V1/V2 workflow |
| 1999 | 2 | 3,187 | 26 | CSD02 official state |
| 2005 | 2 | 3,187 | 26 | Final (current) |

### Logs-sheet Details

Appears between rev 1000 and 1500. Contains automated script execution logs:
- First entry: "10/13/2025 7:11:14 | Script executed. | Edited by: kees@duvekot.net"
- 26-38 rows (varies per revision)
- Records when Apps Script automations ran against the sheet

---

## Part 2: ubl25_documents (2,161 revisions)

### Summary

The documents sheet contains **93-102 worksheets** — one per UBL document type (ApplicationResponse, AttachedDocument, Invoice, Order, etc.) plus a Logs-sheet.

Key findings:

1. **Editing proceeds one document type at a time**, in strict **alphabetical order**
2. Each document type takes exactly **4 revisions** to process
3. The "fast download" first attempt produced mostly collapsed revisions, but **three clusters** retained actual historical content
4. 9 document types were temporarily removed and later re-added

### Fast Download Collapse Pattern

The first-attempt bulk download (without rate limiting) produced 2,161 files, but most are collapsed to the current state:

| Revision Range | Content | ODS Size | Sheets | Cols |
|---------------|---------|----------|--------|------|
| 1-8 | Collapsed (current) | 932K | 102 | 26 |
| **9-47** | **Historical** | 789-792K | 93 | 22-26 |
| 48-145 | Collapsed | 932K | 102 | 26 |
| **146-194** | **Historical** | 807-815K | 93 | 22-26 |
| 195-1718 | Collapsed | 932K | 102 | 26 |
| **1719-1751** | **Historical** | 910-911K | 100 | 22-26 |
| 1752-2161 | Collapsed | 932K | 102 | 26 |

### Sheet Count Evolution

| State | Sheets | Extra Sheets | Notes |
|-------|--------|-------------|-------|
| Current/final (collapsed) | 102 | +9 | DeliveryNote, InvoiceStatusRequest, InvoiceStatusResponse, Logs-sheet, ProcurementStatus, ProcurementStatusRequest, WasteMovement, WasteNotification, WorkReport |
| Historical (rev 9-194) | 93 | — | 9 sheets removed during editing |
| Historical (rev 1719-1751) | 100 | +7 | Some sheets re-added |

### Alphabetical Editing Pattern (rev 9-194)

**Each document type takes exactly 4 revisions:**

1. **Rev N**: Column restructure (adds 4 endorsed/deprecated columns) + data edits
2. **Rev N+1**: Same restructure repeated
3. **Rev N+2**: Slightly smaller restructure variant
4. **Rev N+3**: Header-only changes (cleanup)
5. Move to next document type alphabetically

**Documented sheet processing order (from diff analysis):**

| Revisions | Document Type | Changes per Rev |
|-----------|--------------|-----------------|
| 9-43 | ApplicationResponse | 1-307 |
| 44-47 | AttachedDocument | 299-340 |
| ... | (gap: rev 48-145 collapsed) | ... |
| 146-148 | ExceptionNotification | 3-280 |
| 148-152 | ExportCustomsDeclaration | 244-276 |
| 152-156 | ExpressionOfInterestRequest | 300-343 |
| 156-160 | ExpressionOfInterestResponse | 289-330 |
| 160-164 | Forecast | 323-365 |
| 164-168 | ForecastRevision | 326-368 |
| 168-172 | ForwardingInstructions | 398-449 |
| 172-176 | FreightInvoice | 665-762 |
| 176-180 | FulfilmentCancellation | 324-371 |
| 180-184 | GoodsCertificate | 423-484 |
| 184-188 | GoodsItemItinerary | 300-343 |
| 188-192 | GoodsItemPassport | 404-461 |
| 192-194 | GuaranteeCertificate | 397 |
| ... | (gap: rev 195-1718 collapsed) | ... |

### Late-Stage Fine-Tuning (rev 1719-1751)

By revision ~1719, the alphabetical restructuring is complete. This cluster shows:

- **34 total cell changes** across 32 transitions (vs hundreds per transition earlier)
- **Single-cell edits** across multiple sheets in each revision
- **Logs-sheet renamed** from "Logs" to "Logs-sheet" (rev 1720→1721)
- Occasional row additions/removals in ApplicationResponse and WorkReport
- Sequential single-cell edits moving through: CallForTenders, ContractAwardNotice, ContractNotice, CreditNote, DebitNote, DespatchAdvice, DocumentStatus, etc.

### Column Structure (within historical revisions)

During the alphabetical editing process, the editor adds 4 columns to each document type sheet:
- From 22 columns (original) → 26 columns (with endorsed/deprecated columns)
- The column addition is visible as a "wavefront" moving alphabetically through the sheets
- Sheets not yet processed have 22 columns; processed sheets have 26

### Change Composition per Document Type

A typical 4-revision edit cycle for one document type breaks down as:

| Category | Count | Notes |
|----------|-------|-------|
| header_change | ~20 | Column headers shifting from 22→26 |
| added | ~100-200 | New cells in added columns |
| removed | ~100-200 | Old cell positions (position shift artifact) |
| user_edit | ~40-140 | Real content edits (varies by document complexity) |
| style_only | ~5-15 | Formatting changes |

---

## Key Insight: ODS Export Non-Determinism

The ODS export from Google Sheets is **not deterministic**:
- Same logical sheet state → different ODS XML
- Column insertion changes formula text (reference shifts)
- Row insertion shifts all data positions
- settings.xml and meta.xml change between revisions even when content is identical
- These produce massive apparent diffs that are pure artifacts

For meaningful comparison, diffs must be:
1. **Header-aware** (match by column name, not position)
2. **Content-hash based** (compare text, ignore formula references)
3. **Row-identity based** (match by Component Name, not row number)
4. **Multi-sheet aware** (documents has 93-102 sheets)

---

## Scripts

- `work-sheets/scripts/download-drive-revisions.py` — Download .ods.gz from public Drive folder
- `work-sheets/scripts/diff-ods-revisions.py` — ODS diff with semantic matching:
  - **Default: semantic mode** — matches columns by header name, rows by
    Dictionary Entry Name, eliminating false changes from insertions
  - `--streaming` — Pairwise mode: parse 2 files at a time, write per-pair
    JSON to disk, free memory (essential for 100+ revisions)
  - `--output-dir DIR` — Output directory for streaming mode JSON files
  - `--positional` — Legacy positional comparison (generates false changes)
  - `--text-only` — Ignore formulas (eliminates column-shift noise)
  - `--all-sheets` — Compare all sheets in multi-sheet ODS files
  - `--range N-M` — Process a specific revision range
  - `--json FILE` — Write structured results to JSON
  - `--verbose` — Show detailed per-change output

---

## Next Steps

1. ~~Build a multi-sheet diff~~ ✓ Done (`--all-sheets` flag)
2. ~~Extend analysis to documents sheet~~ ✓ Done (3 clusters analyzed)
3. Download the full slow-validation ODS files for documents once the Colab notebook completes
4. Cross-reference with OASIS release dates to identify which revisions
   correspond to formal committee draft stages
5. Map the alphabetical editing wavefront to estimate total edit duration
   (93 sheets × 4 revisions ≈ 372 revisions for complete restructuring)
6. Analyze the Logs-sheet for Apps Script execution patterns and timing
