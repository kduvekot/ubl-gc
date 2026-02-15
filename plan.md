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

### OASIS TC Folder

`https://drive.google.com/drive/folders/0B4X4evii3UjcdG5wNlVFTXlaYVU?resourcekey=0-QdNl6Z8MKz5C5xrWWo4IsA`

May contain older sheets and other files. Needs Drive API folder listing
(blocked from GCP IPs, works from browser).

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

---

## Phase 2 Results: Authenticated Access (COMPLETED)

### OAuth Token Approach

Used Google OAuth Playground (`407408718192.apps.googleusercontent.com`) with
user-provided tokens. Scopes: `drive.readonly`, `spreadsheets.readonly`, plus
several other readonly scopes.

### GCP IP Limitation

This server's IP (`35.226.26.185`) is a Google Cloud IP. Google blocks
`googleapis.com` API calls from GCP instances, returning HTML 403 (not JSON).

**Blocked:** All `googleapis.com` endpoints (Drive API, Sheets API)
**Works:** `docs.google.com/export?format=ods&revision=N` (different path)

This means we **cannot** get revision metadata (timestamps, authors) from this
server. We CAN download revision content.

### Revision History Availability

| Sheet | Real History? | Max Rev | Verified |
|-------|:---:|---:|:---:|
| **UBL 2.5 Library** | **YES** | **2,005** | 3 distinct content.xml hashes |
| **UBL 2.5 Documents** | **YES** | **2,204** | 4 distinct content.xml hashes |
| **UBL 2.4 Library** | **YES** | **673** | 4 distinct content.xml hashes |
| **UBL 2.4 Documents** | **YES** | **251** | 3 distinct content.xml hashes |
| UBL 2.3 Library | NO | (ignored) | all revisions identical |
| UBL 2.3 Documents | NO | (ignored) | all revisions identical |
| Signature | NO | (ignored) | all revisions identical |

**Total accessible revisions: 5,133** across 4 sheets.

3 sheets silently ignore the `revision` parameter (return current version for
any revision number, accept arbitrarily large numbers without error). These are
likely older sheets where revision sharing is disabled or history was purged.

### Cross-Sheet Lineage

UBL 2.3 Documents current hash = UBL 2.4 Documents rev 1 hash (`e0e6b7c9...`)
UBL 2.3 Library current hash = UBL 2.4 Library rev 1 hash (`7ad7708a...`)

This confirms each version's sheets were **forked from the previous version**.

### Schema Evolution in UBL 2.5 Library

Detailed column-by-column tracking of the first 23 revisions:

| Rev | Cols | Change |
|-----|------|--------|
| 1-3 | 22 | Original (inherited from 2.4) |
| 4 | 23 | +**Deprecated cardinality** (after Cardinality) |
| 9 | 23 | Renamed → "Future cardinality" |
| 10 | 23 | Renamed → "Endorsed cardinality" |
| 14 | 24 | +**Deprecated definition** (after Definition) |
| 17 | 25 | +**Deprecated** (prepended as col 1) |
| 18 | 24 | -Deprecated (removed — experimental) |
| 21 | 25 | +**Deprecated** (re-added as col 2) |
| 22 | 26 | +**"Depracion rational"** (typo!) |
| 23 | 26 | Typo fix → "Depracion rationale" |
| ~100+ | 26 | Stabilized at 26 columns |
| 2005 | 26 | Final: proper names, "Last Changed" added |

**Original 22 columns (rev 1, inherited from UBL 2.4):**
Component Name, Subset Cardinality, Cardinality, Definition, Alternative Business
Terms, Examples, Dictionary Entry Name, Object Class Qualifier, Object Class,
Property Term Qualifier, Property Term Possessive Noun, Property Term Primary Noun,
Property Term, Representation Term, Data Type Qualifier, Data Type, Associated
Object Class Qualifier, Associated Object Class, Component Type, UN/TDED Code,
Current Version, Editor's Notes

**Final 26 columns (rev 2005):**
Component Name, Subset Cardinality, Cardinality, **Endorsed Cardinality**,
**Endorsed Cardinality Rationale**, Definition, **Deprecated Definition**,
Alternative Business Terms, Examples, Dictionary Entry Name, Object Class Qualifier,
Object Class, Property Term Qualifier, Property Term Possessive Noun, Property
Term Primary Noun, Property Term, Representation Term, Data Type Qualifier, Data
Type, Associated Object Class Qualifier, Associated Object Class, Component Type,
UN/TDED Code, Current Version, **Last Changed**, Editor's Notes

### Row and Sheet Growth (UBL 2.5 Library, sampled every 100 revisions)

| Rev | Rows | Sheets | Notes |
|-----|------|--------|-------|
| 1 | 3,010 | CommonLibrary | Initial fork from 2.4 |
| 101 | 3,010 | CommonLibrary | Schema settled, no row changes yet |
| 201 | 3,012 | CommonLibrary | +2 rows |
| 501 | 3,051 | CommonLibrary | Steady growth |
| 1001 | 3,098 | CommonLibrary | |
| 1501 | 3,150 | CommonLibrary | |
| 1701 | 3,173 | CommonLibrary + **Logs-sheet**(11r) | New tab appeared |
| 1901 | 3,187 | CommonLibrary + Logs-sheet(31r) | |
| 2005 | 3,187 | CommonLibrary + Logs-sheet(38r) | Final state |

---

## Phase 3: Next Steps

### Immediate Need: Revision Metadata (timestamps)

The Drive API `revisions.list` call works from non-GCP IPs (e.g., browser).
Need to run these from OAuth Playground or local machine:

```
GET https://www.googleapis.com/drive/v3/files/{SHEET_ID}/revisions?pageSize=1000&fields=nextPageToken,revisions(id,modifiedTime,lastModifyingUser/displayName)
```

For all 4 sheets with real history. Results paginate at 1000 (need `pageToken`
for sheets with >1000 revisions).

### Folder Listing

```
GET https://www.googleapis.com/drive/v3/files?q='0B4X4evii3UjcdG5wNlVFTXlaYVU' in parents&fields=files(id,name,mimeType,modifiedTime)&pageSize=100
```

### Bulk Download Strategy

With 5,133 total revisions at ~600KB each = ~3GB. Feasible (30GB disk available)
but need to pace downloads (2-3 second intervals to avoid 429 rate limits).

**Smarter approach:** Many consecutive revisions may have identical content.xml.
Download all revisions but hash-deduplicate to find unique content snapshots.
Likely far fewer than 5,133 unique states.

### Convert to GenericCode

Each unique ODS snapshot needs Crane XSLT + Saxon conversion to produce the
GenericCode files that would feed into the git history branch.

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
