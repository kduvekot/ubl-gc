# UBL GenericCode Column Structure Analysis

This document captures the complete column structure across all 35 UBL releases
and analyzes what changes at each major version transition. This analysis informs
the commit strategy for the git history branch.

---

## Column Structures by Version

### UBL 2.0 Entities (8 releases)

UBL 2.0 has **three distinct column structures** across its 8 releases:

#### prd (49 columns)

The first public review draft includes 18 extra `SmallBusinessSubset*` columns
for various document types. These are subset markers removed in subsequent releases.

<details>
<summary>Full column list (49 columns)</summary>

1. ModelName
2. UBLName
3. DictionaryEntryName
4. ObjectClassQualifier
5. ObjectClass
6. PropertyTermQualifier
7. PropertyTermPossessiveNoun
8. PropertyTermPrimaryNoun
9. PropertyTerm
10. RepresentationTerm
11. DataType
12. AssociatedObjectClassQualifier
13. AssociatedObjectClass
14. AlternativeBusinessTerms
15. Cardinality
16. ComponentType
17. Definition
18. Examples
19. UNTDEDCode
20. CurrentVersion
21. AnalystNotes
22. CandidateCCID
23. ContextBusinessProcess
24. ContextRegionGeopolitical
25. ContextOfficialConstraints
26. ContextProduct
27. ContextIndustry
28. ContextRole
29. ContextSupportingRole
30. ContextSystemConstraint
31. EditorsNotes
32–49. SmallBusinessSubset* (18 document-type columns)
</details>

#### prd2 through os (31 columns)

The stable standard structure used by 6 of 8 releases. The 18 SmallBusinessSubset
columns were removed.

| # | Column ID |
|---|-----------|
| 1 | ModelName |
| 2 | UBLName |
| 3 | DictionaryEntryName |
| 4 | ObjectClassQualifier |
| 5 | ObjectClass |
| 6 | PropertyTermQualifier |
| 7 | PropertyTermPossessiveNoun |
| 8 | PropertyTermPrimaryNoun |
| 9 | PropertyTerm |
| 10 | RepresentationTerm |
| 11 | DataType |
| 12 | AssociatedObjectClassQualifier |
| 13 | AssociatedObjectClass |
| 14 | AlternativeBusinessTerms |
| 15 | Cardinality |
| 16 | ComponentType |
| 17 | Definition |
| 18 | Examples |
| 19 | UNTDEDCode |
| 20 | CurrentVersion |
| 21 | AnalystNotes |
| 22 | CandidateCCID |
| 23 | ContextBusinessProcess |
| 24 | ContextRegionGeopolitical |
| 25 | ContextOfficialConstraints |
| 26 | ContextProduct |
| 27 | ContextIndustry |
| 28 | ContextRole |
| 29 | ContextSupportingRole |
| 30 | ContextSystemConstraint |
| 31 | EditorsNotes |

#### os-update and errata (32 columns)

One column added to track changes in the update package:

| # | Column ID | Change |
|---|-----------|--------|
| 1–31 | *(same as above)* | Unchanged |
| 32 | ChangesforUBL20UpdatePackage | **Added** |

### UBL 2.0 Column Changes Summary

| Transition | Change | Columns |
|------------|--------|---------|
| prd → prd2 | Removed 18 SmallBusinessSubset* columns | 49 → 31 |
| prd2 → prd3 | No change | 31 |
| prd3 → prd3r1 | No change | 31 |
| prd3r1 → cs | No change | 31 |
| cs → os | No change | 31 |
| os → os-update | Added ChangesforUBL20UpdatePackage | 31 → 32 |
| os-update → errata | No change | 32 |

---

### UBL 2.1 Entities (33 columns)

All 8 releases (prd1 through os) share the same 33-column structure.

| # | Column ID |
|---|-----------|
| 1 | ModelName |
| 2 | UBLName |
| 3 | DictionaryEntryName |
| 4 | ObjectClassQualifier |
| 5 | ObjectClass |
| 6 | PropertyTermQualifier |
| 7 | PropertyTermPossessiveNoun |
| 8 | PropertyTermPrimaryNoun |
| 9 | PropertyTerm |
| 10 | RepresentationTerm |
| 11 | DataTypeQualifier |
| 12 | DataType |
| 13 | AssociatedObjectClassQualifier |
| 14 | AssociatedObjectClass |
| 15 | AlternativeBusinessTerms |
| 16 | Cardinality |
| 17 | ComponentType |
| 18 | Definition |
| 19 | Examples |
| 20 | UNTDEDCode |
| 21 | CurrentVersion |
| 22 | CCLDictionaryEntryName |
| 23 | AnalystNotes |
| 24 | CandidateCCID |
| 25 | ChangesfromPreviousVersion |
| 26 | ContextBusinessProcess |
| 27 | ContextRegionGeopolitical |
| 28 | ContextOfficialConstraints |
| 29 | ContextProduct |
| 30 | ContextIndustry |
| 31 | ContextRole |
| 32 | ContextSupportingRole |
| 33 | ContextSystemConstraint |

---

### UBL 2.2–2.4 Entities (23 columns)

All releases from UBL 2.2 csprd01 through UBL 2.4 os share the same 23-column
structure. This is the "modernized" schema introduced in 2.2.

| # | Column ID |
|---|-----------|
| 1 | ModelName |
| 2 | ComponentName |
| 3 | DictionaryEntryName |
| 4 | ObjectClassQualifier |
| 5 | ObjectClass |
| 6 | PropertyTermQualifier |
| 7 | PropertyTermPossessiveNoun |
| 8 | PropertyTermPrimaryNoun |
| 9 | PropertyTerm |
| 10 | RepresentationTerm |
| 11 | DataTypeQualifier |
| 12 | DataType |
| 13 | AssociatedObjectClassQualifier |
| 14 | AssociatedObjectClass |
| 15 | AlternativeBusinessTerms |
| 16 | Cardinality |
| 17 | ComponentType |
| 18 | Definition |
| 19 | Examples |
| 20 | UNTDEDCode |
| 21 | CurrentVersion |
| 22 | Subset |
| 23 | ChangesfromPreviousVersion |

---

### UBL 2.5 Entities (27 columns)

Four new columns added on top of the 2.2–2.4 structure.

| # | Column ID | New? |
|---|-----------|------|
| 1 | ModelName | |
| 2 | ComponentName | |
| 3 | DictionaryEntryName | |
| 4 | ObjectClassQualifier | |
| 5 | ObjectClass | |
| 6 | PropertyTermQualifier | |
| 7 | PropertyTermPossessiveNoun | |
| 8 | PropertyTermPrimaryNoun | |
| 9 | PropertyTerm | |
| 10 | RepresentationTerm | |
| 11 | DataTypeQualifier | |
| 12 | DataType | |
| 13 | AssociatedObjectClassQualifier | |
| 14 | AssociatedObjectClass | |
| 15 | AlternativeBusinessTerms | |
| 16 | Cardinality | |
| 17 | EndorsedCardinality | **New in 2.5** |
| 18 | EndorsedCardinalityRationale | **New in 2.5** |
| 19 | ComponentType | |
| 20 | Definition | |
| 21 | DeprecatedDefinition | **New in 2.5** |
| 22 | Examples | |
| 23 | UNTDEDCode | |
| 24 | CurrentVersion | |
| 25 | LastChanged | **New in 2.5** |
| 26 | Subset | |
| 27 | ChangesfromPreviousVersion | |

---

### Signature-Entities (2.1–2.5): 33 columns, unchanged

The Signature-Entities file maintains the same 33-column structure from UBL 2.1
through UBL 2.5. Its schema never changes across any version transition.

The columns are identical to the UBL 2.1 Entities structure listed above.

---

### Endorsed-Entities (2.5 only)

New file type introduced in UBL 2.5. Uses the same 27-column structure as the
UBL 2.5 Entities file.

---

## Major Version Transitions

### Transition 1: UBL 2.0 → 2.1

| Change | Columns Affected |
|--------|-----------------|
| **Added** | DataTypeQualifier, CCLDictionaryEntryName, ChangesfromPreviousVersion |
| **Removed** | ChangesforUBL20UpdatePackage, EditorsNotes |
| **Kept** | 30 columns carried forward |
| **Net** | 32 → 33 columns |

**New file introduced:** UBL-Signature-Entities-2.1.gc (first appearance)

**Data migration?** No. The removed `CandidateCCID` column (still present in 2.1
but later removed in 2.2) and added `CCLDictionaryEntryName` column are not
related by data: `CandidateCCID` had only 1 populated value out of ~606 rows
("UN00000069"), while `CCLDictionaryEntryName` starts entirely empty in 2.1.

### Transition 2: UBL 2.1 → 2.2 (Major Schema Restructure)

This is the largest schema change in UBL history.

| Change | Columns Affected |
|--------|-----------------|
| **Added** | ComponentName, Subset |
| **Removed** | UBLName, AnalystNotes, CandidateCCID, CCLDictionaryEntryName, ContextBusinessProcess, ContextRegionGeopolitical, ContextOfficialConstraints, ContextProduct, ContextIndustry, ContextRole, ContextSupportingRole, ContextSystemConstraint |
| **Kept** | 21 columns carried forward |
| **Net** | 33 → 23 columns (10 columns removed, 2 added) |

**Data migration?** No. Despite the similar roles of `UBLName` and
`ComponentName` (both are human-readable names), they contain different data:
- `UBLName` held root document type names (e.g., "ApplicationResponse")
- `ComponentName` holds individual XML component names (e.g., "ID",
  "BuyerCustomerParty")

The entire model was restructured: row count changed from 4,112 (2.1 os) to
4,657 (2.2 csprd01). This is not a column rename but a fundamental schema
reorganization.

### Transition 3: UBL 2.2 → 2.3

**No column changes.** The 23-column structure is identical. Only filenames change
(version number in filename: 2.2 → 2.3) and data content updates.

### Transition 4: UBL 2.3 → 2.4

**No column changes.** The 23-column structure is identical. Only filenames change
(version number in filename: 2.3 → 2.4) and data content updates.

### Transition 5: UBL 2.4 → 2.5

| Change | Columns Affected |
|--------|-----------------|
| **Added** | EndorsedCardinality, EndorsedCardinalityRationale, DeprecatedDefinition, LastChanged |
| **Removed** | *(none)* |
| **Kept** | All 23 columns from 2.4 |
| **Net** | 23 → 27 columns |

**New file introduced:** UBL-Endorsed-Entities-2.5.gc (first appearance)

**Data migration?** No. Pure additions — no columns were removed, so no
migration is possible.

---

## Summary Table

| Transition | Columns Added | Columns Removed | Data Migration? | New File Types? |
|------------|--------------|-----------------|----------------|-----------------|
| 2.0 prd→prd2 | 0 | 18 (SmallBusinessSubset*) | No | — |
| 2.0 os→os-update | 1 (Changes*) | 0 | No | — |
| **2.0 → 2.1** | 3 | 2 | No | Signature-Entities |
| **2.1 → 2.2** | 2 | 12 | No | — |
| **2.2 → 2.3** | 0 | 0 | No | — |
| **2.3 → 2.4** | 0 | 0 | No | — |
| **2.4 → 2.5** | 4 | 0 | No | Endorsed-Entities |

---

## Implications for Git History Build Scripts

1. **No data migration step needed.** Columns are independently added and removed
   across all transitions. The 6-step commit process can safely treat additions
   and removals as separate operations without a "migrate data between columns"
   step.

2. **Schema changes only at three transitions.** Actual column structure changes
   only occur at 2.0→2.1, 2.1→2.2, and 2.4→2.5. The 2.2→2.3 and 2.3→2.4
   transitions only change filenames (version numbers) and data content.

3. **Signature-Entities is schema-stable.** The Signature-Entities file never
   changes its column structure, simplifying version transitions.

4. **Within-version schema changes in 2.0.** Unlike later versions, UBL 2.0 has
   column changes within the version (prd→prd2 removes 18 columns, os→os-update
   adds 1).

---

*Last updated: 2026-02-13*
