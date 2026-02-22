# Valid (lib_rev, doc_rev) Pairs: 2.4 OS → csd01

## Starting State Verified

Rev 1 of both Google Sheets ODS files is identical to the published
UBL 2.4 OS content. Every worksheet has exactly +1 row (the header row,
which is present in the ODS but not in the GenericCode .gc output).

| Metric | ODS Rev 1 | 2.4 OS .gc | Match? |
|--------|-----------|------------|--------|
| Library rows | 3007 | 3006 | ✓ (+1 header) |
| Document rows | 2530 | 2437 | ✓ (+93 headers) |
| Library columns | 22 | 20 (+ModelName, -Qualifiers, -Subset) | ✓ mapped |
| Document sheets | 93 | 93 model names | ✓ exact |

## Column Rollout Timeline

The 4 new columns introduced in UBL 2.5 were added systematically:

**Library ODS** (all in the single CommonLibrary sheet):
- lib rev 3–4: "Endorsed Cardinality" added (initially "Deprecated cardinality")
- lib rev 8–10: Renamed through "Future cardinality" → "Endorsed cardinality"
- lib rev 13–14: "Deprecated Definition" added
- lib rev 21–31: "Deprecation Rationale" added (with typos, fixed by rev 31)
- lib rev 41–42: "Endorsed Cardinality Rationale" added
- lib rev 44–45: "Last Changed" added
- lib rev 71–75: Column name capitalization standardized

**Documents ODS** (93 worksheets, rolled out alphabetically):
- doc rev 35: ApplicationResponse gets all 4 new columns (first sheet)
- doc rev 35–413: 1 sheet per 4 consecutive revisions, alphabetical order
- doc rev 413: All 93 original sheets have all 4 new columns (26 total)

Note: The .gc generation tool normalizes columns — sheets missing columns
get blank values. So partial rollout states CAN produce valid .gc files.

## ABIE Cross-Reference Constraints

For a (lib_rev, doc_rev) pair to produce a valid .gc that passes NDR:
- Every ASBIE in documents must reference an ABIE that exists in the library
- Library-internal ASBIEs must also reference existing ABIEs

### New ABIEs Added (rev 1 → csd01)

| ABIE | Lib Rev Added | Doc Rev First Used | Binding? |
|------|---------------|-------------------|----------|
| Insurance | 232 | never | no |
| Insurance Policy | 281 (replaces Insurance) | never | no |
| Circularity Profile | 393 | never | no |
| End Of Life Treatment | 492 | never | no |
| Resource Consumption | 707 | never | no |
| Score | 742 | never | no |
| Waste Generated | 766 | never | no |
| Security Listing | 810 (replaces Security Listed) | never | no |
| **Buyer Reference** | **995** | **579** | **YES** |
| Interest Rate | 1025 | never | no |
| Billing Reference Line | 1072 (re-added*) | never | internal |
| **Annotation** | **1269** | **781** | **YES** |
| **Work Report Line** | **1413** | **1186** | subsumed |
| **Work Quantity Total** | **1512** | **1173** | **YES** |

*BRL was removed at lib 995 and re-added at lib 1072. Between those
revisions, the library-internal ASBIE "Billing Reference. Billing
Reference Line" is dangling → likely fails NDR.

### Staircase Constraint

```
doc   1 – 578  →  lib ≥    1    (no new ABIE deps from documents)
doc 579 – 780  →  lib ≥ 1072    (Buyer Reference + BRL restored)
doc 781 –1172  →  lib ≥ 1269    (Annotation)
doc 1173–1294  →  lib ≥ 1512    (Work Quantity Total)
```

## Garbage Worksheet Windows (always invalid)

- doc rev 1541–1611: "Sheet2" worksheet present
- doc rev 1805: "Copy of ApplicationResponse" worksheet present

These are between csd01 (doc 1294) and csd02 (doc 2190), so they
don't affect the rev 1 → csd01 range.

## Milestone Valid Pairs

### Band 1: doc 1–578, lib ≥ 1

No document→library ABIE constraints. Library evolves freely.

| # | lib | doc | Description |
|---|-----|-----|-------------|
| 1 | 1 | 1 | 2.4 OS baseline |
| 2 | 45 | 1 | Library has all new columns |
| 3 | 75 | 1 | Library column names capitalized |
| 4 | 75 | 34 | Last doc before column rollout |
| 5 | 75 | 413 | Document column rollout complete |
| 6 | 232 | 413 | +Insurance ABIE |
| 7 | 281 | 413 | Insurance → Insurance Policy |
| 8 | 393 | 413 | +Circularity Profile |
| 9 | 492 | 413 | +End Of Life Treatment |
| 10 | 707 | 413 | +Resource Consumption |
| 11 | 742 | 413 | +Score |
| 12 | 766 | 413 | +Waste Generated |
| 13 | 810 | 413 | Security Listed → Security Listing |
| 14 | 810 | 578 | Last doc before Buyer Reference |

### Band 2: doc 579–780, lib ≥ 1072

| # | lib | doc | Description |
|---|-----|-----|-------------|
| 15 | 1072 | 579 | Buyer Reference in docs, BRL restored |
| 16 | 1072 | 780 | Last doc before Annotation |

### Band 3: doc 781–1172, lib ≥ 1269

| # | lib | doc | Description |
|---|-----|-----|-------------|
| 17 | 1269 | 781 | Annotation used in documents |
| 18 | 1269 | 1172 | Last doc before Work Qty Total |

### Band 4: doc 1173–1294, lib ≥ 1512

| # | lib | doc | Description |
|---|-----|-----|-------------|
| 19 | 1512 | 1173 | Work Quantity Total in documents |
| 20 | 1533 | 1294 | **csd01 pinpoint** |

## Validity Visualization

```
doc_rev
  ▲
  │
1294│                                    ░░░░░B (csd01)
    │                                ████░░░░░░
1173│- - - - - - - - - - - - - -│████░░░░░░░░░
    │                        ████│░░░░░░░░░░░░░
 781│- - - - - - - - - -│████░░░│░░░░░░░░░░░░░
    │                ████│░░░░░░░│░░░░░░░░░░░░░
 579│- - - - - - │████░░░│░░░░░░░│░░░░░░░░░░░░░
    │ ░░░░░░░░░░░│░░░░░░░│░░░░░░░│░░░░░░░░░░░░░
    │ ░░░░░░░░░░░│░░░░░░░│░░░░░░░│░░░░░░░░░░░░░
   1│A░░░░░░░░░░░│░░░░░░░│░░░░░░░│░░░░░░░░░░░░░
    └─────────────────────────────────────────→ lib_rev
    1         995 1072  1269  1512  1533

    ░ = valid pair    █ = invalid (ABIE missing)
    A = 2.4 OS        B = csd01
```

## Key Findings

1. **Starting state = 2.4 OS**: Both ODS files at rev 1 are identical
   to the published UBL 2.4 OS release.

2. **20 meaningful milestone pairs** between 2.4 OS and csd01.

3. **The constraint tightens over time**: Band 1 allows any lib revision;
   by Band 4, lib must be ≥ 1512 (out of 1533 total at csd01).

4. **Library leads, documents follow**: New ABIEs always appear in the
   library first, then documents reference them later. The gap varies
   from 77 revisions (BRL→Buyer Reference) to 339 revisions
   (Work Quantity Total).

5. **BRL gap is subtle**: The Billing Reference Line removal/re-addition
   cycle (lib 995–1072) creates a library-internal inconsistency that
   shifts the Band 2 minimum from lib 995 to lib 1072 for strict NDR.
