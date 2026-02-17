# ODS Revision Diff Analysis: ubl25_library (rev 1-2005)

**Date:** 2026-02-17
**Sheet:** ubl25_library
**Source:** Google Drive public folder, slow-validation ODS exports
**Revisions analyzed:** 92 files (rev 1-100 consecutive, samples at 150, 200, 500, 1000, 1500, 1843, 1999, 2005)

## Summary

The Google Sheets revision history for ubl25_library contains **2,005 revisions**.
Analysis of the first 100 consecutive revisions reveals that:

1. **Real edits are tiny** — typically 0-2 cells changed per revision
2. **"Massive" diffs are artifacts** of column/row insertion shifting data positions
3. **One worksheet** ("CommonLibrary") for rev 1-~1200, then a **second sheet** ("Logs-sheet") appears
4. **Formulas** use OpenFormula syntax with absolute column references that shift on insert

## Change Categories

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

## Quantitative Summary (rev 1-100)

| Metric | Count |
|--------|-------|
| Total transitions analyzed | 85 |
| Transitions with zero changes (text-only) | 39 (46%) |
| Transitions with 1-2 cell changes | 40 (47%) |
| Transitions with row/col insertion artifacts | 6 (7%) |
| **Real text edits** (across all 100 revisions) | **~50 cells** |

## Key Insight: ODS Export Non-Determinism

The ODS export from Google Sheets is **not deterministic**:
- Same logical sheet state → different ODS XML
- Column insertion changes formula text (reference shifts)
- Row insertion shifts all data positions
- These produce massive apparent diffs that are pure artifacts

For meaningful comparison, diffs must be:
1. **Header-aware** (match by column name, not position)
2. **Content-hash based** (compare text, ignore formula references)
3. **Row-identity based** (match by Component Name, not row number)

## Worksheet Evolution (full range)

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

## Scripts

- `work-sheets/scripts/download-drive-revisions.py` — Download .ods.gz from public Drive folder
- `work-sheets/scripts/diff-ods-revisions.py` — Position-based ODS diff (initial analysis)
- Inline scripts in this session for header-aware and text-only diffs

## Next Steps

1. Build a row-identity-aware diff (match by Component Name + row context)
2. Extend analysis to rev 100-2005 to find all real editorial milestones
3. Cross-reference with OASIS release dates to identify which revisions
   correspond to formal committee draft stages
4. Analyze the Logs-sheet for Apps Script execution patterns
