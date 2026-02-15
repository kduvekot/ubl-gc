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

## Phase 1 Results: Access Probing (COMPLETED)

### What works anonymously

| Access Method | Works? | Gives History? |
|--------------|--------|----------------|
| Current export (`/export?format=ods`) | **Yes** (6/7 sheets) | No (current only) |
| Revision export (`&revision=N`) | HTTP 200 but **silently ignored** | **No** |
| Drive API v2/v3 revisions.list | **No** (403 Forbidden) | Would if authenticated |
| /revisions page | **No** (404) | N/A |

**Key finding:** The `revision=N` parameter is silently ignored for anonymous
exports. All revision numbers (1, 2, 50, 100, 999999) return the identical
`content.xml` (verified by SHA256: `5cda4343...`). The difference in ODS-level
hashes is just ZIP re-packaging artifacts.

**Conclusion:** Accessing Google Sheets revision history **requires OAuth
authentication**. There is no anonymous workaround.

### Detailed evidence

- Script: `/home/user/ubl-sheets-history/probes/probe-access.sh`
- Full log: `/home/user/ubl-sheets-history/probes/probe-results.log`
- Provenance: `/home/user/ubl-sheets-history/PROVENANCE.md`

---

## Alternative Discovery: CI Build Artifacts

The `oasis-tcs/ubl` CI workflow captures Google Sheet state on every push:

- **189 total workflow runs** since early 2025
- **58 non-expired artifacts** spanning 2025-11-17 to 2026-02-09
- Each artifact contains the 3 Google ODS files downloaded at build time
- Plus the generated GC files

This gives us ~58 point-in-time snapshots of the Google Sheets from the last
~3 months, with no authentication needed (just `gh api` to download artifacts).

### Limitation

The 93 expired artifacts (older than ~90 days) are gone. So this only covers
a recent window of UBL 2.5 CSD02/CSD03 development, not the full history.

---

## Viable Paths Forward

### Path A: Authenticated Google Drive API (comprehensive, needs setup)

**What it gives us:** Full revision history of all 7 sheets, potentially
hundreds or thousands of revisions spanning years.

**Requirements:**
1. Create Google Cloud project
2. Enable Drive API
3. Create OAuth2 credentials (service account or user consent)
4. Use Drive API v2 `revisions.list` to enumerate revisions
5. Use `revisions.get` with export links to download each revision as ODS
6. Convert each ODS to GC via Crane pipeline

**Pros:** Most comprehensive; covers full history
**Cons:** Requires Google Cloud setup; may need OASIS TC's permission if
sheets require specific sharing for revision access

### Path B: CI Artifact Mining (partial, ready now)

**What it gives us:** ~58 snapshots from the last 3 months of UBL 2.5
development.

**Requirements:**
1. Download all 58 non-expired artifacts via `gh api`
2. Extract ODS files from each (inside 7z inside zip)
3. Compare ODS content.xml hashes to find which are actually different
4. Convert unique snapshots to GC
5. Diff consecutive GC files

**Pros:** No auth needed; data is available right now; proves the concept
**Cons:** Only covers ~3 months; only UBL 2.5; many may be identical
(same sheet state across rapid CI re-runs)

### Path C: Hybrid — Mine artifacts now, set up auth for full history

**Recommended approach:**

1. **Immediate:** Extract unique ODS snapshots from the 58 CI artifacts
   to prove the concept and see what inter-release changes look like
2. **Next:** Set up Google OAuth to access the full revision history
3. **Then:** Build the comprehensive timeline with all available data

### Path D: Ask the OASIS TC

The TC members have direct access to the sheet revision history UI.
They could potentially:
- Export the full revision history
- Share a version history summary
- Grant specific API access to the sheets

---

## Next Steps

1. Compare the Jan 21 artifact ODS with today's download to verify CI
   artifacts capture real content changes
2. Download a few more artifacts from different dates and deduplicate
3. Decide on Path A vs Path C based on findings
4. Update provenance log with all decisions and data
