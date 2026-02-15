# UBL 2.5 Workflow Build Timeline Analysis

**Generated:** 2026-02-15
**Data source:** 55 workflow log files from `/home/user/ubl-artifacts/logs/`
**Cross-referenced with:** `/tmp/all-available-runs.tsv` (76 total runs: 55 successful, 21 cancelled)

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total successful runs analyzed | 55 |
| Total cancelled runs (no logs) | 21 |
| Date range | 2025-11-17 to 2026-02-09 (85 days) |
| Branches used | 6 (`ubl-2.5`, `ubl-2.5-python`, `ubl-2.5-2025-layout`, `kentest`, `server-test`, `ubl-2.5-retry`) |
| Stage labels | 2 (`csd02`, `csd03`) |
| All builds successful | Yes (all 55 = BUILD_OK) |
| Runs with HUB-SKIPPED | 17 |
| Runs with NDR FAIL | 12 |
| Runs with XSLT_ERROR | 47 |
| Runs with clean NDR (PASS, no XSLT error) | 0 |

---

## Distinct ODS Size Snapshots

The Google Sheets ODS source files changed **8 times** across the 55 runs. Each row below represents a distinct combination:

| # | First seen | Sig bytes | Lib bytes | Doc bytes | Runs |
|---|-----------|-----------|-----------|-----------|------|
| 1 | 2025-11-17 | 16,388 | 639,453 | 911,943 | 5 (runs 1-5) |
| 2 | 2025-11-19 | 16,387 | 640,288 | 912,139 | 1 (run 6) |
| 3 | 2025-11-19 | 16,387 | 640,302 | 912,166 | 4 (runs 7-10) |
| 4 | 2025-11-20 | 16,387 | 640,302 | 930,888 | 18 (runs 11-28) |
| 5 | 2025-11-21 | 16,387 | 640,604 | 931,654 | 1 (run 29) |
| 6 | 2025-12-03 | 16,388 | 640,633 | 931,737 | 2 (runs 30-31) |
| 7 | 2026-01-10 | 16,389 | 640,634 | 931,769 | 2 (runs 32-33) |
| 8 | 2026-01-10 | 16,389 | 640,634 | 931,756 | 4 (runs 34-37) |
| 9 | 2026-01-15 | 16,388 | 640,701 | 931,858 | 3 (runs 38-39, 45-48) |
| 10 | 2026-01-21 | 16,388 | 640,651 | 931,743 | 1 (run 40) |
| 11 | 2026-01-21 | 16,388 | 640,701 | 931,743 | 4 (runs 41-44) |
| 12 | 2026-01-21 | 16,388 | 640,701 | 931,858 | 5 (runs 45-48) |
| 13 | 2026-01-28 | 16,389 | 640,701 | 931,871 | 1 (run 49) |
| 14 | 2026-02-09 | 16,389 | 640,703 | 931,924 | 7 (runs 50-55) |

### Key ODS Change Points

1. **2025-11-19 (run 6):** First Library+Documents ODS size change.
   - Signature: 16,388 -> 16,387 (-1 byte)
   - Library: 639,453 -> 640,288 (+835 bytes)
   - Documents: 911,943 -> 912,139 (+196 bytes)

2. **2025-11-20 (run 11):** **Major Documents ODS jump** -- the biggest single change.
   - Documents: 912,166 -> 930,888 (+18,722 bytes, +2.1%)
   - This correlates with the first appearance of NDR FAIL(2) errors.

3. **2025-11-21 (run 29):** Incremental Library+Documents growth.
   - Library: 640,302 -> 640,604 (+302 bytes)
   - Documents: 930,888 -> 931,654 (+766 bytes)

4. **2025-12-03 (runs 30-31):** Minor across-the-board changes after 13-day gap.
   - All three files changed slightly.

5. **2026-01-10 (runs 32-37):** Two sub-changes on same day.
   - Documents briefly at 931,769 then drops to 931,756 (-13 bytes).

6. **2026-01-15 to 2026-01-21:** Library stabilizes at 640,701.
   - Documents oscillates between 931,743 and 931,858 across branches.

7. **2026-02-09 (csd03 era):** Final sizes.
   - Signature: 16,389 (+1 from initial)
   - Library: 640,703 (+1,250 from initial, +0.20%)
   - Documents: 931,924 (+19,981 from initial, +2.19%)

### ODS Size Trends (net change over 85 days)

| File | Initial | Final | Delta | % Change |
|------|---------|-------|-------|----------|
| UBL-Signature-Google.ods | 16,388 | 16,389 | +1 | +0.006% |
| UBL-Library-Google.ods | 639,453 | 640,703 | +1,250 | +0.20% |
| UBL-Documents-Google.ods | 911,943 | 931,924 | +19,981 | +2.19% |

The Documents ODS grew the most, with the vast majority of that growth (+18,722 bytes) happening in a single change on 2025-11-20.

---

## NDR Check Status Evolution

The NDR (Naming and Design Rules) check has three observable states:

1. **XSLT_ERROR** -- The NDR check XSLT stylesheet (`Crane-checkgc4obdndr.xsl`) crashes with "Error at char 208" when comparing against the previous stage's `.gc` file (csd01). This masks the actual NDR result. The check against `UBL-Entities-2.4-os.gc` runs successfully.

2. **FAIL(N)+XSLT_ERROR** -- Same XSLT error, but the check against 2.4 also finds N errors.

3. **FAIL(N)** -- The XSLT error is **fixed** (the `csd01.gc` comparison file presumably now exists or is valid). The actual NDR error count is revealed.

### NDR Timeline

| Phase | Dates | NDR Status | Notes |
|-------|-------|------------|-------|
| Runs 1-10 | Nov 17-20 | XSLT_ERROR only | csd01 .gc file missing/invalid; NDR check crashes |
| Runs 11-13 | Nov 20 | FAIL(2)+XSLT_ERROR | Documents ODS jump introduces 2 NDR violations; XSLT still crashes on csd01 comparison |
| Runs 14-39 | Nov 20 - Jan 15 | XSLT_ERROR only | NDR errors appear to be fixed (2.4 comparison passes), but csd01 crash persists |
| Runs 40-44 | Jan 21 | FAIL(5)+XSLT_ERROR | 5 NDR errors detected on 2.4 comparison; csd01 XSLT crash persists. HUB-SKIPPED. |
| Run 45 | Jan 21 | FAIL(6) | **XSLT error fixed!** 6 errors on Entities csd01 comparison + 9 on Endorsed csd01 comparison (both with 2.4-os too). No XSLT crash. |
| Runs 46-48 | Jan 21 | XSLT_ERROR | Different branch (kentest/retry) reverts to old build config with XSLT crash |
| Run 49 | Jan 28 | FAIL(6) | Same as run 45 -- NDR errors present, no XSLT crash |
| Runs 50-54 | Feb 9 | XSLT_ERROR | csd03 stage, HUB-SKIPPED runs, XSLT crash returns (now comparing against csd02) |
| Run 55 | Feb 9 | FAIL(5) | Final full build: 5 NDR errors on csd02 comparison, no XSLT crash |

### NDR Error Count Details (for runs without XSLT masking)

| Run ID | Date | Entities vs csd-prev | Entities vs 2.4-os | Endorsed vs csd-prev | Endorsed vs 2.4-os |
|--------|------|---------------------|--------------------|--------------------|-------------------|
| 19539148917 | Nov 20 | (XSLT crash) | 2 errors | (XSLT crash) | 2 errors |
| 21222855543 | Jan 21 | 6 errors | (pass) | 9 errors | (pass) |
| 21446440445 | Jan 28 | 6 errors | (pass) | 9 errors | (pass) |
| 21830603834 | Feb 9 | 5 errors | (pass) | 5 errors | (pass) |

The shift from 6+9 errors (csd02 vs csd01) to 5+5 errors (csd03 vs csd02) suggests some NDR issues were fixed in the csd02->csd03 transition.

---

## Stage Label Transition: csd02 to csd03

| Stage | Date Range | Run Count | ODS Sizes (Doc) |
|-------|-----------|-----------|-----------------|
| **csd02** | 2025-11-17 to 2026-01-28 | 49 runs | 911,943 -> 931,871 |
| **csd03** | 2026-02-09 | 7 runs | 931,924 |

The transition from csd02 to csd03 happened between 2026-01-28 and 2026-02-09, after 49 builds over 73 days on csd02.

---

## Branch History

### 1. `ubl-2.5-python` (3 runs, Nov 17)

The earliest runs. Used a **dual build** system running both Python (`build-py`) and Ant (`build`) jobs in parallel. This was the experimental Python toolchain branch. The first two runs had `HUB-SKIPPED` (no spec-to-PDF submission); the third run (19443524617) was the first to successfully submit to `OASIS-2020-spec2pdfhtml`.

### 2. `ubl-2.5` (42 runs, Nov 17 - Feb 9)

The primary development branch. Most active on Nov 20 (16 runs in one day, including 10 runs in a 17-minute burst from 17:12 to 17:30). This intense activity suggests rapid iteration on build configuration, likely related to the intermediate support file count stabilizing around 6094.

### 3. `ubl-2.5-2025-layout` (7 runs, Jan 10 - Jan 15)

A branch for experimenting with the 2025 OASIS document layout. First branch to use the new `OASIS-2025-specnote2pdfhtml` spec server (run 20870610205, Jan 10). The intermediate support file count jumped to 6192 (from 6094) reflecting additional layout-related artefacts.

### 4. `kentest` (5 runs, Jan 21)

Testing branch. Runs 21218439446-21221543384 all had `HUB-SKIPPED` with `FAIL(5)+XSLT_ERROR`. Later runs (21224641487, 21225083874) switched to the new spec server and reverted to XSLT_ERROR only (possibly a different build configuration).

### 5. `server-test` (1 run, Jan 21)

Single test run (21222373700). Had `FAIL(5)+XSLT_ERROR` and `HUB-SKIPPED`. Appears to be a quick test of server connectivity.

### 6. `ubl-2.5-retry` (1 run, Jan 21)

A retry run (21226225406) using the old `spec2pdfhtml` server. Had `XSLT_ERROR` only (not FAIL), suggesting it used an older build configuration.

---

## Spec-to-PDF Server Transition

| Server | First Use | Last Use | Runs Using It |
|--------|-----------|----------|---------------|
| `OASIS-2020-spec2pdfhtml-ISO-pdfdocx` | 2025-11-17 (run 3) | 2026-01-21 (run 48) | 20 |
| `OASIS-2025-specnote2pdfhtml-ISO-pdfdocx` | 2026-01-10 (run 34) | 2026-02-09 (run 55) | 8 |
| Neither (no submission / HUB-SKIPPED) | throughout | throughout | 27 |

The old 2020 server was used exclusively until January 10, 2026. Starting Jan 10 on the `ubl-2.5-2025-layout` branch, the new 2025 server (`specnote2pdfhtml`) was introduced. From Jan 21 onward, the two servers coexisted briefly: runs on `ubl-2.5` and `ubl-2.5-retry` used the old server, while `kentest` runs used the new one. By Jan 28, the new server appears to have become the default.

---

## Artefact File Counts

Three distinct tiers of artefact sizes emerged:

| Tier | Artefact Files | Intermediate Files | When | Context |
|------|---------------|-------------------|------|---------|
| Minimal | 242-243 | 4,527-4,635 | HUB-SKIPPED runs | Incomplete builds (no PDF/hub) |
| Standard (early) | 661 | 5,745 | Nov 17 (python branch) | Early dual-build config |
| Standard (mid) | 765-775 | 6,052-6,100 | Nov 17-Nov 20+ | Full builds, 765->775 at run 14 |
| Extended | 775 | 6,192-6,204 | Jan 10+ (2025-layout) | Additional layout artefacts |

The intermediate support file count trend: 5,745 -> 6,052 -> 6,082 -> 6,086 -> 6,090 -> 6,094 (stabilized) -> 6,192 (2025-layout) -> 6,198/6,204 (final csd03).

---

## Cancelled Runs

21 runs were cancelled without producing logs:

1. **2025-12-03 cluster:** 11 cancelled runs between 12:32-12:39, followed by 1 success at 12:39. Suggests rapid retry behavior (perhaps manual re-triggering after fixing an issue).

2. **2026-02-09 cluster:** 10 cancelled runs between 14:34-15:08, bracketing 6 successful HUB-SKIPPED runs. The csd03 transition day had significant churn.

---

## Development Eras (Chronological Phases)

### Era 1: Python Toolchain Exploration (Nov 17, runs 1-3)
- Branch: `ubl-2.5-python`
- Dual build (Python + Ant)
- ODS sizes: initial values (Sig=16,388, Lib=639,453, Doc=911,943)
- NDR: XSLT crashes only
- First successful spec submission on run 3

### Era 2: Early csd02 Development (Nov 17-19, runs 4-10)
- Branch: `ubl-2.5` established
- Python branch abandoned
- ODS files begin changing (Library growing)
- NDR: XSLT crashes only (masking real errors)
- Artefact count: 765 files, 6,052 intermediate

### Era 3: Documents ODS Major Update (Nov 20, runs 11-28)
- **Big event:** Documents ODS jumps by 18,722 bytes (912K -> 931K)
- NDR briefly shows FAIL(2) then returns to XSLT-only
- Artefact count bumps to 775 files
- 16 runs in one day (Nov 20), including a 10-run burst in 17 minutes
- Intermediate files fluctuate before stabilizing at 6,094

### Era 4: Stable csd02 Builds (Nov 21 - Dec 3, runs 29-31)
- Only 3 runs over 13 days -- development pace slows
- ODS files show minor incremental changes
- NDR: XSLT crashes only
- No missing file warnings resolve

### Era 5: 2025 Layout Experimentation (Jan 10-15, runs 32-38)
- Branch: `ubl-2.5-2025-layout`
- Introduction of new `specnote2pdfhtml` submission server
- Intermediate files jump to 6,192
- 7 runs testing the new layout

### Era 6: Server Testing & NDR Fix (Jan 21, runs 39-48)
- Multiple branches active: `ubl-2.5`, `kentest`, `server-test`, `ubl-2.5-retry`
- **Key event:** XSLT error is fixed in some configurations (runs 45, 49)
- NDR errors now visible: 6 (Entities) + 9 (Endorsed) against csd01
- HUB-SKIPPED runs alternate with full builds
- Spec server: mixed old and new

### Era 7: Final csd02 (Jan 28, run 49)
- Last csd02 build
- FAIL(6): 6 NDR errors on Entities, 9 on Endorsed
- Documents ODS: 931,871 bytes

### Era 8: csd03 Transition (Feb 9, runs 50-55)
- **Stage label changes to csd03**
- 10 cancelled + 6 HUB-SKIPPED + 1 full build
- NDR errors improve: 5+5 (down from 6+9)
- Documents ODS reaches final size: 931,924
- New spec server (`specnote2pdfhtml`) is now the standard
- Intermediate files reach 6,204 (highest ever)

---

## Notable Observations

1. **No run ever had fully clean NDR.** Every single run had either XSLT crashes or actual NDR errors. The "PASS" in the simplified TSV (earlier version) was misleading -- it meant "no errors detected" but the XSLT crash was masking the result.

2. **The XSLT crash is a tooling bug, not a spec issue.** It occurs when comparing against the previous committee stage draft (csd01 for csd02 builds, csd02 for csd03 builds). The comparison against 2.4-os works fine. The error "Error at char 208 in xsl:param/@select on line 48" suggests a file-not-found or parsing issue with the old .gc file.

3. **ODS sizes are a proxy for Google Sheets editing activity.** The files are downloaded live from Google Sheets during each build. Size changes indicate someone edited the source spreadsheets.

4. **The 4 missing files are persistent.** From run 5 onward, 4 `old2newDocBook` XML files are consistently missing, suggesting a build configuration issue that was never resolved.

5. **The Nov 20 burst of 16 runs** (with 10 in 17 minutes) suggests automated or semi-automated testing of build configuration changes, likely related to the artefact count and intermediate file count changes.

6. **csd03 is clearly an early/incomplete stage** at the time of this analysis. Only 1 of 7 runs produced a full build (the rest were HUB-SKIPPED), and significant cancelled-run churn preceded it.

7. **The Documents ODS grew 2.19%** while the Signature ODS barely changed (+1 byte net). This is consistent with active document-level development while the signature model remained stable.

---

## Appendix: Complete Run Inventory

See `complete-timeline.tsv` for the full tab-separated dataset with all 55 runs.

### Column Definitions

| Column | Description |
|--------|-------------|
| `run_id` | GitHub Actions workflow run ID |
| `datetime` | ISO 8601 timestamp when the run started |
| `branch` | Git branch the workflow ran on |
| `stage_label` | OASIS committee stage (csd02 or csd03) |
| `sig_ods_bytes` | Size of UBL-Signature-Google.ods downloaded during build |
| `lib_ods_bytes` | Size of UBL-Library-Google.ods downloaded during build |
| `doc_ods_bytes` | Size of UBL-Documents-Google.ods downloaded during build |
| `ndr_result` | NDR check outcome: XSLT_ERROR, FAIL(N), FAIL(N)+XSLT_ERROR |
| `notes` | Semicolon-separated metadata (build result, hub status, spec server, file counts) |
