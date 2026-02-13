# UBL GenericCode File Format

## Overview

**GenericCode** (.gc) is OASIS's human-readable semantic model format for UBL. It represents the business information entities, their properties, and relationships in a structured text format that can be version-controlled and easily compared across releases.

GenericCode files serve as the **authoritative source** for UBL's semantic model, from which XML schemas (.xsd), documentation, and other artifacts are generated.

---

## What's in a GenericCode File?

GenericCode files define three types of components:

1. **ABIEs** (Aggregate Business Information Entities) - Complex types like "Address", "Party", "Order Line"
2. **BBIEs** (Basic Business Information Entities) - Simple properties like "Line", "Description", "Amount"
3. **ASBIEs** (Association Business Information Entities) - References to other ABIEs like "Buyer Party", "Delivery Address"

### Example Entry

```
Address Line. Line. Text (BBIE)
├─ ObjectClass = Address Line
├─ PropertyTerm = Line
├─ RepresentationTerm = Text
├─ DataType = Text. Type
├─ Cardinality = 0..1
└─ Definition = One line of an address.
```

This describes a **Basic Business Information Entity** (BBIE) that:
- Belongs to the "Address Line" object class
- Has the property name "Line"
- Uses the representation term "Text" (indicates it's textual data)
- References the qualified data type **"Text. Type"** (defined in XSD)
- Is optional (can appear 0 or 1 times)
- Has a human-readable definition

---

## GenericCode Column Structure Evolution

The GenericCode format has evolved across UBL versions:

### UBL 2.0 - 2.1 (Filename Change Only)

**UBL 2.0:**
```
Columns: ObjectClass, PropertyTerm, RepresentationTerm, DataType, Cardinality, Definition
Filename: UBL-Entities-2.0.gc
```

**UBL 2.1:**
```
Columns: ObjectClass, PropertyTerm, RepresentationTerm, DataType, Cardinality, Definition
Filename: UBL-Entities-2.1.gc
```

🔄 **What Changed:** Only the filename and version number in content.

### UBL 2.1 → 2.2 (Major Restructure)

**UBL 2.2+:**
```
Columns: DEN, ObjectClass, PropertyTerm, RepresentationTerm, DataType,
         AssociatedObjectClass, Cardinality, Definition, AlternativeBusinessTerms
```

🔄 **What Changed:**
- Added **DEN** (Dictionary Entry Name) - canonical identifier
- Added **AlternativeBusinessTerms** - common business names
- Reordered columns

### UBL 2.4 → 2.5 (Add Cardinality Supplement)

**UBL 2.5:**
```
Columns: DEN, ObjectClass, PropertyTerm, RepresentationTerm, DataType,
         AssociatedObjectClass, Cardinality, CardinalitySupplement, Definition,
         AlternativeBusinessTerms
```

🔄 **What Changed:**
- Added **CardinalitySupplement** - additional cardinality constraints/notes

---

## The Relationship Between .gc and .xsd Files

### Data Type References vs Definitions

GenericCode files contain **type references**, but the actual **type definitions** live in XSD schemas:

```
UBL 2.0 (2006):
├─ UBL-qDT-2.0.ods (TYPE DEFINITIONS) ← 7 spreadsheet files
├─ UBL-Entities-2.0.gc (TYPE REFERENCES) ← semantic model
└─ UBL-*.xsd (XML SCHEMAS) ← generated from above

UBL 2.1+ (2013→):
├─ (qDT definitions in XSD only) ← no separate GenericCode
├─ UBL-Entities-2.x.gc (TYPE REFERENCES) ← semantic model
└─ UBL-*.xsd (XML SCHEMAS) ← includes qDT definitions
```

### Why This Matters

**GenericCode tells you:**
- What business entities exist (Address, Party, Invoice)
- What properties they have (Line, Description, Amount)
- What data types they **reference** ("Text. Type", "Identifier. Type")

**XSD schemas define:**
- What "Text. Type" actually means
- What XML schema type it maps to (`xsd:string`)
- What supplementary components it has (language code, etc.)
- Validation rules and constraints

**To fully understand the UBL data model, you need BOTH.**

---

## CCTS Data Type Architecture

### The Three-Layer Type Hierarchy

UBL's data typing follows the UN/CEFACT Core Components Technical Specification (CCTS).
The type system has three layers, none of which are represented in the GenericCode files:

```
Layer 1: CCTS Core Component Types (CCTs)
         Defined in: CCTS_CCT_SchemaModule-{version}.xsd
         Source: UN/CEFACT (external standard)
         Examples: Amount. Type, Code. Type, Identifier. Type

Layer 2: UBL Unqualified Data Types (UDTs)
         Defined in: UBL-UnqualifiedDataTypes-{version}.xsd
         Source: UBL TC (extends CCTs with Date, Time, Name, etc.)
         Examples: Date. Type, Time. Type, Name. Type

Layer 3: UBL Qualified Data Types (QDTs)
         Defined in: UBL-QualifiedDataTypes-{version}.xsd
         Source: UBL TC (specializes CCTs for specific business contexts)
         Examples: Currency_ Code. Type, Channel_ Code. Type
```

### Data Types Referenced in UBL 2.0

The UBL 2.0 prd GenericCode file references 20 distinct data types in its BBIE rows.
None of these types are defined within the GC file itself.

**10 CCTS Core Component Types** (from `CCTS_CCT_SchemaModule-2.0.xsd`):

| CCT | UN/CEFACT ID | Primitive Type |
|-----|--------------|----------------|
| Amount. Type | UNDT000001 | decimal |
| Binary Object. Type | UNDT000002 | base64Binary |
| Code. Type | UNDT000007 | normalizedString |
| Date Time. Type | UNDT000008 | string |
| Identifier. Type | UNDT000011 | normalizedString |
| Indicator. Type | UNDT000012 | string |
| Measure. Type | UNDT000013 | decimal |
| Numeric. Type | UNDT000014 | decimal |
| Quantity. Type | UNDT000018 | decimal |
| Text. Type | UNDT000019 | string |

Each CCT also defines **Supplementary Components** (SCs) — attributes like `currencyID`
on Amount, `schemeID` on Identifier, `languageID` on Text, etc.

**4 UBL Unqualified Data Types** (extensions of CCTs):

| UDT | Extends |
|-----|---------|
| Date. Type | Date Time. Type (restricted to date) |
| Time. Type | Date Time. Type (restricted to time) |
| Name. Type | Text. Type (specialized for names) |
| Rate. Type | Numeric. Type (specialized for rates) |

**6 UBL Qualified Data Types** (specializations for business contexts):

| QDT | Qualifies |
|-----|-----------|
| Channel_ Code. Type | Code. Type |
| Currency_ Code. Type | Code. Type |
| Document Status_ Code. Type | Code. Type |
| Latitude Direction_ Code. Type | Code. Type |
| Longitude Direction_ Code. Type | Code. Type |
| Percent. Type | Numeric. Type |

### The Data Type Gap in GenericCode Files

In CCTS terms, a complete semantic model includes:

```
DT  (Data Type definitions)         ← NOT in GC file
 └── SC (Supplementary Components)  ← NOT in GC file
ABIE (Aggregate entities)           ← in GC file ✅
 ├── BBIE → references DT           ← BBIE in GC, DT external
 └── ASBIE → references ABIE        ← both in GC ✅
```

Every BBIE row contains a `DataType` column with a value like `"Identifier. Type"`,
but this is a **dangling reference** — it points to a type defined outside the file,
in the XSD layer. This is by design in every OASIS-published release.

For the purposes of building the git history (PoC and production), we treat data type
references as **external** — matching how OASIS publishes the files. Internal consistency
validation covers:
- Every ASBIE's `AssociatedObjectClass` must reference an ABIE defined in the same file
- Every BBIE/ASBIE must belong to an `ObjectClass` that is defined as an ABIE in the file
- Data type references are accepted as-is (validated against a known list, not against
  in-file definitions)

### Future Possibility: Synthesized Data Types GC File

A more complete CCTS representation could include a companion GenericCode file that
defines the data types as rows. This file does not exist in any OASIS release but
could be synthesized from the XSD schemas.

**Proposed format:** A GenericCode file with rows for each data type, containing:

| Column | Purpose | Example |
|--------|---------|---------|
| ComponentType | "DT" (data type) | DT |
| DictionaryEntryName | CCTS canonical name | Amount. Type |
| UniqueID | UN/CEFACT identifier | UNDT000001 |
| CategoryCode | CCT, UDT, or QDT | CCT |
| PrimitiveType | XSD base type | decimal |
| Definition | Human-readable description | A number of monetary units... |
| RepresentationTermName | CCTS representation term | Amount |
| Qualifier | For QDTs, the qualifying term | Currency_ (for Currency_ Code) |

**Supplementary Components** would be additional rows with ComponentType "SC":

| Column | Purpose | Example |
|--------|---------|---------|
| ComponentType | "SC" (supplementary component) | SC |
| DictionaryEntryName | SC canonical name | Amount Currency. Identifier |
| ParentType | Which DT this belongs to | Amount. Type |
| PrimitiveType | XSD attribute type | string |
| Definition | What this SC represents | The currency of the amount |

**Benefits of this approach:**
- Self-contained CCTS model entirely in GenericCode format
- Enables validation of BBIE DataType references within the GC ecosystem
- Tracks data type evolution across versions (CCTs are stable, QDTs change)
- Provides a foundation for generating XSD from GC alone

**Why this is deferred:**
- No precedent in OASIS releases — would be a novel artifact
- The XSD files already serve this purpose and are authoritative
- The PoC focuses on tracking entity evolution, not type system completeness
- Could be added as a separate enhancement later

---

## The Three GenericCode File Types

### 1. UBL-Entities-{version}.gc (All versions)

The main semantic model containing:
- Document types (Invoice, Order, Catalogue)
- Common aggregates (Address, Party, Line Item)
- Common basic components
- ~1,800 entries across all entity types

**Example:** `UBL-Entities-2.5.gc`

### 2. UBL-Signature-Entities-{version}.gc (2.1+)

Digital signature components for XML signatures:
- Signature properties
- Signature information
- Signing party details
- ~50 specialized entries

**Example:** `UBL-Signature-Entities-2.5.gc`

**Note:** Not all releases include this file. It's updated less frequently than the main Entities file.

### 3. UBL-Endorsed-Entities-{version}.gc (NEW in 2.5!)

A **subset** of the main Entities file containing only the components endorsed by the UBL TC for widespread use:
- Core document types (Invoice, Order, Catalogue, etc.)
- Most common aggregates
- Excludes experimental or domain-specific entities
- ~1,200 entries (subset of the 1,800 in full Entities)

**Example:** `UBL-Endorsed-Entities-2.5.gc`

**Purpose:** Helps implementers focus on the stable, widely-supported core of UBL.

---

## XSD Files We Need

To have a **complete** historical archive, we should include the XSD schemas that define the qualified data types referenced in the GenericCode files.

### For UBL 2.0 (Generated from .ods)

Already have:
- ✅ `history/generated/prd-UBL-2.0/mod/UBL-Entities-2.0.gc`

Should add:
- `common/UBL-QualifiedDataTypes-2.0.xsd`
- `common/UBL-UnqualifiedDataTypes-2.0.xsd`
- `common/CCTS_CCT_SchemaModule-2.0.xsd`

### For UBL 2.1 - 2.5

Already have:
- ✅ All Entities .gc files (35 releases)
- ✅ All Signature-Entities .gc files (where available)

Should add for each version:
- `common/UBL-QualifiedDataTypes-{version}.xsd`
- `common/UBL-UnqualifiedDataTypes-{version}.xsd`
- `common/CCTS_CCT_SchemaModule-{version}.xsd`

### Recommended Directory Structure

```
history/
├─ xsd/                                    ← NEW: XSD schema archive
│  ├─ 2.0/
│  │  ├─ common/
│  │  │  ├─ UBL-QualifiedDataTypes-2.0.xsd
│  │  │  ├─ UBL-UnqualifiedDataTypes-2.0.xsd
│  │  │  └─ CCTS_CCT_SchemaModule-2.0.xsd
│  │  └─ ...
│  ├─ 2.1/
│  │  └─ common/
│  │     ├─ UBL-QualifiedDataTypes-2.1.xsd
│  │     ├─ UBL-UnqualifiedDataTypes-2.1.xsd
│  │     └─ CCTS_CCT_SchemaModule-2.1.xsd
│  ├─ 2.2/
│  ├─ 2.3/
│  ├─ 2.4/
│  └─ 2.5/
│
├─ generated/                              ← UBL 2.0 .gc files
├─ prd1-UBL-2.1/                          ← UBL 2.1-2.5 .gc files
└─ ...
```

---

## Key Column Definitions

### Common Across All Versions

| Column | Description | Example |
|--------|-------------|---------|
| **ObjectClass** | The business object this property belongs to | `Address Line`, `Invoice` |
| **PropertyTerm** | The property name | `Line`, `Issue Date`, `Description` |
| **RepresentationTerm** | How the value is represented | `Text`, `Date`, `Code`, `Identifier` |
| **DataType** | Reference to qualified data type (for BBIEs) | `Text. Type`, `Identifier. Type` |
| **AssociatedObjectClass** | Target object class (for ASBIEs) | `Party`, `Address` |
| **Cardinality** | How many times it can occur | `0..1`, `1..1`, `0..n` |
| **Definition** | Human-readable description | "One line of an address." |

### Added in UBL 2.2+

| Column | Description | Example |
|--------|-------------|---------|
| **DEN** | Dictionary Entry Name (canonical ID) | `Address Line. Line. Text` |
| **AlternativeBusinessTerms** | Common business names | "Address Line 1", "Street Address" |

### Added in UBL 2.5

| Column | Description | Example |
|--------|-------------|---------|
| **CardinalitySupplement** | Additional cardinality notes | "Required when X", "Conditional on Y" |

---

## File Locations in This Repository

### GenericCode Files (65 total)

```bash
# UBL 2.0 (8 files)
history/generated/prd-UBL-2.0/mod/UBL-Entities-2.0.gc
history/generated/prd2-UBL-2.0/mod/UBL-Entities-2.0.gc
...
history/generated/errata-UBL-2.0/mod/UBL-Entities-2.0.gc

# UBL 2.1 (16 files: 8 Entities + 8 Signature)
history/prd1-UBL-2.1/mod/UBL-Entities-2.1.gc
history/prd1-UBL-2.1/mod/UBL-Signature-Entities-2.1.gc
...

# UBL 2.5 (7 files: 2 Entities + 2 Signature + 2 Endorsed + 1 missing)
history/csd01-UBL-2.5/mod/UBL-Entities-2.5.gc
history/csd01-UBL-2.5/mod/UBL-Signature-Entities-2.5.gc
history/csd01-UBL-2.5/mod/UBL-Endorsed-Entities-2.5.gc
```

### XSD Files (to be added)

```bash
# Proposed structure
history/xsd/2.0/common/*.xsd
history/xsd/2.1/common/*.xsd
history/xsd/2.2/common/*.xsd
history/xsd/2.3/common/*.xsd
history/xsd/2.4/common/*.xsd
history/xsd/2.5/common/*.xsd
```

---

## How GenericCode is Used

1. **Version Control** - Text-based format shows exact changes between releases
2. **Documentation** - Generates reference documentation for implementers
3. **Schema Generation** - Produces XML schemas (.xsd) for validation
4. **Code Generation** - Creates programming language bindings (Java, C#, etc.)
5. **Semantic Analysis** - Enables queries like "What properties does Invoice have?"

---

## GenericCode vs XSD: Two Different Views of UBL

The GenericCode semantic model and the XSD schemas represent the **same UBL standard** but from fundamentally different perspectives. Understanding this distinction is key to working with either format.

### XSD View: Structural Reuse Through Composition

In the XSD world, UBL is built through **modular assembly**. Components are defined once and reused everywhere by reference:

```
CommonBasicComponents (cbc):
  cbc:IssueDateType         ← defined ONCE

CommonAggregateComponents (cac):
  cac:PartyType             ← defined ONCE, composes cbc elements
  cac:AddressType           ← defined ONCE, composes cbc elements

Document Schemas:
  Invoice                   ← references cbc:IssueDate, cac:Party, etc.
  CreditNote                ← references cbc:IssueDate, cac:Party, etc.
  Order                     ← references cbc:IssueDate, cac:Party, etc.
```

A single element like `cbc:IssueDate` is shared across dozens of document types. Common Aggregate Components (CACs) compose Common Basic Components (CBCs), and document types compose CACs — it's a layered system of reuse. This makes schemas compact and DRY.

### GenericCode View: Fully Expanded Semantic Catalog

In the GenericCode world, there is **no reuse**. Every property is spelled out in full for every context it appears in:

```
Invoice. Issue Date. Date              ← BBIE belonging to Invoice
Credit Note. Issue Date. Date          ← separate BBIE belonging to Credit Note
Order. Issue Date. Date                ← separate BBIE belonging to Order
```

These are three distinct rows. They share the same `PropertyTerm` ("Issue Date") and `DataType` ("Date. Type"), but each has a unique `DictionaryEntryName` because it belongs to a different `ObjectClass`. The file is a **flat, denormalized catalog** — every combination of entity + property is an independent entry.

### Why the Difference Matters

| Aspect | GenericCode (Semantic) | XSD (Structural) |
|--------|----------------------|-------------------|
| **Purpose** | What things *mean* | How things are *structured* |
| **Reuse model** | None — every entry is explicit | Composition — define once, reference many |
| **"Invoice. Issue Date"** | A standalone row with its own definition | A reference to shared `cbc:IssueDate` element |
| **Granularity** | One row per property-in-context | One definition per reusable component |
| **Row count** | ~1,800 entries (all combinations) | ~60 CBCs + ~100 CACs + ~80 document types |
| **Diff-friendly** | Yes — flat rows, easy to compare | Harder — changes in a shared type affect many documents |

### The Relationship

GenericCode is the **source of truth** for semantics. The XSD schemas are **generated from** the GenericCode model. The generation process takes the flat, denormalized GC catalog and produces the modular, reuse-oriented XSD structure:

```
GenericCode (flat, semantic)
  │
  │  generation / compilation
  ▼
XSD Schemas (modular, structural)
  ├── CommonBasicComponents-2.x.xsd      ← shared basic elements
  ├── CommonAggregateComponents-2.x.xsd  ← shared aggregate types
  ├── UBL-Invoice-2.x.xsd               ← document-level schemas
  ├── UBL-Order-2.x.xsd
  └── ...
```

In the GC file, "Invoice. Issue Date. Date" and "Order. Issue Date. Date" are independent rows. In the generated XSD, both document schemas reference the same `cbc:IssueDateType` — the generator recognizes that they share the same property term and data type, and factors out the common definition.

### Practical Implication for This Repository

This repository tracks the **GenericCode files** — the semantic layer. When you see what looks like duplication (the same property appearing under many ABIEs), that's by design. Each row captures the meaning of that property *in that specific business context*. The structural deduplication happens downstream, in the XSD generation step.

---

## Related Documentation

- [README.md](../README.md) - Complete project overview
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture and design decisions
- [docs/historical-releases.md](historical-releases.md) - All 35 UBL releases with download URLs
- [history/README.md](../history/README.md) - History directory organization

---

## External Resources

- [OASIS UBL TC](https://www.oasis-open.org/committees/ubl/) - Official UBL Technical Committee
- [UBL 2.5 Specification](https://docs.oasis-open.org/ubl/UBL-2.5/) - Latest version documentation
- [UN/CEFACT CCTS](https://unece.org/trade/uncefact/introducing-unCefact) - Core Component Technical Specification (data type foundation)

---

**Last Updated:** 2026-02-12
**Format Version:** Covers UBL 2.0 (2006) through UBL 2.5 (2025)
