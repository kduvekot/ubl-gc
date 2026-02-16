# Validation Plan: Verify All Claims in .md Files

**Branch:** `claude/add-validation-checks-Myp3A`
**Created:** 2026-02-16
**Status:** IN PROGRESS

---

## Goal

Systematically verify every factual claim made in the 26 .md files in this
repository against the actual data on disk. Flag discrepancies, correct
documentation where wrong, and note claims that cannot be verified.

---

## Source Files to Validate (26 .md files)

| # | File | Key Claims |
|---|------|-----------|
| 1 | `README.md` | File counts, version coverage, row counts, tool info |
| 2 | `CLAUDE.md` | 65 files, 35 releases, version breakdown table, directory structure |
| 3 | `ARCHITECTURE.md` | Design decisions, data source descriptions |
| 4 | `docs/historical-releases.md` | 35 releases, dates, stage names, directory names |
| 5 | `docs/column-structure-analysis.md` | Column lists per version, column counts, transition deltas |
| 6 | `docs/genericcode-format.md` | GenericCode XML structure |
| 7 | `docs/workflows.md` | Workflow structure, commit counts, script descriptions |
| 8 | `docs/artifact-provenance.md` | SHA-256 checksums, 10 versions, artifact inventory |
| 9 | `docs/workflow-history-analysis.md` | ODS sizes, version counts, NDR history |
| 10 | `docs/intermediate-versions.md` | Intermediate version claims |
| 11 | `docs/timeline-analysis.md` | Timeline claims |
| 12 | `docs/workflow-artifact-analysis.md` | Artifact analysis claims |
| 13 | `history/README.md` | Directory structure, file counts, ODS file counts, row counts |
| 14 | `history/tools/README.md` | Tool documentation |
| 15 | `history/tools/CONVERSION_GUIDE.md` | Conversion parameters, expected outputs |
| 16 | `history/tools/TOOL_VERIFICATION.md` | 245 ODS files, 100% success, performance |
| 17 | `history/tools/Crane-ods2obdgc/ORIGIN.md` | Tool provenance |
| 18 | `history/tools/saxon9he/ORIGIN.md` | Saxon provenance, row counts per stage |
| 19 | `history/tools/saxon9he/README.md` | Saxon capabilities |
| 20 | `history/tools/scripts/README.md` | Script documentation |
| 21 | `scripts/README.md` | Build script descriptions, 35 releases, 3 file types |
| 22 | `build-analysis.md` | Build process analysis |
| 23 | `transition-analysis.md` | File accumulation bug, git mv issues |
| 24 | `claude-memory-bug-report.md` | Tool bug report (informational, less critical) |
| 25 | `work/TIMELINE.md` | Artifact-to-history mapping, SHA-256 checksums |
| 26 | `work-sheets/README.md` | Google Sheets IDs, revision structure, ODS files |

---

## Validation Categories

### Category A: File Counts & Directory Structure (HIGH PRIORITY)

Claims that can be verified by listing files on disk.

| Claim | Source | How to Verify |
|-------|--------|--------------|
| "65 GenericCode files" | CLAUDE.md, README.md | `find history -name "*.gc" \| wc -l` |
| "35 releases" | CLAUDE.md, historical-releases.md | Count release directories |
| "8 UBL 2.0 releases" | CLAUDE.md | Count dirs in `history/generated/` |
| "8 UBL 2.1 releases" | CLAUDE.md | Count `*-UBL-2.1/` dirs |
| "6 UBL 2.2 releases" | CLAUDE.md | Count `*-UBL-2.2/` dirs |
| "7 UBL 2.3 releases" | CLAUDE.md | Count `*-UBL-2.3/` dirs |
| "4 UBL 2.4 releases" | CLAUDE.md | Count `*-UBL-2.4/` dirs |
| "2 UBL 2.5 releases" | CLAUDE.md | Count `*-UBL-2.5/` dirs |
| "UBL 2.0: 8 generated .gc" | CLAUDE.md | Count .gc in `history/generated/` |
| "UBL 2.1: 16 .gc (2 per release)" | CLAUDE.md | Count .gc in `*-UBL-2.1/` dirs |
| "UBL 2.2: 12 .gc" | CLAUDE.md | Count .gc in `*-UBL-2.2/` dirs |
| "UBL 2.3: 14 .gc" | CLAUDE.md | Count .gc in `*-UBL-2.3/` dirs |
| "UBL 2.4: 8 .gc" | CLAUDE.md | Count .gc in `*-UBL-2.4/` dirs |
| "UBL 2.5: 7 .gc (3 per release)" | CLAUDE.md | Count .gc in `*-UBL-2.5/` dirs |
| "30 ODS files per release" | history/README.md | Count ODS in `history/os-UBL-2.0/mod/` etc. |
| Directory names match docs | historical-releases.md | Compare listed dirs vs actual dirs |
| `work-sheets/revision-ods/` structure | work-sheets/README.md | List actual files |

**Subagent strategy:** One `haiku` agent per version to count files. Run all 6 in parallel.

### Category B: Column Structure Claims (HIGH PRIORITY)

Claims about XML column structure that require parsing .gc files.

| Claim | Source | How to Verify |
|-------|--------|--------------|
| UBL 2.0 prd: 49 columns | column-structure-analysis.md | Parse XML of generated/prd-UBL-2.0 |
| UBL 2.0 prd2-os: 31 columns | column-structure-analysis.md | Parse XML |
| UBL 2.0 os-update/errata: 32 columns | column-structure-analysis.md | Parse XML |
| UBL 2.1: 33 columns (all 8 releases) | column-structure-analysis.md | Parse XML of all 8 |
| UBL 2.2-2.4: 23 columns | column-structure-analysis.md | Parse XML |
| UBL 2.5: 27 columns | column-structure-analysis.md | Parse XML |
| Signature-Entities: 33 columns always | column-structure-analysis.md | Parse XML |
| Endorsed-Entities: 27 columns | column-structure-analysis.md | Parse XML |
| Specific column names per version | column-structure-analysis.md | Extract column IDs from XML |
| Column transition deltas | column-structure-analysis.md | Diff column sets |

**Subagent strategy:** One `sonnet` agent to write a Python script that extracts column IDs from all 62 .gc files, then verify against the documented lists. Sonnet because it needs to understand GenericCode XML structure and write correct parsing code.

### Category C: Row Counts (MEDIUM PRIORITY)

| Claim | Source | How to Verify |
|-------|--------|--------------|
| prd-UBL-2.0: 1,604 rows | history/README.md, saxon9he/ORIGIN.md | Count `<Row>` elements |
| prd2-UBL-2.0: 2,139 rows | history/README.md | Count `<Row>` elements |
| prd3-os: 2,074 rows | history/README.md | Count `<Row>` elements |
| "32 ODS (29+3)" for prd | history/README.md | Count ODS files |
| "33 ODS (31+2)" for prd2 | history/README.md | Count ODS files |

**Subagent strategy:** One `haiku` agent to count `<Row>` elements in all 62 .gc files using grep.

### Category D: SHA-256 Checksums (MEDIUM PRIORITY)

| Claim | Source | How to Verify |
|-------|--------|--------------|
| CSD02 Entities = V5 (`fa9822e1...`) | work/TIMELINE.md | `sha256sum` on disk file |
| CSD02 Signature = V1 (`1104e269...`) | work/TIMELINE.md | `sha256sum` on disk file |
| CSD02 Endorsed = V5 (`0c9365e9...`) | work/TIMELINE.md | `sha256sum` on disk file |
| CSD01 Entities = csd01-ref V2 (`4ad8dd25...`) | work/TIMELINE.md | `sha256sum` on disk file |
| CSD01 Endorsed = csd01-ref V2 (`9206aafb...`) | work/TIMELINE.md | `sha256sum` on disk file |
| V1-original checksums | work/TIMELINE.md | Check work/gc-versions/csd01-ref/ |

**Note:** The `/home/user/ubl-artifacts/` directory does NOT exist in this environment, so the full 55-artifact inventory from `artifact-provenance.md` CANNOT be verified. We can only verify the checksums for files still on disk in `history/` and `work/`.

**Subagent strategy:** One `haiku` agent to run sha256sum on all relevant files and compare.

### Category E: Script & Workflow Claims (LOW-MEDIUM PRIORITY)

| Claim | Source | How to Verify |
|-------|--------|--------------|
| `build_history.py` exists and has described flags | scripts/README.md | Read the actual script |
| `gc_diff.py`, `gc_analyzer.py` etc. exist | scripts/README.md | Check files exist |
| `.github/workflows/build-history.yml` structure | docs/workflows.md | Read actual workflow |
| Workflow trigger paths match docs | docs/workflows.md | Compare |
| Script functions exist as documented | docs/workflows.md | Grep for function names |

**Subagent strategy:** One `haiku` agent to verify file existence and grep for documented functions/flags.

### Category F: External URL Claims (UNVERIFIABLE / LOW PRIORITY)

| Claim | Source | How to Verify |
|-------|--------|--------------|
| OASIS URLs for 35 releases | historical-releases.md | WebFetch (sampling only) |
| Google Sheet IDs | work-sheets/README.md | Cannot verify without auth |
| Google Drive folder URL | work-sheets/README.md | Cannot verify without auth |

**Subagent strategy:** One `haiku` agent to spot-check 3-5 OASIS URLs via WebFetch. We won't check all 35 -- just enough to confirm the URL pattern is valid.

### Category G: Cross-Document Consistency (HIGH PRIORITY)

Multiple documents make overlapping claims. Check for contradictions.

| Check | Files Involved |
|-------|---------------|
| File count: 65 vs actual | CLAUDE.md, README.md, historical-releases.md |
| Release count: 35 vs actual | CLAUDE.md, historical-releases.md, scripts/README.md |
| Version breakdown totals add up | CLAUDE.md table vs actual |
| Column counts consistent | column-structure-analysis.md vs genericcode-format.md |
| Row counts consistent | history/README.md vs saxon9he/ORIGIN.md vs TOOL_VERIFICATION.md |
| Transition analysis matches column analysis | transition-analysis.md vs column-structure-analysis.md |
| Workflow docs match actual workflow files | docs/workflows.md vs .github/workflows/ |

**Subagent strategy:** Done in the main thread by comparing results from Categories A-E.

---

## Subagent Execution Plan

### Phase 1: Data Collection (parallel)

Launch 5 agents simultaneously to collect raw facts from disk:

| Agent | Type | Model | Task | Est. Turns |
|-------|------|-------|------|-----------|
| **A1** | Bash | haiku | Count all .gc files by version, count release dirs, count ODS files | 5 |
| **A2** | general-purpose | sonnet | Write+run Python to extract column IDs from all 62 .gc files | 8 |
| **A3** | Bash | haiku | Count `<Row>` elements in all .gc files via grep | 5 |
| **A4** | Bash | haiku | SHA-256 checksums of all .gc files in history/ and work/ | 3 |
| **A5** | Bash | haiku | Verify script/workflow file existence, grep for documented functions | 5 |

### Phase 2: Cross-Reference (sequential, main thread)

Using results from Phase 1:
1. Compare actual file counts vs all documented counts
2. Compare actual column structures vs documented structures
3. Compare actual row counts vs documented row counts
4. Compare actual checksums vs documented checksums
5. Compare actual scripts vs documented scripts
6. Check for contradictions between documents

### Phase 3: URL Spot-Check (optional, parallel)

| Agent | Type | Model | Task |
|-------|------|-------|------|
| **A6** | general-purpose | haiku | Spot-check 3-5 OASIS URLs from historical-releases.md |

### Phase 4: Report & Fix (sequential, main thread)

1. Write `VALIDATION_REPORT.md` with all findings
2. Fix any incorrect claims in .md files (Edit tool)
3. Update this plan with completion status
4. Commit and push

---

## What We CANNOT Verify

These claims reference data not available in this environment:

1. **55 artifact checksums** (artifact-provenance.md) -- `/home/user/ubl-artifacts/` does not exist
2. **Google Sheets revision content** -- requires Google OAuth token
3. **Historical workflow logs** -- expired from GitHub (>90 days)
4. **Publication dates** -- we trust OASIS metadata; no local source to cross-check
5. **Tool version specifics** (Saxon "9.x.x") -- would need `java -jar saxon9he.jar -version` but Java may not be installed
6. **GC file generation reproducibility** -- would need to re-run ODS->GC conversion

These will be noted as "unverifiable in current environment" in the report.

---

## Preliminary Finding (Before Formal Validation)

From initial reconnaissance:
- `find history -name "*.gc" | wc -l` returns **62**, not 65
- Release directories: **37** dirs found (8 generated + 29 regular), but some may not contain .gc files
- The "65 files" claim in CLAUDE.md may be wrong -- needs detailed counting

---

## Progress Tracker

| Phase | Status | Findings |
|-------|--------|----------|
| Phase 1: Data Collection | NOT STARTED | |
| Phase 2: Cross-Reference | NOT STARTED | |
| Phase 3: URL Spot-Check | NOT STARTED | |
| Phase 4: Report & Fix | NOT STARTED | |

---

*Last updated: 2026-02-16*
