# ubl-gc

The UBL GenericCode representation of the UBL Semantic Model

## Overview

This repository maintains a complete historical archive of UBL (Universal Business Language) GenericCode semantic model files from UBL 2.0 through UBL 2.5, including all intermediate release stages. This enables complete git-based version control and full blame tracking of semantic model evolution across 20 years of UBL development (2006-2026).

## Quick Navigation

- 📖 **[history/README.md](history/README.md)** - History directory overview and semantic model evolution
- 🛠️ **[history/tools/README.md](history/tools/README.md)** - Tool documentation, provenance, and verification
- 📋 **[docs/historical-releases.md](docs/historical-releases.md)** - Complete list of all UBL versions with URLs
- 🏗️ **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design decisions
- ⚙️ **[docs/workflows.md](docs/workflows.md)** - GitHub Actions workflows and build scripts documentation

## Directory Structure

```
/home/user/ubl-gc/
├── README.md                          (this file - comprehensive documentation)
├── ARCHITECTURE.md                    (system architecture & design)
├── docs/
│   └── historical-releases.md         (complete list of all UBL versions with OASIS URLs)
└── history/
    ├── README.md                      (history directory overview & evolution)
    ├── tools/
    │   ├── README.md                  (tool documentation, provenance, verification)
    │   ├── CONVERSION_GUIDE.md        (step-by-step conversion instructions)
    │   └── TOOL_VERIFICATION.md       (known issues, performance, maintenance)
    │
    ├── os-UBL-2.0/mod/
    │   └── UBL-*.ods files            (30 ODS source files from OASIS os-UBL-2.0)
    │
    ├── prd1-UBL-2.1/mod/              (GenericCode files from OASIS)
    │   ├── UBL-Entities-2.1.gc
    │   └── UBL-Signature-Entities-2.1.gc
    │
    ├── ... (other UBL 2.1-2.5 releases from OASIS)
    │
    └── generated/                     (Generated/Synthesized files)
        └── os-UBL-2.0/mod/
            └── UBL-Entities-2.0.gc    (synthesized from 30 ODS files)
```

**Key Structure Notes:**
- `history/` contains files directly from OASIS (ODS and GenericCode)
- `history/generated/` contains files we created/synthesized (currently just UBL 2.0 GenericCode)
- Version directories follow OASIS naming convention: `{release-stage}-UBL-{version}/mod/`

## UBL 2.0 GenericCode Synthesis

### Overview

UBL 2.0 (2006) was originally released as ODS (OpenDocument Spreadsheet) files, not GenericCode format. We have synthesized a GenericCode representation from the official OASIS UBL 2.0 source files to enable complete git history tracking from UBL 2.0 through 2.5.

**Generated File**: `/history/generated/os-UBL-2.0/mod/UBL-Entities-2.0.gc`
- **Source Release**: os-UBL-2.0 (Official Standard, 2006-12-12)
- **Status**: Final, approved OASIS standard
- **File Size**: 3.3 MB
- **Entity Rows**: 2,181
- **Source Files**: 30 ODS files consolidated (2 core + 28 document types)
  - Located in: `/history/os-UBL-2.0/mod/` (all downloaded directly from OASIS)

### Source Data (All 33 ODS Files)

All files obtained from the official OASIS UBL 2.0 release (os-UBL-2.0):
https://docs.oasis-open.org/ubl/os-UBL-2.0/

**Core Files (2):**
- `UBL-CommonLibrary-2.0.ods` - Core component entities, common types
  - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/common/UBL-CommonLibrary-2.0.ods
- `UBL-qDT-2.0.ods` - Qualified datatype definitions
  - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/common/UBL-qDT-2.0.ods

**Document Type Files (28):**
1. ApplicationResponse - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-ApplicationResponse-2.0.ods
2. AttachedDocument - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-AttachedDocument-2.0.ods
3. BillOfLading - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-BillOfLading-2.0.ods
4. Catalogue - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-Catalogue-2.0.ods
5. CatalogueDeletion - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-CatalogueDeletion-2.0.ods
6. CatalogueItemSpecificationUpdate - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-CatalogueItemSpecificationUpdate-2.0.ods
7. CataloguePricingUpdate - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-CataloguePricingUpdate-2.0.ods
8. CatalogueRequest - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-CatalogueRequest-2.0.ods
9. CertificateOfOrigin - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-CertificateOfOrigin-2.0.ods
10. CreditNote - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-CreditNote-2.0.ods
11. DebitNote - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-DebitNote-2.0.ods
12. DespatchAdvice - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-DespatchAdvice-2.0.ods
13. ForwardingInstructions - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-ForwardingInstructions-2.0.ods
14. FreightInvoice - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-FreightInvoice-2.0.ods
15. Invoice - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-Invoice-2.0.ods
16. Order - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-Order-2.0.ods
17. OrderCancellation - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-OrderCancellation-2.0.ods
18. OrderChange - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-OrderChange-2.0.ods
19. OrderResponse - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-OrderResponse-2.0.ods
20. OrderResponseSimple - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-OrderResponseSimple-2.0.ods
21. PackingList - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-PackingList-2.0.ods
22. Quotation - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-Quotation-2.0.ods
23. ReceiptAdvice - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-ReceiptAdvice-2.0.ods
24. Reminder - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-Reminder-2.0.ods
25. RemittanceAdvice - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-RemittanceAdvice-2.0.ods
26. Statement - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-Statement-2.0.ods
27. TransportationStatus - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-TransportationStatus-2.0.ods
28. Waybill - https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-Waybill-2.0.ods

**Total: 30 ODS files (2 core + 28 document types)**

### Conversion Methodology

**Tools Used:**
- **OASIS Crane-ods2obdgc** - Official XSLT stylesheet for ODS to GenericCode conversion
  - Source: https://github.com/oasis-tcs/ubl/tree/review/utilities/Crane-ods2obdgc
- **Saxon 9 HE** - XSLT 2.0 processor

**Conversion Command:**
```bash
java -jar saxon9he.jar \
  -xsl:Crane-ods2obdgc.xsl \
  -o:UBL-Entities-2.0.gc \
  -it:ods-uri \
  ods-uri=[comma-separated list of all 30 ODS file paths] \
  identification-uri=ident-UBL-2.0.xml \
  included-sheet-name-regex='^([Ll]($|[^o].*|o($|[^g].*|g($|[^s].*))))|^[^Ll].*'
```

**Result**: All 30 ODS files consolidated into a single GenericCode file with 2,181 entity rows.

### Why os-UBL-2.0?

We selected **os-UBL-2.0** (the official OASIS standard released 2006-12-12) over intermediate versions because:

1. **Official Release**: Final, approved standard - the authoritative version for UBL 2.0
2. **Complete Document Set**: Includes all document types available for UBL 2.0
3. **Reproducibility**: Being the official standard, it remains stable and permanently available in OASIS archive
4. **Historical Accuracy**: Represents the complete semantic model that forms the basis for UBL 2.1+
5. **Backwards Compatibility**: All subsequent versions (2.1, 2.2, 2.3, 2.4, 2.5) maintain backwards compatibility

### Reproducibility

To verify or reproduce the UBL 2.0 conversion:

**Prerequisites:**
```bash
# Clone OASIS UBL repository
git clone --depth 1 https://github.com/oasis-tcs/ubl.git /tmp/ubl-official

# Download Saxon9HE
wget https://sourceforge.net/projects/saxon/files/Saxon-HE/11/Java/SaxonHE11-4J.zip -O /tmp/saxon.zip
unzip /tmp/saxon.zip -d /tmp/ubl-official/utilities/saxon9he/
```

**Download and Convert:**
```bash
# Download all 30 ODS files from os-UBL-2.0
TMPDIR=$(mktemp -d)
curl -A "Mozilla/5.0" -o "$TMPDIR/UBL-CommonLibrary-2.0.ods" \
  https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/common/UBL-CommonLibrary-2.0.ods
curl -A "Mozilla/5.0" -o "$TMPDIR/UBL-qDT-2.0.ods" \
  https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/common/UBL-qDT-2.0.ods

# Download all 28 document type files (see URLs above)
for doc in ApplicationResponse AttachedDocument BillOfLading Catalogue ...; do
  curl -A "Mozilla/5.0" -o "$TMPDIR/UBL-$doc-2.0.ods" \
    https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-$doc-2.0.ods
done

# Run conversion
java -jar /tmp/ubl-official/utilities/saxon9he/saxon9he.jar \
  -xsl:/tmp/ubl-official/utilities/Crane-ods2obdgc/Crane-ods2obdgc.xsl \
  -o:UBL-Entities-2.0.gc \
  -it:ods-uri \
  ods-uri="$TMPDIR/UBL-CommonLibrary-2.0.ods,$TMPDIR/UBL-qDT-2.0.ods,..." \
  identification-uri=$TMPDIR/ident-UBL-2.0.xml \
  included-sheet-name-regex='^([Ll]($|[^o].*|o($|[^g].*|g($|[^s].*))))|^[^Ll].*'
```

**Verification:**
```bash
# Validate XML
xmllint --noout UBL-Entities-2.0.gc

# Check entity count
grep -c '<Row>' UBL-Entities-2.0.gc  # Should be 2181

# List all models
grep -A1 'ColumnRef="ModelName"' UBL-Entities-2.0.gc | grep '<SimpleValue>' | \
  sed 's/.*<SimpleValue>//' | sed 's/<\/SimpleValue>.*//' | sort -u
```

## Historical Archive Contents

**Version Coverage:**
- **UBL 2.0** (2006): 1 synthesized file from os-UBL-2.0
- **UBL 2.1** (2013): 8 release stages (prd1 through os)
- **UBL 2.2** (2018): 6 release stages
- **UBL 2.3** (2021): 7 release stages
- **UBL 2.4** (2024): 4 release stages
- **UBL 2.5** (2025): 2 release stages (latest: csd02)

**Total**: 28 releases, 55 GenericCode files

### File Organization

Each release directory in `/history/` follows the OASIS naming convention and contains:
```
{release-stage}-UBL-{version}/mod/
├── UBL-Entities-{version}.gc
└── UBL-Signature-Entities-{version}.gc  (if available)
```

These files are direct downloads from OASIS, with the exception of UBL 2.0, which is synthesized from ODS.

## Using This Archive

### View Complete Release History

See `/docs/historical-releases.md` for a comprehensive list of all 28+ releases with direct OASIS documentation links.

### Git Blame Analysis

```bash
# Track changes to the Invoice/Order semantic model
git log -p history/os-UBL-2.1/mod/UBL-Entities-2.1.gc | head -100

# See all commits affecting semantic models
git log --all history/*/mod/UBL-Entities-*.gc
```

### Compare Versions

```bash
# Diff between UBL 2.0 and 2.1
diff history/os-UBL-2.0/mod/UBL-Entities-2.0.gc \
       history/os-UBL-2.1/mod/UBL-Entities-2.1.gc | head -50

# Track a specific entity across versions
for version in history/*/mod/UBL-Entities-*.gc; do
  echo "=== $version ==="
  grep "Invoice" "$version" | head -5
done
```

## Key Design Decisions

1. **UBL 2.0 Synthesis**: UBL 2.0 was released as ODS, not GenericCode. We synthesized GenericCode to enable continuous git history from UBL 2.0 onward.

2. **Official Releases Only**: We archive the complete intermediate release stages (prd, csd, csprd, cs, cos, os) to show the full evolution, not just official standards.

3. **Local Archival**: Local copies enable offline access, faster git operations, and permanent preservation even if OASIS URLs change.

4. **Source Traceability**: Every file includes direct OASIS URLs so the source can always be verified.

5. **No Manual Edits**: All files are preserved exactly as provided by OASIS (except UBL 2.0, which is synthesized).

## Acknowledgments

This archive makes extensive use of tools and expertise from the broader UBL community:

- **Crane Softwrights Ltd.** (http://www.CraneSoftwrights.com) - For the GenericCode Toolkit
- **G. Ken Holman** - Principal at Crane Softwrights, pioneering work in XSLT and semantic standardization
- **OASIS** - For the UBL specification, tools, and community support
- **Saxonica Ltd.** - For the Saxon XSLT processor
- **UBL Technical Committee** - For 20 years of semantic model development

## References

- **OASIS UBL Portal**: https://docs.oasis-open.org/ubl/
- **Official Repository**: https://github.com/oasis-tcs/ubl
- **UBL Technical Committee**: https://www.oasis-open.org/committees/tc_home.php?wg_abbrev=ubl
- **GenericCode Specification**: https://docs.oasis-open.org/codelist/genericode/v1.0/
- **Crane-ods2obdgc Tool**: https://cranesoftwrights.github.io/resources/ubl/
- **Crane Softwrights**: http://www.CraneSoftwrights.com
- **Saxon XSLT**: https://www.saxonica.com/

## Notes

- **UBL 2.0 ODS Sources** (`history/os-UBL-2.0/mod/`): Downloaded from OASIS archive (2006)
- **UBL 2.0 GenericCode** (`history/generated/os-UBL-2.0/mod/`): Synthesized via Crane-ods2obdgc (official OASIS tool)
- **UBL 2.1-2.5**: Direct GenericCode files from OASIS
- **Signature Entities**: Not available for prd1/prd2 of UBL 2.1 (never published)
- **CSD01/CSD02 UBL 2.3**: Not publicly released; first release was CSD03
- **Generated vs. Downloaded**: Files we synthesized are separated in `history/generated/` to distinguish from pure OASIS files
- **Complete Coverage**: Semantic model history from UBL 2.0 (2006) through UBL 2.5 (2025)

---

**Repository Created**: February 11, 2026
**Total Releases Archived**: 28
**Total GenericCode Files**: 55 (1 synthesized + 54 from OASIS)
**Semantic Model Coverage**: Complete history from UBL 2.0 through UBL 2.5
