# UBL 2.4 Intermediate Revision Validity Analysis

## Summary

Between UBL 2.3 OS (the starting point) and UBL 2.4 CSD01, only a narrow set of 
(library_rev, documents_rev) pairs produce valid .gc files. Out of 673 library 
revisions × 157 document revisions = 105,661 possible pairs, only **~406 pairs** 
are valid (~0.4%).

## Valid Pair Windows

| Library Revisions | Document Revisions | Count | Description |
|---|---|---|---|
| **1–102** | **1** | 102 | Library evolving (new ABIEs added), docs at 2.3 baseline |
| **593–599** | **1** | 7 | Both DLR+RLR ABIEs present, docs at 2.3 baseline |
| **593–599** | **155–157** | 21 | Both DLR+RLR ABIEs present, docs with fixed refs |
| **605–673** | **1** | 69 | CSD01+ library (PTQ-qualified refs), docs at 2.3 baseline |
| **605–673** | **155–157** | 207 | CSD01+ library, docs with fixed refs |
| | | **~406** | **Total valid pairs** |

## Why Most Pairs Are Invalid

### Issue 1: Library Unresolved ASBIE References (lib 103–592, 600–604)

Starting at lib rev-103, someone changed ASBIE references from the PTQ-qualified form
(`AssociatedObjectClass="Line Reference"` with `PropertyTermQualifier="Despatch"`)
to the compound form (`AssociatedObjectClass="Despatch Line Reference"`). But no
corresponding ABIEs named "Despatch Line Reference" or "Receipt Line Reference" 
were created, causing unresolved references.

**Timeline:**
- rev-103: "Despatch Line Reference" ASBIE ref appears → **1 unresolved**
- rev-107: "Receipt Line Reference" ASBIE ref appears → **2 unresolved**
- rev-115: "Gross Volume Measure" (mistyped ASBIE) appears → **3 unresolved**
- rev-140: "Gross Weight Measure" (mistyped ASBIE) appears → **4 unresolved**
- rev-160: GVM/GWM fixed → back to **2 unresolved** (DLR + RLR)
- rev-571: "Despatch Line Reference" ABIE added → **1 unresolved** (RLR only)
- rev-593: "Receipt Line Reference" ABIE added → **0 unresolved** ✓
- rev-600: RLR ABIE removed → **1 unresolved** again
- rev-601: DLR ABIE also removed → **2 unresolved**
- rev-604: DLR ASBIE ref removed → **1 unresolved** (RLR)
- rev-605: RLR ASBIE ref changed to PTQ form → **0 unresolved** ✓ (final fix)

### Issue 2: Document Sheet Naming (doc 2, 95–96, 97–129)

- doc rev-2: Sheet "Copy of BusinessInformation" → model "UBL-Copy of BusinessInformation-2.4"
- doc rev-95–96: Sheet "Copy of Invoice" → model "UBL-Copy of Invoice-2.4"
- doc rev-97–129: Sheet "Purchase Receipt" (with space) → model "UBL-Purchase Receipt-2.4"

These produce model names with spaces, which is an NDR violation.

### Issue 3: "Notice Subtype" Reference Mismatch (doc 2–154)

The library has an ABIE called "Notice Sub Type" (three words, from lib rev-19+).
Documents used different spellings until rev-155:

- doc 2–153: `AssociatedObjectClass="Notice Subtype"` (no space in "Subtype") → UNRESOLVED
- doc 154: `AssociatedObjectClass="NoticeSubType"` (camelCase) → UNRESOLVED
- doc 155+: `AssociatedObjectClass="Notice Sub Type"` → RESOLVED ✓

### Issue 4: Cross-Sheet Reference Dependencies (doc ≥2 + early lib)

Documents added after rev-1 reference new library ABIEs:
- "Operation Type" (needs lib ≥14)
- "Party Group" (needs lib ≥10)
- "Cash Register" (needs lib ≥281)
- "Purchase Reference" (needs lib ≥250)
- "Purchase Receipt Line" (needs lib ≥400)
- "Notice Sub Type" (needs lib ≥19)

However, this dependency is always dominated by Issue 1 (library unresolved refs)
and Issue 3 (Notice Subtype mismatch), which are the binding constraints.

## Visual Timeline

```
Library revisions (673 total):
  |----- VALID -----|----- INVALID (DLR/RLR/GVM/GWM) ------|--V--|--I--|---- VALID ----|
  1              102 103                                  592 593 599 600 604 605     673
                    ^                                         ^       ^     ^
                    DLR ref                              Both ABIEs  RLR   PTQ fix
                    introduced                           added       removed

Document revisions (157 for CSD01):
  |V|-------- INVALID (Notice Subtype + sheet names) --------|V-V-V|
  1 2                                                     154 155 157
    ^                                                         ^
    Notice Subtype                                       Notice Sub Type
    introduced                                           (matches library)

Valid pair regions:
  lib 1-102    × doc 1       = 102 pairs (library-only evolution)
  lib 593-599  × doc 1       =   7 pairs (brief DLR+RLR window)
  lib 593-599  × doc 155-157 =  21 pairs (DLR+RLR + fixed docs)
  lib 605-673  × doc 1       =  69 pairs (post-PTQ-fix)
  lib 605-673  × doc 155-157 = 207 pairs (CSD01+ states)
  ─────────────────────────── ≈ 406 valid pairs total
```

## Confirmed Via XSLT Conversion

All boundaries verified by running actual Crane-ods2obdgc XSLT conversions and
checking the resulting .gc files for:
1. Unresolved ASBIE references (AssociatedObjectClass not matching any ABIE ObjectClass)
2. Model names with spaces (NDR violation)

### Key conversion results:
| Pair | Rows | Verdict |
|---|---|---|
| lib-1 + doc-1 (baseline) | 5,286 | VALID |
| lib-102 + doc-1 | 5,300 | VALID (last valid before DLR) |
| lib-103 + doc-1 | — | INVALID (DLR unresolved) |
| lib-593 + doc-155 | 5,433 | VALID (DLR+RLR ABIEs present) |
| lib-599 + doc-155 | 5,434 | VALID |
| lib-600 + doc-1 | — | INVALID (RLR removed) |
| lib-605 + doc-155 | 5,429 | VALID (=CSD01 state) |
| lib-605 + doc-157 | 5,429 | VALID (CSD01 exact) |
| lib-605 + doc-154 | — | INVALID (NoticeSubType) |
| lib-605 + doc-130 | — | INVALID (Notice Subtype) |
| lib-100 + doc-97 | — | INVALID (Purchase Receipt space) |

## Interpretation

The fact that only ~0.4% of revision pairs produce valid .gc files reflects the
reality of concurrent editing in Google Sheets: the library and documents evolved
semi-independently, and mismatches (typos, naming inconsistencies, temporary
structural experiments) persisted for long stretches. The editors eventually
fixed all issues by CSD01 time (lib-605, doc-157), but the path there was
remarkably narrow.
