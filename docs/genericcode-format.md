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
