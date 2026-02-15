# Workflow Artifact Analysis - 2026-02-15

## Summary

Analysis of 58 non-expired GitHub Actions artifacts from `oasis-tcs/ubl`,
with urgent preservation of 32 artifacts expiring between Feb 15-19, 2026.

## Key Discovery: Google Sheets Are the True Source

The UBL build pipeline does NOT generate `.gc` files from files in the git repository.
Instead, each workflow run:

1. Downloads **3 live Google Sheets** as `.ods` at build time
2. Converts `.ods` → `.gc` via Saxon XSLT (Crane-ods2obdgc tooling)
3. Validates the `.gc` files (namespace-aware XML parsing)
4. Runs NDR compliance checks against previous versions
5. Generates downstream artifacts (XSD, JSON, HTML, etc.)

### The 3 Source Spreadsheets

| Sheet | Google Sheets ID | Purpose |
|-------|-----------------|---------|
| Signature | `1T6z2NZ4mc69YllZOXE5TnT5Ey-FlVtaXN1oQ4AIMp7g` | Signature entity definitions |
| Library | `18o1YqjHWUw0-s8mb3ja4i99obOUhs-4zpgso6RZrGaY` | Library/component definitions |
| Documents | `1024Th-Uj8cqliNEJc-3pDOR7DxAAW7gCG4e-pbtarsg` | Document type definitions |

**Implication:** Different builds on the SAME git commit can produce different `.gc`
files if the sheets were edited between runs. The build timestamp is the true
provenance identifier, not the git SHA.

## Artifacts Preserved

11 artifacts downloaded from the Nov 17-21, 2025 window, capturing **5 distinct
states** of the UBL 2.5 entity model.

### .gc File Evolution

| Date/Time | UBL-Entities-2.5.gc | UBL-Endorsed-Entities-2.5.gc | Notes |
|-----------|:---:|:---:|---|
| Nov 17 (all 5 builds) | `fbff373c` | `b3c6953e` | Stable all day |
| Nov 19 (both builds) | `5c21797f` | `9069e372` | Sheets edited |
| Nov 20 10:10 | `5c21797f` | `9069e372` | Same as Nov 19 |
| Nov 20 13:50 | `c706354e` | `1f7d3616` | **NDR errors** - mid-edit |
| Nov 20 19:30 | `92ce4ba5` | `cbc7608f` | Fixed |
| Nov 21 12:41 | `396a25cb` | `4b66cbaf` | Continued evolution |

`UBL-Signature-Entities-2.5.gc` was stable throughout (1 hash: `64291c42`).

### ODS Source File Changes (Nov 17 → Nov 21)

| File | Size Change |
|------|-------------|
| UBL-Entities-2.5.ods | +24,983 bytes |
| UBL-Endorsed-Entities-2.5.ods | +24,256 bytes |
| UBL-Documents-Google.ods | +19,711 bytes |
| UBL-Library-Google.ods | +1,151 bytes |
| UBL-Signature-Google.ods | -1 byte |

## Build Pipeline Details

```
Tools: Java 1.8.0_472 (Zulu), Apache Ant 1.9.7, Saxon 9 HE,
       Crane utilities, LibreOffice, 7-Zip 23.01

Full build time: ~44 minutes (including 77 XSLT validation phases)
Truncated build (NDR errors): ~3.5 minutes
```

### Artifact Size Categories

| Size | ISO Package | Downstream | Cause |
|------|-------------|------------|-------|
| 68-79 MB | Empty | Skipped | NDR check failures |
| 74-75 MB | Empty | Skipped | Early build config |
| 178-181 MB | ~43 MB | Full (77 phases) | Clean build |

## Archive Location

All downloaded artifacts, extracted files, .gc snapshots, .ods sources, workflow
logs, and build summaries are stored at:

```
/home/user/ubl-artifacts/
```

Full provenance documentation: `/home/user/ubl-artifacts/PROVENANCE.md`

## Remaining Artifacts

| Expires | Count | Size | Action Needed |
|---------|-------|------|---------------|
| Feb 17-19 | 22 (remaining) | ~3.4 GB | Download more if unique states needed |
| Mar 3 | 2 | ~361 MB | Monitor, download before expiry |
| Apr 10-28 | 17 | ~1.9 GB | Safe for 2 months |
| May 10 | 7 | ~420 MB | Most recent (Feb 9), safe 3 months |

---

**Analysis performed:** 2026-02-15 by Claude Code session
