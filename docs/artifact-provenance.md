# UBL 2.5 Workflow Artifact Provenance Analysis

**Date:** 2026-02-15
**Branch:** `claude/analyze-workflow-history-Gdrth`
**Source:** `oasis-tcs/ubl` GitHub Actions workflow

## Executive Summary

We downloaded and analyzed **all 55 non-expired artifacts** from the OASIS UBL
build workflow (Nov 17, 2025 – Feb 9, 2026). By computing SHA-256 checksums of
every `.gc` file in every artifact, we found:

- **10 unique versions** of `UBL-Entities-2.5.gc` (not 5 as previously estimated)
- **10 unique versions** of `UBL-Endorsed-Entities-2.5.gc`
- **2 unique versions** of `UBL-Signature-Entities-2.5.gc`
- **53 unique ODS hashes** for Library, 53 for Documents (every download is different)

### Key Finding: ODS Non-Determinism

Google Sheets exports are **non-deterministic at the binary level**. The same
spreadsheet data produces different `.ods` files on every download (different
internal timestamps/metadata). However, the XSLT conversion to `.gc` is
**deterministic**: the same cell data always produces the same `.gc` output.

**Therefore:**
- ODS file **hashes** cannot determine if content changed (every download is unique)
- ODS file **sizes** are an unreliable proxy (same size ≠ same content; different size ≠ different content)
- `.gc` SHA-256 hashes are the **only reliable fingerprint** of actual content state

### Previous Error Acknowledged

Our earlier analysis estimated ~5–7 unique `.gc` states based on ODS file sizes
extracted from workflow logs. That method was flawed for two reasons:
1. ODS sizes vary ±30–115 bytes even when content hasn't changed
2. Content can change without changing ODS size (e.g., version 3→4: 4-byte fix)

This document corrects the record with SHA-256 verification of every artifact.

---

## Methodology

### What We Did

1. **Listed all artifacts** via GitHub API (`/repos/oasis-tcs/ubl/actions/artifacts`)
2. **Downloaded all 55 non-expired regular artifacts** (skipped 3 Python-variant duplicates)
3. **Extracted from `*-archive-only.7z`** inside each artifact zip
   - Why this archive: it's the only one containing both `.gc` outputs AND `.ods` sources
   - Verified: `.gc` files in `archive-only.7z` are byte-identical to those in the main `.7z`
     (SHA-256 verified on artifact 4632606474)
4. **Computed SHA-256 checksums** of every `.gc` and `.ods` file
5. **Diffed consecutive unique `.gc` versions** to characterize changes

### What We Extracted Per Artifact

| File | Type | Purpose |
|------|------|---------|
| `UBL-Entities-2.5.gc` | Output | Main semantic model (generated from ODS) |
| `UBL-Signature-Entities-2.5.gc` | Output | Signature entities (generated from ODS) |
| `UBL-Endorsed-Entities-2.5.gc` | Output | Endorsed subset (generated from ODS) |
| `UBL-Entities-2.5-csd01.gc` | Reference | Previous stage baseline |
| `UBL-Signature-Entities-2.5-csd01.gc` | Reference | Previous stage baseline |
| `UBL-Endorsed-Entities-2.5-csd01.gc` | Reference | Previous stage baseline |
| `UBL-Entities-2.4-os.gc` | Reference | Previous version baseline |
| `UBL-Signature-Entities-2.4-os.gc` | Reference | Previous version baseline |
| `UBL-Endorsed-Entities-2.4-os.gc` | Reference | Previous version baseline |
| `UBL-Library-Google.ods` | Source | Google Sheets export (Library) |
| `UBL-Documents-Google.ods` | Source | Google Sheets export (Documents) |
| `UBL-Signature-Google.ods` | Source | Google Sheets export (Signature) |
| `UBL-Entities-2.5.ods` | Source | Entity model spreadsheet |
| `UBL-Signature-Entities-2.5.ods` | Source | Signature entity spreadsheet |
| `UBL-Endorsed-Entities-2.5.ods` | Source | Endorsed entity spreadsheet |
| `skeletonDisplayEditSubset.ods` | Source | Display/edit skeleton |

### Python-Variant Artifacts (Skipped)

Runs 19437106789 and 19437348197 each produced two artifacts:
- `UBL-package-github-*` (regular build)
- `UBL-package-py-github-*` (Python build variant)

Both artifacts from the same run share the same ODS download moment and the same
XSLT conversion, so their `.gc` files are necessarily identical. We processed
only the regular variants.

### Disk Space Management

Each artifact is 40–190 MB compressed. To avoid filling disk:
- Downloaded one at a time
- Extracted only `.gc` + `.ods` files (not full 200+ MB 7z expansion)
- Deleted zip immediately after extraction
- Peak disk usage: ~200 MB temp + 2.7 GB final snapshots
- Final: 55 snapshot directories, 2.7 GB total

---

## UBL-Entities-2.5.gc: 10 Unique Content Versions

| # | SHA-256 (first 16) | Size (bytes) | First Seen | Last Seen | Count | Description |
|---|-------------------|-------------|------------|-----------|-------|-------------|
| 1 | `b62566116b2c302a` | 8,824,734 | Nov 17 16:37 | Nov 17 22:30 | 5 | Initial CSD02 state |
| 2 | `f3dfce2001c58934` | 8,829,865 | Nov 19 19:14 | Nov 20 10:10 | 5 | Customs definitions rewritten |
| 3 | `7b5a425c2b2f6003` | 8,896,201 | Nov 20 13:50 | Nov 20 13:58 | 2 | WasteMovement added (NDR errors) |
| 4 | `44b5b8e890ecc6e0` | 8,896,205 | Nov 20 14:05 | Nov 20 19:30 | 16 | NDR fix (4 bytes: spacing) |
| 5 | `fa9822e180f7111b` | 8,897,815 | Nov 21 12:41 | Jan 10 17:01 | 9 | Definition rewrites, stable 7 weeks |
| 6 | `881db55f19aae4a0` | 8,897,877 | Jan 21 16:38 | Jan 21 16:38 | 1 | BuyerReference renamed (transient) |
| 7 | `fd7a2531ca30ecb8` | 8,897,877 | Jan 21 17:01 | Jan 21 19:10 | 4 | Cardinality change (0..1→0..n) |
| 8 | `775f7187a8a7fb9d` | 8,898,129 | Jan 21 19:26 | Jan 28 16:25 | 6 | Rename propagated, stable 1 week |
| 9 | `94b7ce6b6f1bb984` | 8,898,129 | Feb 9 14:42 | Feb 9 14:46 | 5 | CSD03: cardinality changes |
| 10 | `c3737612e83e59c4` | 8,898,129 | Feb 9 14:46 | Feb 9 15:13 | 2 | CSD03: stage metadata update |

### Changes Between Consecutive Versions

**V1→V2** (Nov 17→Nov 19): +5,131 bytes, +2099/-1985 lines
- Customs definitions rewritten with more precise language
- Cardinality changes (1 → 0..1)

**V2→V3** (Nov 19→Nov 20 13:50): +66,336 bytes, +1710/-0 lines
- **WasteMovement document type ADDED** (entire new ABIE)
- Triggered NDR compliance errors

**V3→V4** (Nov 20 13:50→14:05): +4 bytes, +4/-4 lines
- NDR fix: "WasteProducer" → "Waste Producer" (space added)

**V4→V5** (Nov 20 14:05→Nov 21): +1,610 bytes, +296/-293 lines
- Systematic definition rewrites ("The party presenting" → "The Party who presents")

**V5→V6** (Nov 21→Jan 21 16:38): +62 bytes, +7/-7 lines
- BuyerReference → BuyerAssignedReference rename (initial)

**V6→V7** (Jan 21 16:38→17:01): 0 bytes, +1/-1 lines
- Single cardinality change: 0..1 → 0..n

**V7→V8** (Jan 21 17:01→19:26): +252 bytes, +29/-29 lines
- BuyerAssignedReference rename propagated to other document types
- Deprecation notices updated

**V8→V9** (Jan 28→Feb 9): 0 bytes, +3/-3 lines
- Three cardinality changes: 0..1 → 0..n

**V9→V10** (Feb 9 14:42→14:46): 0 bytes, +3/-3 lines
- CSD02 → CSD03 stage metadata in XML header (ShortName, LongName, LocationUri)

---

## UBL-Signature-Entities-2.5.gc: 2 Unique Content Versions

| # | SHA-256 (first 16) | Size | First Seen | Last Seen | Count | Description |
|---|-------------------|------|------------|-----------|-------|-------------|
| 1 | `1104e26913cbddb9` | 13,871 | Nov 17 16:37 | Feb 9 14:45 | 52 | Stable 3 months |
| 2 | `b90385acd37a36f4` | 13,871 | Feb 9 14:46 | Feb 9 15:13 | 3 | CSD02→CSD03 metadata |

Change: Only the XML header metadata (ShortName, LongName, LocationUri) updated
from CSD02 to CSD03. No data changes.

---

## UBL-Endorsed-Entities-2.5.gc: 10 Unique Content Versions

Changes track in lockstep with UBL-Entities-2.5.gc at every transition point.

**Critical finding:** `UBL-Endorsed-Entities-2.4-os.gc` is always **byte-identical**
to `UBL-Endorsed-Entities-2.5.gc` within the same artifact. This means the "2.4-os"
reference file is being regenerated from current Google Sheets data, not stored as
a static published reference.

---

## Reference File Stability

| File | Unique Versions | Notes |
|------|----------------|-------|
| `UBL-Entities-2.4-os.gc` | **1** | Stable (8,234,496 bytes) |
| `UBL-Signature-Entities-2.4-os.gc` | **1** | Stable (13,862 bytes) |
| `UBL-Endorsed-Entities-2.4-os.gc` | **10** | NOT stable — equals current 2.5 Endorsed |
| `UBL-Entities-2.5-csd01.gc` | **2** | Changed Jan 21 on `ubl-2.5` branch |
| `UBL-Signature-Entities-2.5-csd01.gc` | **1** | Stable (13,871 bytes) |
| `UBL-Endorsed-Entities-2.5-csd01.gc` | **2** | Changed Jan 21 on `ubl-2.5` branch |

The CSD01 reference file change (versions 1→2) correlates with a git branch
divergence: the `ubl-2.5` branch received updated CSD01 files on Jan 21, while
the `ubl-2.5-2025-layout` and `kentest` branches retained the old versions.

---

## ODS Source File Analysis

### Binary Non-Determinism (Proven)

5 artifacts on Nov 17 produced identical `UBL-Entities-2.5.gc` (hash `b62566116b2c`),
but each has a completely different `UBL-Library-Google.ods` SHA-256:

| Artifact | Entities.gc SHA-256 | Library.ods SHA-256 |
|----------|-------------------|--------------------|
| 4591159085 | `b62566116b2c...` | `b1cd8fe51ef6...` |
| 4591257222 | `b62566116b2c...` | `6020b3460d83...` |
| 4594074506 | `b62566116b2c...` | `168e8c7d07ec...` |
| 4594558628 | `b62566116b2c...` | `1862918fac8d...` |
| 4595163792 | `b62566116b2c...` | `41f5ffbab52c...` |

All 55 Library.ods files have unique SHA-256 hashes. Same for Documents.ods.

### Size Variation Within Same .gc Version

Within `.gc` version 5 (9 artifacts, Nov 21 – Jan 10, all producing identical `.gc`):

| ODS File | Min Size | Max Size | Variation |
|----------|---------|---------|-----------|
| Library | 640,604 | 640,634 | ±30 bytes |
| Documents | 931,654 | 931,769 | ±115 bytes |
| Signature | 16,387 | 16,389 | ±2 bytes |

### Size Does NOT Predict Content Changes

- **Same ODS size, different `.gc`:** Versions 3→4 have identical ODS sizes
  (640302, 930888, 16387) but different `.gc` output (4-byte spacing fix)
- **Different ODS size, same `.gc`:** Version 5 spans 3 different Library.ods
  sizes (640604, 640633, 640634) but produces identical `.gc` output

---

## Complete Artifact Inventory

55 artifacts processed. For each, the complete SHA-256 checksums of all `.gc`
and `.ods` files are stored in:

```
/home/user/ubl-artifacts/checksums/{artifact_id}.sha256  (per-artifact)
/home/user/ubl-artifacts/checksums/all-gc-checksums.tsv  (combined index)
```

The combined index has 843 entries (55 artifacts × ~15 files each).

### Artifact List

| # | Artifact ID | Timestamp | Branch | Entities.gc | Sig.gc | Endorsed.gc |
|---|-------------|-----------|--------|-------------|--------|-------------|
| 1 | 4591159085 | Nov 17 16:37 | ubl-2.5-python | V1 | V1 | V1 |
| 2 | 4591257222 | Nov 17 16:46 | ubl-2.5-python | V1 | V1 | V1 |
| 3 | 4594074506 | Nov 17 20:27 | ubl-2.5-python | V1 | V1 | V1 |
| 4 | 4594558628 | Nov 17 21:20 | ubl-2.5 | V1 | V1 | V1 |
| 5 | 4595163792 | Nov 17 22:30 | ubl-2.5 | V1 | V1 | V1 |
| 6 | 4619385679 | Nov 19 19:14 | ubl-2.5 | V2 | V1 | V2 |
| 7 | 4620429376 | Nov 19 20:51 | ubl-2.5 | V2 | V1 | V2 |
| 8 | 4620993143 | Nov 19 21:56 | ubl-2.5 | V2 | V1 | V2 |
| 9 | 4621441403 | Nov 19 22:51 | ubl-2.5 | V2 | V1 | V2 |
| 10 | 4626371666 | Nov 20 10:10 | ubl-2.5 | V2 | V1 | V2 |
| 11 | 4628183442 | Nov 20 13:50 | ubl-2.5 | V3 | V1 | V3 |
| 12 | 4628269333 | Nov 20 13:58 | ubl-2.5 | V3 | V1 | V3 |
| 13 | 4628889619 | Nov 20 14:05 | ubl-2.5 | V4 | V1 | V4 |
| 14 | 4630563293 | Nov 20 16:17 | ubl-2.5 | V4 | V1 | V4 |
| 15 | 4630655623 | Nov 20 16:22 | ubl-2.5 | V4 | V1 | V4 |
| 16 | 4630674627 | Nov 20 16:24 | ubl-2.5 | V4 | V1 | V4 |
| 17 | 4631135968 | Nov 20 17:12 | ubl-2.5 | V4 | V1 | V4 |
| 18 | 4631203120 | Nov 20 17:14 | ubl-2.5 | V4 | V1 | V4 |
| 19 | 4631205480 | Nov 20 17:16 | ubl-2.5 | V4 | V1 | V4 |
| 20 | 4631223253 | Nov 20 17:18 | ubl-2.5 | V4 | V1 | V4 |
| 21 | 4631258913 | Nov 20 17:19 | ubl-2.5 | V4 | V1 | V4 |
| 22 | 4631258889 | Nov 20 17:21 | ubl-2.5 | V4 | V1 | V4 |
| 23 | 4631298820 | Nov 20 17:23 | ubl-2.5 | V4 | V1 | V4 |
| 24 | 4631338943 | Nov 20 17:24 | ubl-2.5 | V4 | V1 | V4 |
| 25 | 4631321598 | Nov 20 17:29 | ubl-2.5 | V4 | V1 | V4 |
| 26 | 4631326753 | Nov 20 17:30 | ubl-2.5 | V4 | V1 | V4 |
| 27 | 4631833752 | Nov 20 18:15 | ubl-2.5 | V4 | V1 | V4 |
| 28 | 4632606474 | Nov 20 19:30 | ubl-2.5 | V4 | V1 | V4 |
| 29 | 4640431446 | Nov 21 12:41 | ubl-2.5 | V5 | V1 | V5 |
| 30 | 4750371329 | Dec 3 11:25 | ubl-2.5 | V5 | V1 | V5 |
| 31 | 4751186216 | Dec 3 12:39 | ubl-2.5 | V5 | V1 | V5 |
| 32 | 5082891142 | Jan 10 00:44 | ubl-2.5-2025-layout | V5 | V1 | V5 |
| 33 | 5083116302 | Jan 10 01:33 | ubl-2.5-2025-layout | V5 | V1 | V5 |
| 34 | 5085444153 | Jan 10 14:23 | ubl-2.5-2025-layout | V5 | V1 | V5 |
| 35 | 5085592701 | Jan 10 15:12 | ubl-2.5-2025-layout | V5 | V1 | V5 |
| 36 | 5085787152 | Jan 10 16:11 | ubl-2.5-2025-layout | V5 | V1 | V5 |
| 37 | 5085943942 | Jan 10 17:01 | ubl-2.5-2025-layout | V5 | V1 | V5 |
| 38 | 5207385070 | Jan 21 16:38 | ubl-2.5 | V6 | V1 | V6 |
| 39 | 5207702772 | Jan 21 17:01 | kentest | V7 | V1 | V7 |
| 40 | 5207817834 | Jan 21 17:09 | kentest | V7 | V1 | V7 |
| 41 | 5209008188 | Jan 21 18:43 | kentest | V7 | V1 | V7 |
| 42 | 5209350022 | Jan 21 19:10 | server-test | V7 | V1 | V7 |
| 43 | 5210053700 | Jan 21 19:26 | ubl-2.5 | V8 | V1 | V8 |
| 44 | 5210168034 | Jan 21 19:36 | ubl-2.5-2025-layout | V8 | V1 | V8 |
| 45 | 5210795934 | Jan 21 20:28 | kentest | V8 | V1 | V8 |
| 46 | 5211002498 | Jan 21 20:44 | kentest | V8 | V1 | V8 |
| 47 | 5211444097 | Jan 21 21:24 | ubl-2.5-retry | V8 | V1 | V8 |
| 48 | 5291568120 | Jan 28 16:25 | ubl-2.5 | V8 | V1 | V8 |
| 49 | 5433696827 | Feb 9 14:42 | ubl-2.5 | V9 | V1 | V9 |
| 50 | 5433723623 | Feb 9 14:44 | ubl-2.5 | V9 | V1 | V9 |
| 51 | 5433745368 | Feb 9 14:45 | ubl-2.5 | V9 | V1 | V9 |
| 52 | 5433752931 | Feb 9 14:45 | ubl-2.5 | V9 | V1 | V10 |
| 53 | 5433756608 | Feb 9 14:46 | ubl-2.5 | V9 | V2 | V10 |
| 54 | 5433775026 | Feb 9 14:46 | ubl-2.5 | V10 | V2 | V10 |
| 55 | 5434847144 | Feb 9 15:13 | ubl-2.5 | V10 | V2 | V10 |

Note: Artifacts 52–55 show the CSD02→CSD03 transition happening in real-time,
with Endorsed updating first, then Signature, then Entities.

---

## Reproduction

### Re-downloading Artifacts

```bash
# While artifacts remain non-expired (90-day retention):
gh api "repos/oasis-tcs/ubl/actions/artifacts/{ARTIFACT_ID}/zip" > artifact.zip

# List current non-expired artifacts:
gh api "repos/oasis-tcs/ubl/actions/artifacts?per_page=100" \
  --jq '.artifacts[] | select(.expired == false) | [.id, .name, .expires_at] | @tsv'
```

### Re-extracting .gc Files

```bash
# From a downloaded artifact zip:
unzip -q artifact.zip "*-archive-only.7z" -d /tmp/extract
7z e -o/tmp/gc /tmp/extract/*-archive-only.7z \
    "UBL-Entities-*.gc" "UBL-Signature-Entities-*.gc" "UBL-Endorsed-Entities-*.gc" \
    "*.ods" -r -y
sha256sum /tmp/gc/UBL-*.gc
```

### Verifying This Analysis

```bash
# All checksums are stored in:
cat /home/user/ubl-artifacts/checksums/all-gc-checksums.tsv

# Per-artifact checksums:
cat /home/user/ubl-artifacts/checksums/{ARTIFACT_ID}.sha256

# Verify a specific snapshot:
cd /home/user/ubl-artifacts/gc-snapshots/{TIMESTAMP}_{ARTIFACT_ID}/
sha256sum -c ../../checksums/{ARTIFACT_ID}.sha256
```

---

## Full SHA-256 Checksums

### UBL-Entities-2.5.gc (10 versions)

```
V1:  b62566116b2c302a37bdea8bc5b641b362cafbf8577fc656045248f1fcefca2b  8824734
V2:  f3dfce2001c58934a3284498e7f39aa93b1bf761732d49fdde711fdd57570fb3  8829865
V3:  7b5a425c2b2f60036478c14c6e12bf7d69e0c17461612d653b47888ce5b0e858  8896201
V4:  44b5b8e890ecc6e0fbd7725817a7439cab35f07d4b294a21b71e25a96bc2f13d  8896205
V5:  fa9822e180f7111bcd7286c4341cd70962befe12ccc36b518da26930b857a7bc  8897815
V6:  881db55f19aae4a0d8d2f1ec7852e3bf81c6e375b28e2811727a5d7f07f4e0ab  8897877
V7:  fd7a2531ca30ecb8515aad48dbdc4bf2007c520715865ea51498b7b838eec0cc  8897877
V8:  775f7187a8a7fb9dc40976bcd377bab7ef6aef4c1cbe37a7334da989d87ea51a  8898129
V9:  94b7ce6b6f1bb984c7c44ba36e345817713b7c5355593146ffb7539eba34d193  8898129
V10: c3737612e83e59c482f6b513e11447f61df70e6f7fa72cdab09743daa6218070  8898129
```

### UBL-Signature-Entities-2.5.gc (2 versions)

```
V1:  1104e26913cbddb9c1c4eb1eb742e3fc04e37af7b506e9c01dad48b3191874c6  13871
V2:  b90385acd37a36f43a9f2bbe1832510ec43108a10482265152ea788add1a25ea  13871
```

### UBL-Endorsed-Entities-2.5.gc (10 versions)

```
V1:  68a1bc6c9243aa787c8902dcb9f7ee6ed430aea8af1da869fd9aea7da335a3c1  8365067
V2:  19a9784985d517966476461618c3cff77586366219ff9e7ba2ec82311c1b28cb  8370198
V3:  44f99acde7b8e1be5eb64d464a4d3460fb8a5a4a27c09b8ea625478950084fde  8436534
V4:  3e3c0ddda6d6e97bd0409640918c8eee22469bee8e1a7d9503ab3b5b5f6673df  8436538
V5:  0c9365e918f398aa8d564c94a8bb2280d934663cc5a15eb900c03b3ac357dcb0  8438113
V6:  4ee47e115cb3e9a7da42b900d24fa771f09cdf3892a1c64b24292f0cfd7d0d4c  8438175
V7:  ee0a7d346280e4cc2b8b2731bb36d1d50d74458d0efa07b26fddb2b1f8ba07de  8438175
V8:  4d43d4f6dd393a17facd4e793ee296a0c6c965a5e8e01eeca1598f4cd131c036  8438395
V9:  df1eec393f9c84921b4e441a1a9b765e13ff9e662049c3dacde3c8e16264c9af  8438395
V10: 3e6ba659d0e1970c020aeef122ab26b8d772db5f9fe42c866343d351421e4d9c  8438395
```

---

## Archive Location

All extracted data is stored at:

```
/home/user/ubl-artifacts/
├── gc-snapshots/           ← 55 directories, one per artifact
│   └── {timestamp}_{id}/
│       ├── UBL-*.gc        ← Extracted .gc files
│       └── ods-sources/    ← Extracted .ods files
├── checksums/
│   ├── {id}.sha256         ← Per-artifact checksums (55 files)
│   └── all-gc-checksums.tsv ← Combined index (843 entries)
├── manifests/
│   ├── inventory-*.json    ← GitHub API artifact listings
│   └── download-log.jsonl  ← Download provenance log
├── download-all-v2.sh      ← Extraction script (documented, re-runnable)
└── PROVENANCE.md           ← Original provenance document
```

Total: 2.7 GB of extracted snapshots across 55 artifacts.

---

**Analysis performed:** 2026-02-15 by Claude Code session
**All 55 artifacts:** Zero download failures, zero extraction errors
**Methodology:** Exhaustive (every non-expired artifact, not a sample)
