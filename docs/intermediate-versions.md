# Naming Convention for Intermediate Working Drafts

**Date:** 2026-02-15
**Status:** Adopted for UBL 2.5 intermediate snapshots

---

## Background: OASIS TC Process Stages

The OASIS Technical Committee (TC) process defines formal stages through which
a specification progresses. Each published stage gets a directory on
`docs.oasis-open.org/ubl/` using a standardized abbreviation:

| Abbreviation | Full Name | Used In |
|---|---|---|
| `prd` / `prd{N}` | Proposed Recommendation Draft | UBL 2.0, 2.1 |
| `cs` / `cs{NN}` | Committee Specification | UBL 2.0, 2.1, 2.2, 2.3 |
| `csd{NN}` | Committee Specification Draft | UBL 2.1, 2.3, 2.4, 2.5 |
| `csprd{NN}` | CS Public Review Draft | UBL 2.2, 2.3 |
| `cos` / `cos{NN}` | Candidate OASIS Standard | UBL 2.1, 2.2 |
| `os` | OASIS Standard | UBL 2.0-2.4 |
| `errata` | Errata | UBL 2.0 |

These abbreviations form the directory prefix in the standard OASIS pattern:

```
{stage}-UBL-{major}.{minor}
```

Examples: `csd01-UBL-2.5`, `os-UBL-2.4`, `prd3-UBL-2.0`

The 35 official published releases and their stage names are listed in
[`docs/historical-releases.md`](historical-releases.md).

---

## The Problem: What Happens Between Official Releases?

Between official releases, the UBL TC works continuously in Google Sheets
(Library, Documents, and Signature spreadsheets). The `oasis-tcs/ubl` repo's
CI workflow (`build.yml`) runs on every push to the `ubl-2.5` branch,
downloading the current sheets and generating fresh `.gc` files via XSLT.
These CI artifacts capture the semantic model at specific moments in time --
intermediate states that are **not published by OASIS** but represent real
editorial work.

For UBL 2.5, we recovered **9 intermediate working drafts** from CI artifacts
(full analysis in [`docs/artifact-provenance.md`](artifact-provenance.md)):

- **4 between CSD01 and CSD02** (Nov 17 - Nov 20, 2025)
- **5 between CSD02 and the upcoming CSD03** (Jan 21 - Feb 9, 2026)

These were identified by downloading all 55 non-expired GitHub Actions
artifacts from `oasis-tcs/ubl`, computing SHA-256 checksums of every `.gc`
file, and finding 10 unique content versions (the official CSD02 being version
V5, leaving 9 intermediate snapshots).

---

## Naming Convention

### Pattern

```
pre-{target_stage}-{YYYY}-{MM}-{DD}-{HHMM}-UBL-{version}
```

### Components

| Component | Meaning | Example |
|---|---|---|
| `pre-` | Prefix: this is a working draft *before* the next official stage | -- |
| `{target_stage}` | The official OASIS stage this work is heading toward | `csd02`, `csd03` |
| `{YYYY}-{MM}-{DD}` | ISO 8601 date of the CI artifact | `2025-11-17` |
| `{HHMM}` | UTC time (24-hour, no separator) when the CI workflow produced the artifact | `1042` |
| `-UBL-{version}` | Version suffix, matching the OASIS directory convention | `-UBL-2.5` |

### All 9 Intermediate Labels

```
pre-csd02-2025-11-17-1042-UBL-2.5   Initial CSD02 working copy
pre-csd02-2025-11-19-0915-UBL-2.5   Customs definitions rewritten
pre-csd02-2025-11-20-1350-UBL-2.5   WasteMovement ABIE added (with NDR errors)
pre-csd02-2025-11-20-1405-UBL-2.5   NDR fix: WasteProducer spacing corrected
pre-csd03-2026-01-21-1638-UBL-2.5   BuyerReference renamed to BuyerAssignedReference
pre-csd03-2026-01-21-1701-UBL-2.5   Cardinality change: 0..1 to 0..n
pre-csd03-2026-01-21-1926-UBL-2.5   BuyerAssignedReference rename propagated
pre-csd03-2026-02-09-1442-UBL-2.5   Three additional cardinality changes
pre-csd03-2026-02-09-1446-UBL-2.5   CSD02 to CSD03 metadata update in headers
```

---

## Design Rationale

### Why `pre-` and Not `wd` (Working Draft)?

An earlier proposal considered using the OASIS `wd` (Working Draft) stage
label for these artifacts. We chose `pre-` instead because:

- **`wd` is a formal OASIS process stage** with specific procedural meaning
  (see the [OASIS TC Process](https://www.oasis-open.org/policies-guidelines/tc-process-2017-05-26/)).
  These CI artifacts are not formal Working Drafts -- they were never
  submitted to the TC for review.
- **`pre-` is descriptive, not prescriptive.** It clearly signals "work in
  progress toward the next stage" without implying any formal status.
- **Unambiguous reading:** `pre-csd02` means "before CSD02 was published."

### Why Include the Full Timestamp (HHMM)?

Multiple working drafts can occur on the same date:

- `2025-11-20` has two snapshots: `1350` (WasteMovement added) and `1405`
  (NDR fix, 15 minutes later)
- `2026-02-09` has two snapshots: `1442` (cardinality changes) and `1446`
  (metadata update, 4 minutes later)

The minute-level timestamp ensures unique, sortable labels. It also supports
a future scenario where Google Sheets are polled at regular intervals (e.g.,
every 10 minutes), which would produce many snapshots sharing the same date.

### Why Is the Target Stage Lowercase?

This follows the OASIS directory convention on `docs.oasis-open.org`, where
all stage prefixes are lowercase: `csd01-UBL-2.5`, `os-UBL-2.4`,
`prd3-UBL-2.0`, etc.

### How Is the Target Stage Determined?

The target stage comes from two sources that must agree:

1. **`build.sh` in `oasis-tcs/ubl`:** The `UBLstage` variable declares what
   the TC is currently working toward (e.g., `UBLstage=csd03`).
2. **`.gc` file headers:** The `<ShortName>`, `<LongName>`, and `<LocationUri>`
   elements inside the generated `.gc` files contain the target stage
   (e.g., `UBL-2.5-CSD03`, `csd03-UBL-2.5`).

When the TC transitions from one stage to the next, both the `build.sh`
configuration and the `.gc` metadata are updated, which is visible in the
final intermediate snapshot before each official release (e.g.,
`pre-csd03-2026-02-09-1446` contains the CSD02-to-CSD03 metadata update).

---

## How Labels Appear in Commit Messages

In the `work-history` branch, commit messages use this format:

**Intermediate releases** -- full timestamp label, minus the `-UBL-{version}`
suffix (since the version is already in the subject line):

```
UBL 2.5 pre-csd02-2025-11-17-1042: Initial CSD02 working copy
UBL 2.5 pre-csd03-2026-02-09-1446: Update metadata (UBL-2.5-CSD02 -> UBL-2.5-CSD03)
```

**Official releases** -- uppercased stage name only:

```
UBL 2.5 CSD01: Modify ABIE "Weight Statement"
UBL 2.5 CSD02: Modify ABIE "Waybill"
```

This formatting logic is implemented in `work/scripts/build_work_history.py`
(the `_format_stage()` method, line 94).

---

## Relationship to Official Releases

```
                    Official                          Intermediate
                    --------                          ------------
UBL 2.5 CSD01      csd01-UBL-2.5
                    |
                    +-- pre-csd02-2025-11-17-1042     (V1: initial working copy)
                    +-- pre-csd02-2025-11-19-0915     (V2: customs rewrite)
                    +-- pre-csd02-2025-11-20-1350     (V3: WasteMovement added)
                    +-- pre-csd02-2025-11-20-1405     (V4: NDR fix)
                    |                                 (V5 = the published CSD02)
UBL 2.5 CSD02      csd02-UBL-2.5
                    |
                    +-- pre-csd03-2026-01-21-1638     (V6: BuyerReference renamed)
                    +-- pre-csd03-2026-01-21-1701     (V7: cardinality change)
                    +-- pre-csd03-2026-01-21-1926     (V8: rename propagated)
                    +-- pre-csd03-2026-02-09-1442     (V9: cardinality changes)
                    +-- pre-csd03-2026-02-09-1446     (V10: stage metadata)
                    |
UBL 2.5 CSD03      csd03-UBL-2.5  (pending)
```

The V1-V10 labels are for cross-referencing with `docs/artifact-provenance.md`
only. They do not appear in filenames, directory names, or commit messages.

---

## Data Sources

| Source | What It Provides | Reference |
|---|---|---|
| GitHub Actions artifacts (`oasis-tcs/ubl`) | `.gc` files generated from Google Sheets at specific moments | [`docs/artifact-provenance.md`](artifact-provenance.md) |
| `build.sh` in `oasis-tcs/ubl` | `UBLstage` / `UBLprevStage` variables declaring the target stage | [`docs/workflow-history-analysis.md`](workflow-history-analysis.md) |
| `.gc` file XML headers | `<ShortName>`, `<LongName>`, `<LocationUri>` containing the stage metadata | [`docs/genericcode-format.md`](genericcode-format.md) |
| SHA-256 checksums of `.gc` files | Content identity: 55 artifacts reduced to 10 unique versions | [`docs/artifact-provenance.md`](artifact-provenance.md) |

---

## Applicability to Future Versions

This naming convention is designed to generalize beyond UBL 2.5. If
intermediate working drafts are captured for future versions, the same
pattern applies:

```
pre-{target_stage}-{YYYY}-{MM}-{DD}-{HHMM}-UBL-{version}
```

For example, a working draft toward UBL 2.6 CSD01 would be labeled:

```
pre-csd01-2027-03-15-0930-UBL-2.6
```

The target stage component adapts to whatever OASIS stage name the TC uses
for the next milestone, preserving compatibility with the evolving OASIS
process terminology (PRD, CSD, CSPRD, CS, COS, OS).

---

## Related Documentation

- [`docs/historical-releases.md`](historical-releases.md) -- All 35 official OASIS releases
- [`docs/artifact-provenance.md`](artifact-provenance.md) -- SHA-256 analysis of 55 CI artifacts
- [`docs/workflow-history-analysis.md`](workflow-history-analysis.md) -- CI workflow analysis
- [`work/scripts/work_release_manifest.py`](../work/scripts/work_release_manifest.py) -- Manifest with all 44 releases (35 official + 9 intermediate)
- [`work/scripts/build_work_history.py`](../work/scripts/build_work_history.py) -- Build script with commit message formatting
