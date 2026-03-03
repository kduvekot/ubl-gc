# UBL 2.4 CSD01→CSD02: One BIE at a Time — ODS Revision Mapping

## Summary

Between UBL 2.4 CSD01 (lib-605, doc-157) and CSD02 (lib-673, doc-251), there are
**19 BIE-level changes** in the generated .gc file:
- 8 row additions in CommonLibrary
- 1 row removal in CommonLibrary (Shipment Stage. Environmental Emission)
- 1 row modification in CommonLibrary (Tax Category. Tax Scheme cardinality)
- 3 row additions in DespatchAdvice document model
- 4 row additions in ReceiptAdvice document model
- 2 row modifications in ReceiptAdvice document model

**Key finding:** The most granular natural ODS pair decomposition yields **13 steps**
covering 19 BIE changes. Of these, 9 steps have exactly 1 BIE change, 3 steps have
2 BIE changes, and 1 step has 4 BIE changes. Achieving true 1-BIE-per-step for all
19 changes requires programmatic .gc XML editing for 4 of the steps.

---

## The 19 BIE Changes (CSD01 → CSD02)

### CommonLibrary (10 changes, library ODS only)

| # | DictionaryEntryName | Type | Change |
|---|---------------------|------|--------|
| 1 | Tax Category. Tax Scheme | ASBIE | Cardinality: `1` → `0..1` |
| 2 | Despatch Line. Accounting Cost Code. Code | BBIE | **Added** (v=2.4) |
| 3 | Despatch Line. Accounting Cost. Text | BBIE | **Added** (v=2.4) |
| 4 | Package. Status | ASBIE | **Added** (v=2.4) |
| 5 | Receipt Line. Received\_ Time. Time | BBIE | **Added** (v=2.4) |
| 6 | Customs Declaration. Function Code. Code | BBIE | **Added** (v=2.4) |
| 7 | Transport Handling Unit. Damage Documentation\_ Attachment. Attachment | ASBIE | **Added** (v=2.4) |
| 8 | Fuel Consumption. Fuel Provider\_ Party. Party | ASBIE | **Added** (v=2.4) |
| 9 | Shipment Stage. Fuel Consumption | ASBIE | **Added** (v=2.4) |
| 10 | Shipment Stage. Environmental Emission | ASBIE | **Removed** |

### DespatchAdvice document model (3 changes, documents ODS only)

| # | DictionaryEntryName | Type | Change |
|---|---------------------|------|--------|
| 11 | Despatch Advice. Accounting Cost Code. Code | BBIE | **Added** (v=2.4) |
| 12 | Despatch Advice. Accounting Cost. Text | BBIE | **Added** (v=2.4) |
| 13 | Despatch Advice. Project Reference | ASBIE | **Added** (v=2.4) |

### ReceiptAdvice document model (6 changes, documents ODS only)

| # | DictionaryEntryName | Type | Change |
|---|---------------------|------|--------|
| 14 | Receipt Advice. Delivery\_ Acceptance Code. Code | BBIE | **Added** (v=2.4) |
| 15 | Receipt Advice. Reject Reason. Text | BBIE | **Added** (v=2.4) |
| 16 | Receipt Advice. Reject\_ Action Code. Code | BBIE | **Added** (v=2.4) |
| 17 | Receipt Advice. Reject\_ Reason Code. Code | BBIE | **Added** (v=2.4) |
| 18 | Receipt Advice. Details | ABIE | Definition text changed |
| 19 | Receipt Advice. Receipt Line | ASBIE | Cardinality: `1..n` → `0..n` |

---

## The 13-Step Natural ODS Pair Sequence

### Phase 1: Library-side BIEs (advance lib, doc stays at 157)

| Step | (lib, doc) | Rows | BIE changes | Count |
|------|-----------|------|-------------|-------|
| 0 (CSD01) | (605, 157) | 5429 | *baseline* | — |
| 1 | **(606, 157)** | 5429 | #1: Tax Scheme cardinality 1→0..1 | **1** |
| 2 | **(623, 157)** | 5431 | #2: +AccountingCostCode.Code, #3: +AccountingCost.Text | **2** |
| 3 | **(631, 157)** | 5432 | #4: +Package.Status | **1** |
| 4 | **(642, 157)** | 5433 | #5: +ReceiptLine.ReceivedTime | **1** |
| 5 | **(653, 157)** | 5434 | #6: +CustomsDecl.FunctionCode | **1** |
| 6 | **(665, 157)** | 5435 | #7: +THU.DamageDocAttachment | **1** |
| 7 | **(671, 157)** | 5436 | #8: +FuelConsumption.FuelProviderParty | **1** |
| 8 | **(673, 157)** | 5436 | #9: +ShipmentStage.FuelConsumption, #10: −ShipmentStage.EnvironmentalEmission | **2** |

### Phase 2: Document-side BIEs (lib stays at 673, advance doc)

| Step | (lib, doc) | Rows | BIE changes | Count |
|------|-----------|------|-------------|-------|
| 9 | **(673, 185)** | 5438 | #11: +DA.AccountingCostCode, #12: +DA.AccountingCost | **2** |
| 10 | **(673, 195)** | 5439 | #13: +DA.ProjectReference | **1** |
| 11 | **(673, 245)** | 5443 | #14-17: +4 ReceiptAdvice BIEs | **4** |
| 12 | **(673, 250)** | 5443 | #18: ~RA.Details definition changed | **1** |
| 13 (CSD02) | **(673, 251)** | 5443 | #19: ~RA.ReceiptLine cardinality 1..n→0..n | **1** |

---

## Steps That Cannot Be Separated (natural ODS pairs)

### Step 2: AccountingCostCode + AccountingCost (lib-side)

These two BIEs evolve together in the Library ODS through many intermediate renames:
- lib-611→612: first placeholder "Despatch Line. Quantity" added
- lib-612→613: second placeholder added (same DEN!)
- lib-613→617: both renamed through several wrong DENs
- lib-617: AccountingCostCode reaches final DEN; AccountingCost still wrong
- lib-618: AccountingCost reaches final DEN
- lib-619-620: version bumps (v2.0→v2.4)
- lib-621-623: EditorNotes finalized

**Why inseparable:** At every revision where one BIE has its correct DEN, the other also
exists (with either a placeholder or wrong DEN). There's no revision where exactly one
new BIE exists with a correct DEN and the other doesn't exist at all.

**For 1-BIE-at-a-time:** Edit the .gc XML directly to add one row, then the other.

### Step 8: FuelConsumption/EnvironmentalEmission (lib-side)

This is semantically a **rename**: Shipment Stage. Environmental Emission →
Shipment Stage. Fuel Consumption. In the GC it manifests as +1 row, -1 row.

- lib-671→672: Environmental Emission definition text changes (preparation)
- lib-672→673: DEN changes from "Environmental Emission" to "Fuel Consumption"

**Arguably 1 logical BIE change** (a rename), but 2 row-level changes.

### Step 9: DespatchAdvice AccountingCostCode + AccountingCost (doc-side)

Both rows appear as "Note. Text" placeholders at doc-159-160 and are refined together:
- doc-160: 2× "Note. Text" placeholders
- doc-170: partially renamed ("Accounting Cost_ Code Note. Text")
- doc-175: "Accounting Cost Code. Text" + "Accounting Cost. Text"
- doc-176: AccountingCostCode corrected to ".Code"
- doc-177-185: version and notes refinement
- doc-185: both at final state (v=2.4)

**Why inseparable:** Both rows are always refined together at each revision.

### Step 11: 4 ReceiptAdvice BIEs (doc-side)

All 4 BIEs were added simultaneously at doc-215→216 (44 cells = 4 rows × 11 columns)
and then refined together through doc-251:
- doc-216: 4× "Note. Text" placeholders
- doc-230: partially renamed (2 of 4)
- doc-240: all 4 have final DENs (v=2.0)
- doc-245: all 4 at v=2.4 (finalized)

**Why inseparable:** The editor added all 4 rows in a single edit at doc-216. They
always appear together.

---

## Approach for True 1-BIE-at-a-Time

For the 4 multi-BIE steps (2, 8, 9, 11), use **programmatic .gc XML editing**:

1. Generate the .gc from an ODS pair at the previous step
2. Parse the XML, add/remove exactly one `<Row>` element
3. Write the modified .gc

The row content for each BIE can be extracted from the final CSD02 .gc file
(`history/csd02-UBL-2.4/mod/UBL-Entities-2.4.gc`).

This would expand the 13 natural steps to 19 steps (one per BIE).

---

## ODS File Locations

All ODS files are available on Google Drive and cached locally at:
- Library: `/tmp/ubl24-ods/library/rev-{N}.ods` (revisions 605-673)
- Documents: `/tmp/ubl24-ods/documents/rev-{N}.ods` (revisions 157-251)

Download script: `.github/scripts/download-ods-revision.py`
(uses Google Drive folder IDs for UBL 2.4)

Conversion pipeline: `.github/scripts/validate-gc-pipeline.sh`
(Saxon 9 HE + Crane-ods2obdgc.xsl)

---

## Data Sources

- Library ODS diff: `/tmp/ubl24-lib-diff.json` (68 transitions, 605→673)
- Documents ODS diff: `/tmp/ubl24-doc-diff.json` (94 transitions, 157→251)
- Revision-to-fileID mapping: `/tmp/ubl24-rev-ids.json`
- Generated .gc files: `/tmp/gc-matrix/lib{N}-doc{M}.gc`
- ODS diff tool: `work-sheets/scripts/diff-ods-revisions.py`
