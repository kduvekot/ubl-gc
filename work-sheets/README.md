# work-sheets/

Google Sheets revision history for UBL 2.5 — the authoritative source
spreadsheets are edited in-place on Google Drive, and this folder captures
their evolution over time.

## Background

The `oasis-tcs/ubl` CI workflow downloads three Google Sheets as ODS files
and converts them to GenericCode (.gc) via Saxon + Crane XSLT. The sheets
are the **authoritative source** — GC files are generated artifacts.

Two sheets matter for UBL 2.5:

| Sheet | Google Sheet ID |
|-------|-----------------|
| **Library** (common components) | `18o1YqjHWUw0-s8mb3ja4i99obOUhs-4zpgso6RZrGaY` |
| **Documents** (document types) | `1024Th-Uj8cqliNEJc-3pDOR7DxAAW7gCG4e-pbtarsg` |

Each sheet accumulates revisions as the TC edits it. The same sheet ID
serves all stages within a version (csd01 → csd02 → cs01 → os).

---

## Directory Structure

```
work-sheets/
├── README.md                  ← this file
├── revision-ods/              ← ODS snapshots at specific revision points
│   ├── manifest.json          ← version-to-revision mapping (V1-V10)
│   ├── ubl25_library/         ← 4 unique library revisions
│   │   ├── rev-1843.ods
│   │   ├── rev-1868.ods
│   │   ├── rev-1999.ods
│   │   └── rev-2005.ods
│   └── ubl25_documents/       ← 6 unique documents revisions
│       ├── rev-1793.ods
│       ├── rev-1803.ods
│       ├── rev-1983.ods
│       ├── rev-2190.ods
│       ├── rev-2200.ods
│       └── rev-2204.ods
└── scripts/                   ← tools for discovery, download, conversion
    ├── run.py                         ← orchestrator (runs steps in order)
    ├── discover-drive-history.py      ← map all Drive files and revisions
    ├── fetch-revision-metadata.py     ← get revision timestamps and authors
    ├── fetch-revision-content.py      ← download spreadsheet content per revision
    ├── download-revision-ods.py       ← download ODS via Drive API v2 exportLinks
    ├── test-revision-download.py      ← PoC validating revision-specific downloads
    ├── convert-revision-ods-to-gc.sh  ← ODS → GenericCode conversion pipeline
    ├── massageModelName.xml           ← regex rules for UBL model name expansion
    └── gc2endorsed.xsl                ← XSLT filter: raw GC → endorsed GC
```

---

## revision-ods/

ODS exports at the 10 revision points that correspond to the 10 CI workflow
runs (V1-V10) during CSD02/CSD03 development. These are the inputs to the
GenericCode conversion pipeline.

The `manifest.json` maps each version to its library + documents revision
pair and timestamp. Some versions share the same revision for one sheet
(e.g., V1 and V2 both use library rev-1843).

**Revision numbers** refer to Google Sheets' internal revision IDs, visible
via the authenticated export URL:
`https://docs.google.com/spreadsheets/export?id=SHEET_ID&revision=N&exportFormat=ods`

---

## scripts/

### Orchestrator

- **`run.py`** — Runs the next needed step in sequence (discovery → download
  → PoC test → ODS download). Uses `.claude/swap/` for intermediate state.
  Requires `GOOGLE_ACCESS_TOKEN` environment variable.

### Discovery and Download

These scripts require a Google OAuth token with `drive.readonly` scope.

- **`discover-drive-history.py`** — Recursively explores the OASIS UBL Google
  Drive folder, listing all files and their revision history with metadata.
- **`fetch-revision-metadata.py`** — Fetches revision timestamps and author
  info from the Drive API. Must run from a non-GCP IP (googleapis.com is
  blocked from Google Cloud IPs).
- **`fetch-revision-content.py`** — Downloads actual spreadsheet content at
  each revision for diffing and analysis.
- **`download-revision-ods.py`** — Downloads ODS files for specific revisions
  using Drive API v2 `exportLinks` (which return revision-specific content,
  unlike v3 which ignores the revision parameter).
- **`test-revision-download.py`** — PoC that validated the v2 exportLinks
  approach returns genuinely different content per revision.

### ODS → GenericCode Conversion

- **`convert-revision-ods-to-gc.sh`** — Converts ODS files to GenericCode
  using the same pipeline as the official `oasis-tcs/ubl` CI workflow:
  1. Saxon + `Crane-ods2obdgc.xsl` → `UBL-Entities-2.5.gc`
  2. Saxon + `Crane-ods2obdgc.xsl` → raw endorsed GC
  3. Saxon + `gc2endorsed.xsl` → `UBL-Endorsed-Entities-2.5.gc`

  Requires Java (for Saxon). Tools are in `history/tools/`.

- **`massageModelName.xml`** — Regex rules that expand short Google Sheet tab
  names to proper UBL model names (e.g., sheet tab "Invoice" becomes
  "UBL-Invoice-2.5" in the GC output).

- **`gc2endorsed.xsl`** — XSLT that filters a raw GenericCode file into its
  endorsed subset: removes `Endorsed*` columns, deletes rows with
  `EndorsedCardinality='0'`, and replaces `Cardinality` values with their
  endorsed equivalents.

---

## Regenerating GenericCode Files

The GC output files are not checked in (they're ~165MB). To regenerate:

```bash
# Ensure Java is available, then:
./work-sheets/scripts/convert-revision-ods-to-gc.sh

# Output goes to work-sheets/gc-from-revisions/V1-V10/
# Each version gets UBL-Entities-2.5.gc and UBL-Endorsed-Entities-2.5.gc
```
