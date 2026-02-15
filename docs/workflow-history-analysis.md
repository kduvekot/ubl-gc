# UBL Build Workflow History Analysis

**Date:** 2026-02-15
**Data source:** GitHub Actions workflow logs from oasis-tcs/ubl
**Coverage:** 189 total runs (Apr 2025 - Feb 2026), 55 logs analyzed in detail (Nov 17 2025 - Feb 9 2026)

---

## Executive Summary

The oasis-tcs/ubl repository uses GitHub Actions to build UBL specification packages.
The workflow downloads Google Sheets (ODS format) containing the UBL semantic model,
converts them to GenericCode (.gc) XML files, runs NDR validation, and produces
distributable 7z archives.

Analysis of 55 workflow logs spanning Nov 17 2025 to Feb 9 2026 reveals:

- **13 distinct ODS states** (Google Sheet edits) detected across 55 builds
- **7 distinct versions** of the main UBL-Entities-2.5.gc file
- The Signature Entities file was **stable for 2+ months** (only metadata change)
- **NDR failures oscillated** -- introduced, fixed, reintroduced, fixed again
- A **stage transition** from CSD02 to CSD03 occurred between Jan 21 and Feb 9
- Two new document types (**WasteMovement**, **WasteNotification**) were added Nov 20

---

## Data Availability

| Period | Runs | Logs | Artifacts | Status |
|--------|:----:|:----:|:---------:|--------|
| Apr 2025 | 18 | expired | expired | Metadata only |
| May 2025 | 1 | expired | expired | Metadata only |
| Jun 2025 | 4 | expired | expired | Metadata only |
| Jul 2025 | 15 | expired | expired | Metadata only |
| Aug 2025 | 30 | expired | expired | Metadata only |
| Oct 2025 | 45 | expired | expired | Metadata only |
| **Nov 2025** | **29** | **29** | **58 artifacts** | **Full analysis** |
| **Dec 2025** | **13** | **2** | **2** | **Full analysis** |
| **Jan 2026** | **17** | **17** | **17** | **Full analysis** |
| **Feb 2026** | **17** | **7** | **7** | **Full analysis** |

GitHub retains logs and artifacts for ~90 days. Everything before Nov 2025 is gone.

---

## Complete ODS Size Timeline

The workflow downloads three Google Sheets on every run. Size changes indicate edits.

```
Date              Time   Branch                Sig ODS  Lib ODS  Doc ODS  NDR     Notes
─────────────────────────────────────────────────────────────────────────────────────────
2025-11-17        16:37  ubl-2.5-python        16,388   639,453  911,943  PASS    Initial state
2025-11-17        22:30  ubl-2.5               16,388   639,453  911,943  PASS    Same
                                                                                  ── 2-day gap ──
2025-11-19        19:14  ubl-2.5               16,387   640,288  912,139  PASS    Customs defs updated
2025-11-19        20:51  ubl-2.5               16,387   640,302  912,166  PASS    More edits (live!)
2025-11-19        22:51  ubl-2.5               16,387   640,302  912,166  PASS    Stabilized
                                                                                  ── overnight ──
2025-11-20        10:10  ubl-2.5               16,387   640,302  912,166  PASS    Same as Nov 19
2025-11-20        13:50  ubl-2.5               16,387   640,302  930,888  FAIL(2) WasteMovement added!
                                                                                  Doc ODS +18,722 bytes
2025-11-20        14:05  ubl-2.5               16,387   640,302  930,888  PASS    NDR fix (WasteProducer spacing)
2025-11-20    17:12-19:30 ubl-2.5              16,387   640,302  930,888  PASS    12 builds, ODS unchanged
                                                                                  ── overnight ──
2025-11-21        12:41  ubl-2.5               16,387   640,604  931,654  PASS    Definition rewording
                                                                                  ── 12-day gap ──
2025-12-03        11:25  ubl-2.5               16,388   640,633  931,737  PASS    Small edits
2025-12-03        12:39  ubl-2.5               16,388   640,633  931,737  PASS    Same
                                                                                  ── 38-day gap ──
2026-01-10        00:44  ubl-2.5-2025-layout   16,389   640,634  931,769  PASS    New branch, tiny changes
2026-01-10        14:22  ubl-2.5-2025-layout   16,389   640,634  931,756  PASS    Doc ODS shrank 13 bytes
2026-01-10        17:01  ubl-2.5-2025-layout   16,389   640,634  931,756  PASS    Stabilized
                                                                                  ── 5-day gap ──
2026-01-15        20:06  ubl-2.5-2025-layout   16,388   640,701  931,858  PASS    Library jump +67 bytes
                                                                                  ── 6-day gap ──
2026-01-21        16:38  ubl-2.5               16,388   640,651  931,743  FAIL(5) NDR errors return!
2026-01-21        17:01  kentest               16,388   640,701  931,743  FAIL(5) Lib different on kentest
2026-01-21        19:26  ubl-2.5               16,388   640,701  931,858  FAIL(6) Doc changes, 6 errors
2026-01-21        20:28  kentest               16,388   640,701  931,858  PASS    NDR fixed on kentest!
2026-01-21        21:23  ubl-2.5-retry         16,388   640,701  931,858  PASS    Fix confirmed
                                                                                  ── 7-day gap ──
2026-01-28        16:25  ubl-2.5               16,389   640,701  931,871  FAIL(6) NDR errors again
                                                                                  ── 12-day gap ──
2026-02-09        14:42  ubl-2.5               16,389   640,703  931,924  PASS    CSD03 stage! Fixed
2026-02-09        15:13  ubl-2.5               16,389   640,703  931,924  FAIL(5) ...but last run fails
```

### ODS Size Summary

| File | Nov 17 (first) | Feb 9 (last) | Delta | Growth |
|------|---------------:|-------------:|------:|-------:|
| Signature ODS | 16,388 | 16,389 | +1 | ~0% |
| Library ODS | 639,453 | 640,703 | +1,250 | +0.2% |
| Documents ODS | 911,943 | 931,924 | +19,981 | +2.2% |

---

## GenericCode File Changes

### UBL-Entities-2.5.gc (main semantic model)

7 distinct versions detected across 14 downloaded artifact snapshots:

| Version | Period | Size | Delta | What Changed |
|:-------:|--------|-----:|------:|--------------|
| 1 | Nov 17 (all day) | 8,824,734 | — | Initial state |
| 2 | Nov 19 - Nov 20 10:10 | 8,829,865 | +5,131 | Customs office definitions rewritten |
| 3 | Nov 20 13:50 | 8,896,201 | +66,336 | **WasteMovement + WasteNotification added** |
| 4 | Nov 20 19:30 | 8,896,205 | +4 | NDR fix: `WasteProducer` → `Waste Producer` |
| 5 | Nov 21 - Dec 3 | 8,897,815 | +1,610 | Definition rewording (naming conventions) |
| 6 | Jan 21 | 8,898,129 | +314 | Minor definition improvements |
| 7 | Feb 9 | 8,898,129 | 0 | CSD02→CSD03 stage bump + 3 cardinality changes |

### UBL-Signature-Entities-2.5.gc

2 distinct versions:

| Version | Period | Size | What Changed |
|:-------:|--------|-----:|--------------|
| 1 | Nov 17 - Jan 21 | 13,871 | Stable for 2+ months |
| 2 | Feb 9 | 13,871 | CSD02→CSD03 metadata only |

### UBL-Endorsed-Entities-2.5.gc

7 distinct versions (mirrors Entities changes exactly -- generated from same source sheets).

---

## NDR (Naming and Design Rules) Validation History

**Important nuance:** The NDR check has three observable states:

1. **XSLT_ERROR** -- The NDR checker stylesheet (`Crane-checkgc4obdndr.xsl`) crashes
   when comparing against the previous stage's .gc file (e.g., csd01.gc for a csd02 build).
   This masks the actual NDR result. The check against UBL-2.4-os.gc runs fine.
2. **FAIL(N)+XSLT_ERROR** -- Same XSLT crash, but the 2.4 comparison also finds N errors.
3. **FAIL(N)** -- XSLT error fixed; actual NDR error count is revealed.

**No run ever had fully clean NDR.** Every single one of the 55 runs had either XSLT
crashes (47 runs) or actual NDR errors (12 runs), or both.

```
Date              NDR Status              Details
──────────────────────────────────────────────────────────────────────
Nov 17 - Nov 20   XSLT_ERROR only         csd01.gc missing/invalid; NDR crashes
Nov 20 13:50      FAIL(2)+XSLT_ERROR      WasteProducer naming error exposed
Nov 20 14:05      XSLT_ERROR only         2 errors appear fixed (2.4 comparison passes)
Nov 20 - Jan 15   XSLT_ERROR only         Stable -- but XSLT crash masks real state
Jan 21 16:38      FAIL(5)+XSLT_ERROR      5 errors vs 2.4 comparison
Jan 21 19:26      FAIL(6)                 XSLT fixed! 6 Entities + 9 Endorsed errors
Jan 21 20:28      XSLT_ERROR only         kentest branch reverts to old build config
Jan 28            FAIL(6)                 6 Entities + 9 Endorsed (no XSLT crash)
Feb 09 14:42      XSLT_ERROR only         csd03 stage -- now crashes on csd02.gc
Feb 09 15:13      FAIL(5)                 Final full build: 5+5 errors (improved!)
```

The shift from 6+9 errors (csd02 vs csd01) to 5+5 errors (csd03 vs csd02) suggests
some NDR issues were fixed in the stage transition.

---

## Stage Transition: CSD02 → CSD03

Between Jan 21 and Feb 9 2026, the build stage label changed from `csd02` to `csd03`.

Actual .gc file changes (Jan 21 → Feb 9):

1. **Metadata**: ShortName `UBL-2.5-CSD02` → `UBL-2.5-CSD03`
2. **Metadata**: LocationUri `csd02-UBL-2.5` → `csd03-UBL-2.5`
3. **Cardinality changes** (3 fields changed `0..1` → `0..n`):
   - `CatalogueItemSpecificationUpdate.ContractorCustomerParty`
   - `CataloguePricingUpdate.ContractorCustomerParty`
   - `CatalogueRequest.ReferencedContract`

---

## Significant Content Changes

### Nov 19: Customs Office Definitions Rewritten

Updated definitions for 7 customs-related locations:
- `CustomsOfficeOfEntry` - From generic to EU-specific regulation language
- `CustomsOfficeOfSubsequentlyEntry` - Expanded definition
- `CustomsOfficeOfExit` - Added "actual exit" and "export procedure" language
- `CustomsOfficeOfDeparture` - Added "transit" terminology
- `CustomsOfficeOfDestination` - Added "customs transit operation" language
- `CustomsOfficeOfImport` - Added "customs-approved treatment" language
- `CustomsOfficeOfExport` - Updated

Also changed one cardinality from `1` to `0..1`.

### Nov 20: New Document Types Added

Two entirely new UBL 2.5 document types:
- **WasteMovement** - "A document used to report the transport of waste"
- **WasteNotification** - Waste notification document

Added ~1,710 lines to the semantic model. Initially caused NDR errors due to
`WasteProducer` (should be `Waste Producer` with space), fixed within 15 minutes.

### Nov 20-21: Definition Rewording

Wholesale rewording of party definitions to follow naming conventions:
- "The party presenting..." → "The Party who presents..."
- "The party to whom..." → "The Party who receives..."
- "The authorized organization that issued..." → "The authorised Organisation who issues..."

Note the British spelling change: "authorized" → "authorised".

---

## Branch Activity

| Branch | Runs | Period | Purpose |
|--------|:----:|--------|---------|
| ubl-2.5 | 37 | Nov 17 - Feb 9 | Main development |
| ubl-2.5-python | 3 | Nov 17 | Python build system testing |
| ubl-2.5-2025-layout | 7 | Jan 10-15 | Layout experiment |
| kentest | 5 | Jan 21 | Testing branch |
| server-test | 1 | Jan 21 | Server testing |
| ubl-2.5-retry | 1 | Jan 21 | Retry after failures |

---

## Historical Workflow Runs (Before Nov 2025)

Metadata-only (no logs or artifacts available):

| Month | Total | Success | Failed | Cancelled | Notable Branches |
|-------|:-----:|:-------:|:------:|:---------:|------------------|
| Apr 2025 | 18 | 18 | 0 | 0 | ubl-2.4-os-iso-pub, ubl-2.5-csd01 |
| May 2025 | 1 | 1 | 0 | 0 | ubl-2.5 |
| Jun 2025 | 4 | 1 | 1 | 2 | ubl-2.5-dev |
| Jul 2025 | 15 | 15 | 0 | 0 | ubl-2.5 |
| Aug 2025 | 30 | 30 | 0 | 0 | UBL-2.4-ISO, ubl-2.5-7zip-test |
| Oct 2025 | 45 | 26 | 8 | 11 | ubl-2.5-python (migration) |
| **Total** | **113** | **91** | **9** | **13** | |

Notable: April 2025 shows `ubl-2.5-csd01` branch (the CSD01 era), and `ubl-2.4-os-iso-pub`
(UBL 2.4 OS ISO publication). October was turbulent with 8 failures during the Python
build system migration.

---

## Artifacts Preserved Locally

14 gc-snapshots downloaded and preserved:

| Snapshot | Artifact | .gc files | Notes |
|----------|----------|:---------:|-------|
| 20251117-1637z | 4591159085 | 6 | Earliest (ubl-2.5-python, no Endorsed) |
| 20251117-1646z | 4591257222 | 6 | ubl-2.5-python |
| 20251117-2027z | 4594074506 | 9 | First with all 3 gc types |
| 20251117-2120z | 4594558628 | 9 | |
| 20251117-2230z | 4595163792 | 9 | Last pre-customs-update |
| 20251119-1914z | 4619385679 | 9 | Post customs update |
| 20251119-2251z | 4621441403 | 9 | |
| 20251120-1010z | 4626371666 | 9 | Pre WasteMovement |
| 20251120-1350z | 4628183442 | 9 | **Post WasteMovement (NDR errors)** |
| 20251120-1930z | 4632606474 | 9 | NDR fixed |
| 20251121-1241z | 4640431446 | 9 | Definitions reworded |
| 20251203-1125z | 4750371329 | 9 | Dec snapshot |
| 20260121-1926z | 5210053700 | 6 | Jan snapshot (last CSD02) |
| 20260209-1513z | 5434847144 | 9 | **CSD03 transition** |

---

## Spec-to-PDF Server Transition

| Server | First Use | Last Use | Runs |
|--------|-----------|----------|:----:|
| `OASIS-2020-spec2pdfhtml` | Nov 17 (run 3) | Jan 21 (run 48) | 20 |
| `OASIS-2025-specnote2pdfhtml` | Jan 10 (run 34) | Feb 9 (run 55) | 8 |
| Neither (HUB-SKIPPED) | throughout | throughout | 27 |

The new 2025 spec server was introduced on the `ubl-2.5-2025-layout` branch on Jan 10
and became the default by Jan 28.

---

## Key Findings

1. **The Google Sheets are the source of truth.** All .gc files are generated from
   ODS downloads. The sheets are actively edited; we detected 13 distinct ODS states
   in 3 months.

2. **The TC works in bursts.** Nov 17-21 was intensely active (new document types,
   definition rewrites). Then 12-day gaps. Then another burst in Jan 21.

3. **No run ever had fully clean NDR.** The XSLT crash in the NDR checker
   (`Crane-checkgc4obdndr.xsl` line 48) masks the real NDR state on 47 of 55 runs.
   When it doesn't crash, actual errors are found. The build still succeeds
   (setting `Fail = no`).

4. **CSD03 is in progress.** The Feb 9 builds already use the CSD03 stage label
   with real cardinality changes, suggesting the TC is preparing for the next
   committee specification draft.

5. **Artifact retention is 90 days.** Everything before Nov 2025 is permanently lost.
   For historical preservation, artifacts should be downloaded within their retention
   window.

6. **The XSLT crash is a tooling bug, not a spec issue.** It occurs when comparing
   against the previous committee stage draft (csd01.gc for csd02 builds). The
   comparison against UBL 2.4-os works fine.

7. **4 missing files are persistent.** From run 5 onward, 4 `old2newDocBook` XML
   files are consistently missing -- a build configuration issue never resolved.
