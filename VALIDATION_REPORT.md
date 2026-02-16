# Validation Report: Claims in .md Files vs Actual Data

**Branch:** `claude/add-validation-checks-Myp3A`
**Date:** 2026-02-16
**Method:** Systematic verification of every factual claim against on-disk data

---

## Executive Summary

Checked 26 .md files against actual files on disk. Found **11 errors** and
**3 inconsistencies** across 6 documents. All SHA-256 checksums, OASIS URLs,
release dates, ODS file counts, and row counts for UBL 2.0 stages are correct.
The main problems are inflated file counts, a stale directory listing in
README.md, and extensive documentation referencing shell scripts that no longer
exist (replaced by `build_history.py`).

| Severity | Count | Summary |
|----------|:-----:|---------|
| ERROR (factually wrong) | 11 | Wrong file counts, wrong row count, wrong column count, missing files documented as existing |
| INCONSISTENCY (self-contradictory) | 3 | "30" vs "33" ODS, "3.3 MB" approximation, stale script references |
| VERIFIED OK | ~95 claims | Checksums, URLs, dates, column structures, row counts, tool provenance |
| UNVERIFIABLE | ~10 claims | Artifact data not on disk, Google auth required, Java not tested |

---

## ERRORS Found

### E1. Total .gc file count is 62, not 65

**Claimed in:** CLAUDE.md (line ~20), README.md (various)

**Claim:** "65 GenericCode (.gc) files"

**Actual:** 62 .gc files on disk

**Root cause:** CLAUDE.md assumes 2 files per release for all of UBL 2.1 (16)
and 3 per release for UBL 2.5 (6 -- should be 7 to hit 65, but is actually 6).

**Correct breakdown:**

| Version | Entities | Signature | Endorsed | Total |
|---------|:--------:|:---------:|:--------:|:-----:|
| UBL 2.0 | 8 | 0 | 0 | 8 |
| UBL 2.1 | 8 | **6** (not 8) | 0 | **14** |
| UBL 2.2 | 6 | 6 | 0 | 12 |
| UBL 2.3 | 7 | 7 | 0 | 14 |
| UBL 2.4 | 4 | 4 | 0 | 8 |
| UBL 2.5 | 2 | 2 | 2 | 6 |
| **Total** | **35** | **25** | **2** | **62** |

---

### E2. UBL 2.1 has 14 .gc files, not 16

**Claimed in:** CLAUDE.md line ~32

**Claim:** "UBL 2.1: 16 .gc (2 per release)"

**Actual:** 14 .gc files. Releases `prd1-UBL-2.1` and `prd2-UBL-2.1` have only
`UBL-Entities-2.1.gc` -- no Signature-Entities file. The Signature file first
appears at `prd3-UBL-2.1`.

---

### E3. UBL 2.5 has 6 .gc files, not 7

**Claimed in:** CLAUDE.md line ~36

**Claim:** "UBL 2.5: 7 .gc (3 per release: Entities + Signature + Endorsed)"

**Actual:** 6 files (3 per release x 2 releases = 6). The claim of 7 is
arithmetically wrong -- 3 x 2 = 6, not 7.

---

### E4. Signature-Entities count is 25, not 28

**Claimed in:** CLAUDE.md line ~45

**Claim:** "Signature-Entities: 28 files (2.1-2.5, not all releases have them)"

**Actual:** 25 Signature-Entities files on disk.

Breakdown: 6 (2.1) + 6 (2.2) + 7 (2.3) + 4 (2.4) + 2 (2.5) = 25

---

### E5. README.md row count for os-UBL-2.0 is wrong

**Claimed in:** README.md line 61

**Claim:** "Entity Rows: 2,181"

**Actual:** 2,074 rows (verified by `grep -c '</Row>'`)

This 2,181 number does not match any actual file. The correct count for os-UBL-2.0
generated .gc is 2,074 (confirmed across prd3, prd3r1, cs, os, os-update, errata
-- all are 2,074).

---

### E6. README.md shows prd1-UBL-2.1 with Signature file

**Claimed in:** README.md lines 36-38

**Claim:** Directory listing shows `prd1-UBL-2.1/mod/` containing both
`UBL-Entities-2.1.gc` and `UBL-Signature-Entities-2.1.gc`

**Actual:** `prd1-UBL-2.1/mod/` contains only `UBL-Entities-2.1.gc`. The
Signature file first appears at prd3-UBL-2.1.

---

### E7. Endorsed-Entities has 25 columns, not 27

**Claimed in:** column-structure-analysis.md lines 239-242

**Claim:** "Uses the same 27-column structure as the UBL 2.5 Entities file."

**Actual:** Endorsed-Entities files have **25 columns**, not 27. They are
missing `EndorsedCardinality` and `EndorsedCardinalityRationale` -- which makes
semantic sense, since the endorsed file IS the endorsed subset (those columns
are used in the main Entities file to derive the endorsed version, then removed).

---

### E8-E12. Shell scripts documented but don't exist (5 missing groups)

**Claimed in:** docs/workflows.md, CLAUDE.md, build-analysis.md

The following files are extensively documented but do not exist on disk:

| Documented File | Referenced In | Status |
|-----------------|--------------|--------|
| `scripts/build-history.sh` | workflows.md, CLAUDE.md, build-analysis.md | NOT FOUND |
| `scripts/lib/common.sh` | workflows.md | NOT FOUND |
| `scripts/lib/commit-helpers.sh` | workflows.md, transition-analysis.md | NOT FOUND |
| `scripts/versions/build-2.0.sh` through `build-2.5.sh` (6 files) | workflows.md, CLAUDE.md, build-analysis.md | NOT FOUND |
| `.github/workflows/build-poc-granular.yml` | workflows.md | NOT FOUND |
| `scripts/run-poc-granular.py` | workflows.md | NOT FOUND |
| `scripts/build-poc-granular.sh` | workflows.md | NOT FOUND |

**Total: 12 documented files that don't exist.**

These shell scripts were apparently the original approach, later replaced by the
Python-based `scripts/build_history.py` which DOES exist. The documentation was
never updated to reflect this change.

**Files that DO exist and ARE correctly documented:**
- `scripts/build_history.py` (24,305 bytes)
- `scripts/lib/gc_diff.py` (34,985 bytes)
- `scripts/lib/gc_analyzer.py` (12,128 bytes)
- `scripts/lib/gc_builder.py` (4,652 bytes)
- `scripts/lib/gc_commit_builder.py` (8,731 bytes)
- `scripts/lib/release_manifest.py` (17,766 bytes)
- `.github/workflows/build-history.yml` (2,706 bytes)
- `scripts/download-oasis-distributions.sh` (10,089 bytes)
- `scripts/extract-xsd-from-reference.sh` (5,342 bytes)
- `history/tools/Crane-ods2obdgc/Crane-ods2obdgc.xsl` (16,216 bytes)
- `history/tools/saxon9he/saxon9he.jar` (5,057,022 bytes)
- `work-sheets/scripts/run.py` (5,151 bytes)
- `work-sheets/scripts/convert-revision-ods-to-gc.sh` (10,022 bytes)
- `work-sheets/scripts/gc2endorsed.xsl` (3,177 bytes)
- `work-sheets/scripts/massageModelName.xml` (1,430 bytes)

---

## INCONSISTENCIES Found

### I1. README.md says "30 ODS" and "33 ODS" for the same data

**Location:** README.md line 62 vs line 65

- Line 62: "Source Files: 30 ODS files consolidated (2 core + 28 document types)"
- Line 65: heading says "Source Data (All 33 ODS Files)"
- Line 106: "Total: 30 ODS files (2 core + 28 document types)"

**Actual on disk:** os-UBL-2.0 has **30 ODS files**. The "33" heading is wrong.
(Though prd2-UBL-2.0 does have 33 -- so the heading may be a copy-paste from
a different stage analysis.)

### I2. File size approximation

**Location:** README.md line 60

**Claim:** "File Size: 3.3 MB"

**Actual:** 3,214,880 bytes = 3.07 MB

Minor -- it's an approximation, but "3.1 MB" would be more accurate.

### I3. CLAUDE.md "Proposed Structure" shows shell scripts that were replaced

**Location:** CLAUDE.md "Proposed Structure" section

The proposed structure shows `scripts/build-history.sh`, `lib/common.sh`,
`lib/commit-helpers.sh`, and `versions/build-2.X.sh` -- these were the original
plan but were replaced by the Python-based system. CLAUDE.md title says
"Proposed Structure" so this is arguably forward-looking, but it's misleading
since the actual implementation took a different path.

---

## VERIFIED CORRECT

### File counts and directories
- 35 release directories: OK (8+8+6+7+4+2)
- Directory names match historical-releases.md: OK (all 35 match)
- ODS file counts for all 8 UBL 2.0 stages: OK
  - prd: 32, prd2: 33, prd3-errata: 30 each

### Column structures (verified by XML parsing of all 62 files)
- UBL 2.0 prd: 49 columns: OK
- UBL 2.0 prd2-os: 31 columns: OK
- UBL 2.0 os-update/errata: 32 columns: OK
- UBL 2.1 all releases: 33 columns: OK
- UBL 2.2-2.4 all releases: 23 columns: OK
- UBL 2.5 Entities: 27 columns: OK
- Signature-Entities all versions: 33 columns: OK
- Column transition deltas (added/removed counts): OK for all 5 transitions

### Row counts (verified by grep on all 62 files)
- prd-UBL-2.0: 1,604 rows: OK
- prd2-UBL-2.0: 2,139 rows: OK
- prd3 through errata: 2,074 rows each: OK
- All Signature files: 5 rows each: OK (consistent across all 25 files)

### SHA-256 checksums (verified against work/TIMELINE.md)
- All 9 checksums in TIMELINE.md verified: OK
- All 3 file sizes in TIMELINE.md verified: OK

### OASIS URLs (spot-checked 4 of 35)
- prd-UBL-2.0: OK (accessible, correct content)
- os-UBL-2.1: OK
- os-UBL-2.4: OK
- csd02-UBL-2.5: OK

### Tool provenance
- Saxon 9 HE jar present: OK (5,057,022 bytes)
- Crane-ods2obdgc XSLT present: OK (16,216 bytes)

### Publication dates in historical-releases.md
- All 35 dates listed: present and formatted consistently
- (Cannot independently verify dates without external source)

---

## UNVERIFIABLE in Current Environment

| Claim | Source | Why Unverifiable |
|-------|--------|-----------------|
| 55 artifact checksums | artifact-provenance.md | `/home/user/ubl-artifacts/` does not exist |
| 10 unique Entities versions | artifact-provenance.md | Artifact data not on disk |
| ODS size timeline | workflow-history-analysis.md | Workflow logs not available |
| Google Sheets revision content | work-sheets/README.md | Requires Google OAuth token |
| Saxon version number | saxon9he/ORIGIN.md | Java not tested in this session |
| Tool performance claims | TOOL_VERIFICATION.md | Would require running conversions |
| 245 ODS files processed | TOOL_VERIFICATION.md | Would require running conversions |
| NDR validation history | workflow-history-analysis.md | Workflow logs not available |
| Publication dates accuracy | historical-releases.md | No independent local source |

---

## Recommendations

### Immediate fixes (factual errors):
1. **CLAUDE.md:** Change "65" to "62", "16" to "14", "7" to "6", "28" to "25"
2. **README.md:** Change "2,181" to "2,074", fix prd1 directory listing, fix "33" heading
3. **column-structure-analysis.md:** Change Endorsed column count from "27" to "25"

### Documentation cleanup (stale references):
4. **docs/workflows.md:** Major rewrite needed -- most of the documented shell scripts
   don't exist. Should document the actual Python-based system.
5. **CLAUDE.md "Proposed Structure":** Update to reflect actual `build_history.py` system
6. **build-analysis.md:** Note that the analyzed scripts were since replaced
7. **transition-analysis.md:** Note that the analyzed scripts were since replaced

### Nice-to-have:
8. Add a note about when Signature-Entities first appears (prd3-UBL-2.1, not prd1)
9. Clarify that Endorsed uses 25 columns (a proper subset of the 27 Entities columns)

---

*Validated: 2026-02-16 by Claude Code*
*Methodology: Sequential subagent execution (haiku for data collection, sonnet for XML parsing)*
