# Google Sheets Revision API Investigation Plan

**Date:** 2026-02-17
**Branch:** `claude/investigate-oasis-sheets-aYOlG`
**Focus:** UBL 2.5 sheets (Library + Documents)

---

## The Problem

We have **three methods** for downloading historical revisions of Google Sheets
as ODS files. Previous work discovered that:

1. One method (v3 `files.export`) silently ignores the revision parameter
2. Two methods (v2 `exportLinks` and direct Sheets URL) claim to return
   revision-specific content
3. When the Colab notebook (`download-all-revisions.ipynb`) was run using the
   direct Sheets URL method, it **did not produce ODS files matching** the ones
   downloaded earlier via v2 `exportLinks`

This raises the question: are both "working" methods truly returning
revision-specific content, or does one of them silently fall back to the
latest version under certain conditions?

Additionally, we know that ODS exports are **non-deterministic at the binary
level** (different metadata/timestamps each download). This means raw ODS
hashes will always differ between downloads, even for the same revision. Only
`content.xml` hashes or GC conversion output hashes are reliable fingerprints.

---

## The Three API Methods

### Method A: Drive API v3 `files.export` (BROKEN)

```
GET https://www.googleapis.com/drive/v3/files/{fileId}/export
    ?mimeType=application/x-vnd.oasis.opendocument.spreadsheet
    &revision={revisionId}
```

- **Status:** BROKEN for Google Sheets. The `revision` parameter is silently
  ignored. Always returns the current (latest) content.
- **Evidence:** `fetch-revision-content.py` (Step 2) used this method. All
  exports for different revisions produced identical CSV/XLSX content.
- **Used by:** `fetch-revision-content.py`

### Method B: Drive API v2 `revisions/{id}` → `exportLinks` (PROVEN)

```
Step 1: GET https://www.googleapis.com/drive/v2/files/{fileId}/revisions/{revisionId}
        → JSON response includes { "exportLinks": { "mime/type": "url", ... } }

Step 2: GET {exportLinks URL for ODS MIME type}
        → ODS file bytes
```

- **Status:** PROVEN to return revision-specific content
- **Evidence:** PoC in `test-revision-download.py` confirmed that different
  revision IDs produce different CSV hashes via this method. The 10 ODS files
  in `work-sheets/revision-ods/` were downloaded this way and have 10 distinct
  SHA-256 hashes.
- **Used by:** `download-revision-ods.py`, `validate-revision-ods-to-gc.ipynb`
- **Limitation:** Only accesses ~25 "major" revisions (the ones returned by
  `revisions.list`), not the thousands of internal save points

### Method C: Direct Sheets Export URL (UNVERIFIED)

```
GET https://docs.google.com/spreadsheets/export
    ?id={sheetId}
    &revision={N}
    &exportFormat=ods
```

- **Status:** ASSUMED working but NOT independently verified against Method B
- **Evidence:** The Colab notebook `download-all-revisions.ipynb` uses this
  method. When run, it downloaded ODS files that DID NOT match the files from
  Method B.
- **Used by:** `download-all-revisions.ipynb`
- **Key difference:** Accesses ALL internal revision numbers (1 → max), not
  just the ~25 major ones. This is much more granular.
- **Suspicion:** May silently return the current version for certain revision
  numbers or under rate limiting / load

### Method D: Drive API v3 `files.download` POST (PARTIALLY TESTED)

```
POST https://www.googleapis.com/drive/v3/files/{fileId}/download
     ?mimeType=text/csv
     &revisionId={revisionId}
```

- **Status:** Tested in `test-revision-download.py` but results not preserved
  (the `.claude/swap/poc-revision-download.txt` file is missing)
- **Note:** This is a newer API specifically documented as supporting
  `revisionId` for Google Workspace files

---

## What We Need to Determine

### Question 1: Do Methods B and C use the same revision numbering?

Method B uses `revisionId` from `revisions.list` (e.g., "1843", "2005").
Method C uses `revision=N` where N ranges from 1 to ~2005.

We ASSUME these are the same numbers. But are they? If "revision 1843" in
Method B means something different from `revision=1843` in Method C, that
alone explains the mismatch.

### Question 2: Does Method C actually return revision-specific content?

Possible failure modes:
- Always returns current content (like Method A)
- Returns revision-specific content for recent revisions but falls back to
  current for old ones
- Returns revision-specific content normally but falls back under rate limiting
- Returns revision-specific content for "major" revision numbers (those in
  `revisions.list`) but current content for intermediate save points
- Works correctly, but we're comparing the wrong way (binary ODS hash instead
  of content.xml hash)

### Question 3: What does "didn't produce the exact ODS files" mean?

ODS exports are non-deterministic at the binary level. To properly compare:
- Extract `content.xml` from each ODS (it's a ZIP archive)
- Hash `content.xml` — this should be deterministic for same spreadsheet state
- Or convert ODS → GC and compare GC hashes (deterministic conversion)

If the Colab notebook compared raw ODS hashes, mismatches are EXPECTED and
don't indicate a problem. If it compared content.xml hashes or GC hashes,
then we have a real API behavior issue.

### Question 4: Are the revision-ods files in the repo the right ones?

The 10 ODS files in `work-sheets/revision-ods/` were downloaded via Method B.
They need to be independently verified:
- Convert each to GC using `convert-revision-ods-to-gc.sh`
- Compare GC SHA-256 against the known V1-V10 hashes from CI artifacts
  (documented in `docs/artifact-provenance.md` and `work/TIMELINE.md`)
- If they match, Method B is confirmed reliable

---

## Investigation Plan

### Phase 1: Local Verification (No API calls needed)

**Goal:** Verify the 10 ODS files we already have produce the correct GC output.

**Steps:**

1. **Run the conversion pipeline locally**
   ```bash
   ./work-sheets/scripts/convert-revision-ods-to-gc.sh --force
   ```
   This converts all 10 revision ODS pairs → GC files using Saxon + Crane.

2. **Compare GC hashes against known V1-V10 hashes**
   The expected hashes are in:
   - `docs/artifact-provenance.md` (full table)
   - `work/TIMELINE.md` (verification checksums)
   - `notebooks/validate-revision-ods-to-gc.ipynb` (EXPECTED_GC dict)

   If all 10 match → Method B (v2 exportLinks) is confirmed reliable.

3. **Check existing ODS content.xml hashes**
   Extract and hash content.xml from each ODS in `work-sheets/revision-ods/`.
   Record these as the reference content fingerprints.

### Phase 2: API Comparison Notebook (Requires Google Auth — run in Colab)

**Goal:** Directly compare Methods B and C by downloading the same revision
via both methods and comparing output.

**Design:** Create a new Colab notebook `notebooks/compare-api-methods.ipynb`

**Steps:**

1. **Download 4 known revisions via BOTH methods**
   - Pick revisions where we know the content differs:
     - Library rev-1843 (V1 state)
     - Library rev-2005 (V7-V10 state)
     - Documents rev-1793 (V1 state)
     - Documents rev-2204 (V9-V10 state)

2. **For each revision, download via:**
   - Method B: `v2/files/{id}/revisions/{rev}` → `exportLinks` → ODS
   - Method C: `spreadsheets/export?id={id}&revision={rev}&exportFormat=ods`

3. **Compare at three levels:**
   - Raw ODS SHA-256 (expected to differ — non-deterministic)
   - Extracted content.xml SHA-256 (should match if same data)
   - GC conversion output SHA-256 (definitive — should match)

4. **Test Method C edge cases:**
   - Download the SAME revision twice via Method C — does content.xml match?
     (Tests non-determinism)
   - Download a non-existent revision number — does it 404 or return current?
   - Download with a very rapid burst (no delay) — does it degrade?
   - Download revision 1 (very first) — does it return actual old content?

5. **Test revision number consistency:**
   - Via Method B: `v2/files/{id}/revisions/{rev}` → get `modifiedDate`
   - Via Method C: download `revision={rev}` and check if content matches
   - This confirms both methods use the same numbering

### Phase 3: Deep Revision Scan (Requires Google Auth — run in Colab)

**Goal:** Understand the full revision landscape and find the exact ODS states
that correspond to each GC version.

**Steps:**

1. **Scan a small range around known revisions via Method C**
   - For Library: try revisions 1840-1850 (around 1843), 1995-2010 (around 1999/2005)
   - For each: download ODS, hash content.xml
   - Map out which revision ranges share the same content state

2. **Compare content.xml hashes from Method C against Method B reference**
   - The reference hashes from Phase 1 tell us what content.xml should look
     like for each known revision
   - If Method C produces different content.xml for the same revision number,
     that's the smoking gun

3. **Check if Method C returns "current" for old revisions**
   - Download revision 1 via Method C
   - If its content.xml matches the LATEST content.xml → Method C is broken
     for old revisions
   - If it has genuinely old content → Method C works

### Phase 4: Public Drive Exploration (No Auth needed)

**Goal:** Use `explore-public-drive.py` to see what's publicly visible in the
OASIS UBL Google Drive folder.

**Steps:**

1. **Run the public folder explorer**
   ```bash
   python3 work-sheets/scripts/explore-public-drive.py \
     1SVXV_8CF4ib9YsVZ6G7AqIP3gNK6q3Gj \
     work-sheets/public-drive-contents.json
   ```
   This folder was referenced in the Colab notebook as the output location
   for bulk revision downloads.

2. **Check if Colab output exists on Drive**
   - If the Colab notebook was run and saved results to Drive, the manifests
     would be here
   - These manifests would tell us exactly what was downloaded and what hashes
     were observed

3. **Cross-reference with our local data**
   - Do the files on Drive correspond to our local `work-sheets/revision-ods/`?
   - Are there additional files (from the full 2005-revision scan) that we
     don't have locally?

---

## Expected Outcomes

### If Methods B and C agree (content.xml match for same revision):
- The Colab notebook issue was likely a comparison methodology problem
  (comparing raw ODS hashes instead of content.xml or GC hashes)
- Both methods are reliable; Method C is preferable for exhaustive scans
  because it accesses ALL internal revisions

### If Methods B and C disagree (different content.xml for same revision):
- Method C may be returning current content, not historical
- Need to determine: always? or only for certain revision numbers/conditions?
- If Method C is unreliable, the `download-all-revisions.ipynb` Colab notebook
  needs to be rewritten to use Method B (v2 exportLinks)
- Method B only accesses ~25 "major" revisions though, which limits granularity

### If Method B GC output doesn't match V1-V10:
- The ODS files in `work-sheets/revision-ods/` are wrong
- Need to investigate whether the revision-to-workflow mapping is incorrect
- The V1-V10 mapping in the manifest may have wrong revision numbers

---

## Files Inventory

### Already have (local, in repo):
- `work-sheets/revision-ods/` — 10 ODS files (4 library + 6 documents)
  downloaded via Method B, with manifest
- `work-sheets/scripts/convert-revision-ods-to-gc.sh` — conversion pipeline
- `work/work-history/` — 9 intermediate GC snapshots from CI artifacts
- `work/gc-versions/` — 27 reference GC files (V1-V10 entities, endorsed, sig)
- `notebooks/validate-revision-ods-to-gc.ipynb` — Colab validation notebook
  (uses Method B)
- `notebooks/download-all-revisions.ipynb` — Colab bulk download notebook
  (uses Method C)

### Need to create:
- `notebooks/compare-api-methods.ipynb` — API comparison notebook (Phase 2)
- `docs/api-method-comparison-results.md` — Results writeup

### Useful existing tool:
- `work-sheets/scripts/explore-public-drive.py` — can check public Drive
  folder for any Colab output files without auth

---

## Quick Reference: Revision Numbers

### Library (18o1YqjHWUw0-s8mb3ja4i99obOUhs-4zpgso6RZrGaY)

| Rev | Date | V-Map | Description |
|-----|------|-------|-------------|
| 1843 | 2025-11-12 | V1+V2 | Pre-CSD02 initial |
| 1868 | 2025-11-19 | V3+V4 | Customs rewritten |
| 1999 | 2025-12-03 | V5+V6 | CSD02 official |
| 2005 | 2026-01-21 | V7-V10 | BuyerReference renamed |

### Documents (1024Th-Uj8cqliNEJc-3pDOR7DxAAW7gCG4e-pbtarsg)

| Rev | Date | V-Map | Description |
|-----|------|-------|-------------|
| 1793 | 2025-10-17 | V1+V2 | Pre-CSD02 baseline |
| 1803 | 2025-11-19 | V3 | Before Nov 20 edit |
| 1983 | 2025-11-20 | V4 | NDR fix edit |
| 2190 | 2025-11-21 | V5-V7 | Last before CSD02 |
| 2200 | 2026-01-21 | V8 | Jan 21 edit |
| 2204 | 2026-02-04 | V9+V10 | Feb 4 edit |

---

## Priority Order

1. **Phase 1** first — purely local, no API calls, verifies what we have
2. **Phase 4** next — no auth needed, quick public Drive check
3. **Phase 2** then — requires Colab session with Google auth, but is the
   critical experiment
4. **Phase 3** last — deeper scan, only needed if Phase 2 shows both methods
   work

---

## Phase 1 Results (2026-02-17)

### ODS→GC Conversion: All 10 versions converted successfully

### GC Hash Verification Against CI Artifacts

| ODS Ver | Revisions (lib/doc) | Full Hash Match | Data Hash Match | CI Match |
|---------|--------------------|----|-----|----|
| V1 | L1843/D1793 | FULL | FULL | CI V1 |
| V2 | L1843/D1793 | MISMATCH | MISMATCH | CI V1 (wrong! should match CI V2) |
| V3 | L1868/D1803 | MISMATCH | MISMATCH | CI V2 (shifted!) |
| V4 | L1868/D1983 | FULL | FULL | CI V4 |
| V5 | L1999/D2190 | FULL | FULL | CI V5 (published CSD02) |
| V6 | L1999/D2190 | MISMATCH | MISMATCH | CI V5 data (wrong! should match CI V6) |
| V7 | L2005/D2190 | DATA-ONLY | FULL | CI V7 |
| V8 | L2005/D2200 | DATA-ONLY | FULL | CI V8 |
| V9 | L2005/D2204 | DATA-ONLY | FULL | CI V9/V10 |
| V10 | L2005/D2204 | FULL | FULL | CI V10 |

### Key Finding: 3 Revision Mappings Are Wrong

The revision-to-workflow mapping has **3 incorrect entries**:

1. **V2 (CI ran Nov 19 09:15):** Mapped to lib=1843 (Nov 12), but CI V2
   produced different data than V1. The library was edited between Nov 12 and
   Nov 19 — an intermediate revision exists between 1843 and 1868 that our
   `revisions.list` query didn't capture.

2. **V3 (CI ran Nov 20 13:50):** ODS V3 (lib=1868, doc=1803) produces data
   matching CI V2, not CI V3. The documents sheet had an additional edit
   between doc=1803 and doc=1983 that isn't in our "major" revision list.

3. **V6 (CI ran Jan 21 16:38):** ODS V6 (lib=1999, doc=2190) produces the
   same data as CSD02 (V5), but CI V6 has different data. By Jan 21, the
   library had already been edited beyond rev-1999.

### Root Cause: Major vs Internal Revisions

The Drive API v2 `revisions.list` only returns ~25 "major" revisions per
sheet. But Google Sheets has ~2005 internal revision save-points for the
Library sheet and ~2204 for Documents. The mapping was built from "major"
revision timestamps, but the CI workflow downloaded the CURRENT sheet state
(which could be an intermediate auto-save between major revisions).

**The "major" revisions are insufficient to reconstruct exact CI states.**

We need to scan ALL internal revisions (via Method C: direct Sheets export
URL) to find the exact revision numbers that match CI V2, V3, and V6.

### DATA-ONLY Matches (V7, V8, V9)

These have correct entity data but different `<Identification>` blocks.
The CI used slightly different stage parameters than our conversion script.
This is expected and non-problematic — the data content is verified correct.

### Content.xml Reference Hashes

All 10 ODS files have unique content.xml hashes (4 library + 6 documents),
confirming the ODS files themselves contain distinct data. Saved to
`work-sheets/revision-ods/content-hashes.json`.

### Implications for Phase 2

Phase 2 (API comparison notebook) should:
1. Download revisions 1843-1870 for library to find which intermediate
   revision matches CI V2's data hash (`c21c9fd6de75cfe5...`)
2. Download revisions 1800-1810 for documents to find the revision matching
   CI V3's data hash (`85d713818f2654c2...`)
3. Download revisions 1995-2010 for library to find the revision matching
   CI V6's data hash (`1ebde1fcadd0f0f9...`)
4. Compare Method B and Method C outputs for the same revision number

---

## Manifest Cluster Analysis (2026-02-17)

Downloaded and analyzed the Colab manifests from the public Google Drive folder
(`/tmp/ubl-gc-investigation/manifests/`).

### Method C is NOT Fully Broken — It Has Correct Clusters

Analysis of all ~4200 downloaded revisions reveals that Method C (direct Sheets
export URL) does return correct historical data, but only in **short clusters**.
Between clusters, it returns the current/latest content.

### Library Sheet (1962 revisions downloaded)

| Rev Range | Count | Unique States | ODS Size | Status |
|-----------|-------|---------------|----------|--------|
| 1-39 | 39 | 34 unique | ~596-601KB | **Historical** |
| 40-350 | 311 | 1 (current) | 640KB | Broken |
| 351-368 | — | GAP (missing) | — | — |
| 369-401 | 33 | 33 unique | ~606-607KB | **Historical** |
| 402-1135 | 734 | 1 (current) | 640KB | Broken |
| 1136-2004 | 845 | 1 (current) | 640KB | Broken |

- **96% of revisions returned current content** (1890/1962)
- 2 historical clusters with 72 genuinely unique revision states
- ALL 4 Method B reference revisions (1843, 1868, 1999, 2005) are MISSING
  from the Colab download (returned 400/404 errors)
- GC data: 49 unique GC states in the historical clusters

### Documents Sheet (2161 revisions downloaded)

| Rev Range | Count | Unique States | ODS Size | Status |
|-----------|-------|---------------|----------|--------|
| 1-8 | — | GAP | — | — |
| 9-47 | 39 | 32 unique | ~790-791KB | **Historical** |
| 48-133 | 86 | 1 (current) | 931KB | Broken |
| 134-145 | — | GAP (missing) | — | — |
| 146-194 | 49 | 49 unique | ~807-814KB | **Historical** |
| 195-1695 | 1501 | 1 (current) | 931KB | Broken |
| 1696-1718 | — | GAP (missing) | — | — |
| 1719-1751 | 33 | 32 unique | ~910KB | **Historical** |
| 1752-2204 | 453 | 1 (current) | 931KB | Broken |

- **94% of revisions returned current content** (2040/2161)
- 3 historical clusters with 121 genuinely unique revision states
- All 6 Method B reference revisions are present but ALL return LATEST content
- GC data: 28 unique GC states, mostly in historical clusters

### The Pattern: Session Reset Hypothesis

Method C works correctly for short bursts (~30-50 revisions) after:
1. **Start of download session** (rev 1-39 for library, rev 9-47 for docs)
2. **After error gaps** (missing revisions = HTTP errors during the Colab run)

Then it "collapses" back to returning current content for hundreds of
subsequent revisions until the next error gap triggers a reset.

Evidence supporting this:
- Historical clusters have **progressive file sizes** appropriate for the
  sheet's age (smaller files = earlier versions)
- Broken runs have **uniform 640KB / 931KB** file sizes (= current state)
- Gaps (missing revisions) immediately precede each new historical cluster

### Implication: Method B and Method C Use DIFFERENT Revision Numbering

The fact that Method B revision IDs (1843, 1868, etc.) either don't exist
in Method C's namespace (library: 404 errors) or return current content
(documents) strongly suggests the two methods use different numbering.

- **Method B (v2)**: Uses Drive API revision IDs from `revisions.list`
- **Method C**: Uses Google Sheets' internal revision counter (1-2005)
- These may map to different revisions!

### None of the Historical Clusters Match CI V1-V10

The historical data in the clusters is from very early in the sheets' life:
- Library cluster 1 (rev 1-39): ~596KB files — the sheet when first created
- Library cluster 2 (rev 369-401): ~607KB files — still much smaller than
  current 640KB
- Documents late cluster (rev 1719-1751): ~910KB — closer to current 931KB

The CI V1-V10 versions correspond to revisions 1843-2005 (library) and
1793-2204 (documents) — well within the "broken" ranges.

### New Notebooks Created

1. **`notebooks/revision-metadata-and-export-links.ipynb`** — Gets ALL revision
   metadata with timestamps via v3 `revisions.list` + v2 `revisions/{id}`.
   Iterates all ~4200 revision IDs to get `modifiedDate` + `exportLinks`.
   Matches revisions to CI workflow timestamps for correct pairings.

2. **`notebooks/analyze-method-c-clusters.ipynb`** — Analyzes the actual
   downloaded ODS files on Google Drive: file creation timestamps, cluster
   boundaries, cell-level diffs between historical and current content.

### Next Steps

1. **Run notebook 1** (revision-metadata-and-export-links) to get timestamps
   for all revisions via v2 — this gives us the correct revision numbering
   and export links
2. **Run notebook 2** (analyze-method-c-clusters) to understand the temporal
   pattern of correct vs broken downloads in Method C
3. **Use v2 export links** to download ODS for the correct revisions at each
   CI workflow timestamp — this is the proven method
4. **Cell-level diffs** may reveal which edits happened between revisions,
   helping us understand the sheet's evolution
