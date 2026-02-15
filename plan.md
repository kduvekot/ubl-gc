# Plan: Exploring Historical Edits from UBL Google Sheets

## Context

The `oasis-tcs/ubl` repository has a build workflow (`build.yml`) that downloads
three Google Sheets as ODS and converts them to GenericCode via Saxon + Crane XSLT.
The sheets are the **authoritative source** — GC files are generated artifacts.

### The Google Sheets (per version)

| Sheet | UBL 2.5 ID | UBL 2.4 ID | UBL 2.3 ID |
|-------|------------|------------|------------|
| **Library** | `18o1YqjHWUw0-s8mb3ja4i99obOUhs-4zpgso6RZrGaY` | `1kxlFLz2thJOlvpq2ChRAcv76SiKgEIRtoVRqsZ7OBUs` | `1eilb2NOKIuiy5kzCpp5O8vbZZk-oU9Ao7TiswJmVsvs` |
| **Documents** | `1024Th-Uj8cqliNEJc-3pDOR7DxAAW7gCG4e-pbtarsg` | `1GNpHCS7_QkJtP3QIOdPJWL5N3kQ1EzPznT6M8sPsA0Y` | `1_YamjYiJ5DFnWiA5h1tASDCOBTBSOgMYcS5ffHPFa3g` |
| **Signature** | `1T6z2NZ4mc69YllZOXE5TnT5Ey-FlVtaXN1oQ4AIMp7g` | *(same)* | *(same)* |

The Signature sheet is shared across versions. Each major version has its own
Library and Documents sheets. The sheets are edited in-place — the same sheet ID
serves all stages within a version (csd01 → csd02 → cs01 → os).

---

## What "More Detailed History" Means

Currently we have **one snapshot per OASIS release stage** (35 releases). But the
Google Sheets are continuously edited between releases. The edit history would give us:

1. **Inter-release changes** — Individual TC member edits between official stages
2. **Finer granularity** — See exactly when each entity/column was added or modified
3. **Attribution** — Who made each change (via revision metadata)
4. **Draft/work-in-progress states** — How the model evolved within a release cycle

---

## Exploration Plan

### Phase 1: Probe — Assess Access & Revision Depth

**Goal:** Determine what's actually accessible and how much history exists.

#### Step 1.1: Check public accessibility of each sheet

For each of the 7 unique sheet IDs, attempt:
```
wget --spider "https://docs.google.com/spreadsheets/d/{ID}/export?format=ods"
```
This tells us which sheets allow anonymous export (the CI workflow uses no
Google auth — it downloads via plain `wget --no-check-certificate`).

#### Step 1.2: Probe the revision list via Drive API v2

Use the **undocumented but functional** revision export endpoint:
```
https://docs.google.com/spreadsheets/d/{ID}/revisions
```
Or attempt the Drive API v2 revisions list (may require auth):
```
GET https://www.googleapis.com/drive/v2/files/{ID}/revisions
```

If anonymous access doesn't work, we'll need a Google API key or OAuth token.

#### Step 1.3: Test revision export

Try downloading a specific revision:
```
wget "https://docs.google.com/spreadsheets/d/{ID}/export?format=ods&revision=1"
wget "https://docs.google.com/spreadsheets/d/{ID}/export?format=ods&revision=100"
```
This endpoint reportedly works even when the Drive API revisions endpoint doesn't.
The `revision` parameter is a sequential integer starting from 1.

#### Step 1.4: Binary search for max revision number

If revision export works, find the total number of revisions per sheet using
binary search:
```python
lo, hi = 1, 100000
while lo < hi:
    mid = (lo + hi + 1) // 2
    if download_revision(sheet_id, mid) succeeds:
        lo = mid
    else:
        hi = mid - 1
max_revision = lo
```

**Expected output of Phase 1:**
- Which sheets are publicly exportable
- Whether revision-specific export works anonymously
- Approximate revision count per sheet
- Whether auth is required (and what kind)

---

### Phase 2: Map — Build a Revision Timeline

**Goal:** Create a metadata index of all revisions with timestamps.

#### Step 2.1: If Drive API access works

Use `revisions.list` (v2 or v3) to get metadata for each revision:
- `revisionId`
- `modifiedTime`
- `lastModifyingUser` (if available)
- File size changes

#### Step 2.2: If only export-with-revision works

Download a sparse sample of revisions (e.g., every 50th or 100th revision) as
ODS files. Extract metadata from the ODS internal XML:
```bash
unzip -p revision_N.ods meta.xml | xmllint --format -
```
This gives us creation date, modification date, and potentially author info.

#### Step 2.3: Correlate revisions with known release dates

Cross-reference revision timestamps against the known OASIS release dates
(documented in `docs/historical-releases.md`) to identify which revisions
correspond to which release stages.

**Expected output of Phase 2:**
- Timeline mapping: revision number → timestamp → OASIS stage
- Identification of "interesting" revisions (large changes, schema modifications)
- Gaps or periods of heavy editing

---

### Phase 3: Extract — Download Historical Snapshots

**Goal:** Download ODS snapshots at meaningful points in the sheet history.

#### Step 3.1: Define snapshot strategy

Options (from coarse to fine):
- **Coarse:** One snapshot per known release date (validates our existing GC files)
- **Medium:** Weekly snapshots during active editing periods
- **Fine:** Every Nth revision (e.g., every 10th or 50th)
- **Complete:** Every single revision (potentially thousands of files)

Recommended: Start with **coarse**, then selectively go finer for interesting periods.

#### Step 3.2: Download snapshots as ODS

```bash
for rev in $REVISION_LIST; do
    wget -O "snapshot-${rev}.ods" \
        "https://docs.google.com/spreadsheets/d/${ID}/export?format=ods&revision=${rev}"
done
```

Rate-limit to avoid Google throttling (1-2 second delay between requests).

#### Step 3.3: Convert each snapshot to GenericCode

Use the existing Crane-ods2obdgc pipeline (already in `history/tools/`):
```bash
java -jar saxon9he.jar \
    -xsl:Crane-ods2obdgc.xsl \
    -o:UBL-Entities-snapshot-${rev}.gc \
    -it:ods-uri \
    ods-uri="Library-${rev}.ods,Documents-${rev}.ods" \
    ...
```

This gives us diffable GenericCode for each snapshot.

#### Step 3.4: Diff consecutive snapshots

Generate diffs between consecutive GC snapshots to identify:
- When entities were added/removed/modified
- Column structure changes
- Cardinality modifications
- Name changes

**Expected output of Phase 3:**
- ODS snapshots at meaningful revision points
- Corresponding GC files for each snapshot
- Diff reports showing what changed between snapshots

---

### Phase 4: Integrate — Build Enhanced Git History

**Goal:** Create a richer git history branch using Google Sheets revision data.

#### Step 4.1: Determine commit strategy

For each Google Sheets revision that produces a different GC file:
- Use the revision's timestamp as the commit date
- Use the revision's author (if available) as commit metadata
- Include a commit message noting the revision number and any known context

#### Step 4.2: Build the enhanced history branch

Same approach as the current `build-history.sh` but with many more commits
representing the inter-release evolution.

#### Step 4.3: Tag known release stages

Apply git tags at commits that correspond to known OASIS release stages,
linking the fine-grained history to the official milestones.

---

## Key Risks & Unknowns

| Risk | Impact | Mitigation |
|------|--------|------------|
| Sheets not publicly accessible for revision export | Blocks everything | Test in Phase 1; may need OASIS TC member to share/export |
| Revision export requires authentication | Adds complexity | Try anonymous first; fall back to API key or OAuth |
| Google merges small edits into single revisions | Reduces granularity | Accept merged revisions; still better than release-only |
| Rate limiting on bulk downloads | Slows extraction | Add delays; download over multiple sessions |
| Crane XSLT fails on intermediate sheet states | Some snapshots won't convert | Skip unconvertible snapshots; log errors |
| Sheets were replaced (not edited in-place) across versions | Older versions may have short history | Each version has its own sheet IDs; history is per-sheet |
| Very large number of revisions | Storage/time concerns | Start coarse, refine selectively |

## Authentication Considerations

The UBL CI workflow downloads sheets anonymously (`wget --no-check-certificate`).
This suggests the sheets have "Anyone with the link can view" permissions. However:

- **Current content export:** Likely works anonymously (CI proves this)
- **Revision-specific export:** May or may not work anonymously
- **Drive API revisions.list:** Almost certainly requires OAuth or API key

If auth is needed, options:
1. **Google API key** (simplest, read-only, no user consent needed)
2. **OAuth2 service account** (more capable, can access Drive API)
3. **Manual export** (ask TC member to export revision history from UI)

---

## Proposed First Step

Write a small probe script (`scripts/probe-sheets-history.sh`) that:
1. Tests anonymous ODS export for each sheet (current version)
2. Tests revision-specific export (revision=1 and revision=2)
3. Reports what's accessible and what's not
4. If revision export works, does binary search for max revision number

This gives us concrete data to decide how to proceed.
