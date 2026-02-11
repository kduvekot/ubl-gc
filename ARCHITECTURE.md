# UBL Historical Semantic Archive - Architecture & Implementation

This document describes what was created, where files came from, and how everything is organized for complete auditability and reproducibility.

## Executive Summary

Created a complete historical archive of UBL GenericCode semantic model files from UBL 2.0 (2006) through UBL 2.5 (2025), with full git version control enabling complete blame tracking across 20 years of UBL development.

**Total Coverage**: 28 releases, 55 GenericCode files, complete from 2006-2026

## Data Sources & Origins

### UBL 2.0 (2006) - ODS Semantic Models

**Original Format**: OpenDocument Spreadsheet (ODS) - UBL 2.0 predates GenericCode format

**Source Files Downloaded**:
- All 30 ODS files from official OASIS UBL 2.0 release (os-UBL-2.0)
- **Base URL**: https://docs.oasis-open.org/ubl/os-UBL-2.0/
- **Location in archive**: `history/os-UBL-2.0/mod/`

**File List** (30 total):

Core files (2):
- UBL-CommonLibrary-2.0.ods
- UBL-qDT-2.0.ods (Qualified Datatypes)

Document types (28):
- ApplicationResponse, AttachedDocument, BillOfLading, Catalogue
- CatalogueDeletion, CatalogueItemSpecificationUpdate, CataloguePricingUpdate, CatalogueRequest
- CertificateOfOrigin, CreditNote, DebitNote, DespatchAdvice
- ForwardingInstructions, FreightInvoice, Invoice, Order
- OrderCancellation, OrderChange, OrderResponse, OrderResponseSimple
- PackingList, Quotation, ReceiptAdvice, Reminder
- RemittanceAdvice, Statement, TransportationStatus, Waybill

**Download Method**: curl with proper User-Agent header
```bash
curl -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  -o file.ods \
  https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/{common|maindoc}/UBL-...ods
```

### UBL 2.1-2.5 (2013-2025) - GenericCode Format

**Original Format**: GenericCode (GC) - OASIS XML standard for semantic models

**Source**: Official OASIS repository
- **Base URL**: https://docs.oasis-open.org/ubl/
- **Location in archive**: `history/{release-stage}-UBL-{version}/mod/`

**Coverage** (27 releases with 54 files total):

| Version | Stages | Files |
|---------|--------|-------|
| UBL 2.1 | 8 (prd1-prd4, csd4, cos1, cs1, os) | 16 |
| UBL 2.2 | 6 (csprd01-03, cos01, cs01, os) | 12 |
| UBL 2.3 | 7 (csd03-04, csprd01-02, cs01-02, os) | 14 |
| UBL 2.4 | 4 (csd01-02, cs01, os) | 8 |
| UBL 2.5 | 2 (csd01-02) | 4 |
| **Total** | **27 releases** | **54 files** |

**Note**: prd1/prd2 of UBL 2.1 never had Signature-Entities files published

## Generated Files

### UBL 2.0 GenericCode Synthesis

**File Generated**: `history/generated/os-UBL-2.0/mod/UBL-Entities-2.0.gc`

**Why Generated**: UBL 2.0 was released as ODS only (GenericCode format not adopted until UBL 2.1). We synthesized GenericCode to enable continuous git history from UBL 2.0 onward.

**Generation Method**:
1. Downloaded 30 ODS files from OASIS os-UBL-2.0
2. Used official OASIS Crane-ods2obdgc XSLT stylesheet to convert ODS to GenericCode
3. Processed with Saxon 9 HE XSLT processor
4. Validated output XML structure

**Tools Used**:
- **Crane-ods2obdgc XSLT**: Official OASIS tool from UBL repository
  - Source: https://github.com/oasis-tcs/ubl/tree/review/utilities/Crane-ods2obdgc
  - Location in archive: `history/tools/crane-ods2obdgc/Crane-ods2obdgc.xsl`

- **Saxon 9 HE**: XSLT 2.0 processor
  - Source: https://sourceforge.net/projects/saxon/
  - License: Mozilla Public License
  - Location in archive: `history/tools/saxon9he/saxon9he.jar`

**Conversion Command**:
```bash
java -jar saxon9he.jar \
  -xsl:Crane-ods2obdgc.xsl \
  -o:UBL-Entities-2.0.gc \
  -it:ods-uri \
  ods-uri="UBL-CommonLibrary-2.0.ods,UBL-qDT-2.0.ods,..." \
  identification-uri=ident-UBL-2.0.xml \
  included-sheet-name-regex='^([Ll]($|[^o].*|o($|[^g].*|g($|[^s].*))))|^[^Ll].*'
```

**Output Statistics**:
- File size: 3.3 MB
- Lines: 88,492
- Entity rows: 2,181
- Column definitions: 33
- Status: Valid XML, properly balanced tags

**Reproducibility**: Script provided at `history/tools/scripts/ubl20-ods-to-gc-convert.sh`
- Downloads/uses local ODS files
- Runs exact conversion command
- Validates output
- Reports statistics
- Allows independent verification

## Directory Organization

### Key Principle
- **`history/`**: Pure OASIS files (downloaded, unmodified)
- **`history/generated/`**: Files we created/synthesized
- **`history/tools/`**: Tools used for generation (for auditability)
- **Root README**: Comprehensive documentation

### Full Structure

```
/home/user/ubl-gc/
│
├── README.md                          Main documentation (all details here)
├── ARCHITECTURE.md                    This file
├── docs/
│   └── historical-releases.md         List of all 28+ releases with URLs
│
└── history/
    ├── README.md                      Brief overview
    │
    ├── os-UBL-2.0/mod/                ODS source files (30 files from OASIS)
    │   ├── UBL-CommonLibrary-2.0.ods
    │   ├── UBL-qDT-2.0.ods
    │   ├── UBL-Invoice-2.0.ods
    │   └── ... (27 more ODS files)
    │
    ├── prd1-UBL-2.1/mod/              GenericCode files from OASIS
    ├── prd2-UBL-2.1/mod/              (all 27 UBL 2.1-2.5 releases)
    ├── ... (other releases)
    ├── os-UBL-2.5/mod/
    ├── csd02-UBL-2.5/mod/
    │
    ├── generated/                     Our synthesized files
    │   └── os-UBL-2.0/mod/
    │       └── UBL-Entities-2.0.gc    Synthesized from 30 ODS files
    │
    └── tools/                         Conversion tools (for reproducibility)
        ├── README.md
        ├── crane-ods2obdgc/
        │   ├── Crane-ods2obdgc.xsl    Official OASIS XSLT stylesheet
        │   └── README.md
        ├── saxon9he/
        │   ├── saxon9he.jar           XSLT processor
        │   └── README.md
        └── scripts/
            ├── ubl20-ods-to-gc-convert.sh  Conversion orchestration script
            └── README.md
```

## File Counts & Statistics

**Downloads from OASIS**:
- 30 ODS files (UBL 2.0)
- 54 GenericCode files (UBL 2.1-2.5)
- **Total downloaded**: 84 files

**Generated**:
- 1 GenericCode file (UBL 2.0 synthesized)

**Tools Stored**:
- 1 XSLT stylesheet (Crane-ods2obdgc)
- 1 JAR file (Saxon 9 HE)
- 1 Bash script (conversion orchestration)
- 4 README files (documentation)

**Total Repository**: 91 content files + documentation

## Auditability & Reproducibility

### What Can Be Verified

1. **ODS Source Files**
   - Location: `history/os-UBL-2.0/mod/*.ods`
   - Origin: https://docs.oasis-open.org/ubl/os-UBL-2.0/
   - Can be re-downloaded and verified against OASIS

2. **Conversion Process**
   - Tools: `history/tools/` (Crane-ods2obdgc XSLT + Saxon JAR)
   - Script: `history/tools/scripts/ubl20-ods-to-gc-convert.sh`
   - Anyone can run the script and generate identical output

3. **GenericCode Results**
   - Location: `history/generated/os-UBL-2.0/mod/UBL-Entities-2.0.gc`
   - Can be verified by running the conversion script
   - File size, row counts, and contents are reproducible

4. **OASIS-Downloaded Files**
   - Locations: `history/{release}-UBL-{version}/mod/*.gc`
   - Can be re-downloaded from OASIS and compared
   - Sources documented in `/docs/historical-releases.md`

### Transparency

- **No black-box operations**: All tools and scripts are included
- **No proprietary code**: All tools are open-source (OASIS, Apache, Mozilla)
- **No undocumented steps**: Every action is documented or automated in scripts
- **Full traceability**: Each file has documented origin URL
- **Complete reproducibility**: Anyone can recreate any generated artifact

## Licenses & Attribution

### Tools Used

**Crane-ods2obdgc XSLT**
- Source: https://github.com/oasis-tcs/ubl
- License: OASIS (see repository)
- Purpose: Official ODS-to-GenericCode conversion tool

**Saxon 9 HE**
- Source: https://sourceforge.net/projects/saxon/
- License: Mozilla Public License
- Purpose: XSLT 2.0 processor (required for Crane-ods2obdgc)

**Scripts**
- Created for this project
- Available under the same license as the repository

## How to Use This Archive

### For Analysis
```bash
# View git history of semantic model changes
git log -p history/os-UBL-2.1/mod/UBL-Entities-2.1.gc

# Compare versions
diff history/os-UBL-2.0/generated/mod/UBL-Entities-2.0.gc \
     history/os-UBL-2.1/mod/UBL-Entities-2.1.gc

# Track evolution of specific entity
for version in history/*/mod/UBL-Entities-*.gc; do
  grep "Invoice" "$version" | head -2
done
```

### For Verification
```bash
# Download fresh ODS files and reconvert
cd /tmp
mkdir ubl20-verify
cd ubl20-verify
for doc in Invoice Order Quotation ...; do
  curl -O https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-$doc-2.0.ods
done

# Run conversion
/path/to/repo/history/tools/scripts/ubl20-ods-to-gc-convert.sh . .

# Compare with archived version
diff UBL-Entities-2.0.gc /path/to/repo/history/generated/os-UBL-2.0/mod/UBL-Entities-2.0.gc
```

### For Extension
```bash
# If converting other UBL versions or documents:
# 1. Copy conversion script
# 2. Modify ODS file list
# 3. Update identification file
# 4. Run with new parameters
# 5. Store results in history/generated/
```

## Key Design Decisions

1. **Separate ODS Sources from Generated GC**
   - ODS files mirror OASIS exactly (for verification)
   - Generated GC kept in separate `history/generated/` directory
   - Clear distinction between downloaded and synthesized content

2. **Include All Tools**
   - Crane-ods2obdgc XSLT and Saxon JAR stored in repository
   - Eliminates dependency on external tool availability
   - Enables long-term reproducibility

3. **Comprehensive Documentation**
   - Root README with complete synthesis details
   - Tool-specific READMEs with usage instructions
   - Script documentation with examples
   - Architecture document (this file)

4. **Git-Based History**
   - Every release stage in separate commit
   - Full blame tracking across all versions
   - Complete audit trail of when files were added

5. **Auditability First**
   - Every file has documented origin
   - Tools/scripts included for verification
   - Conversion process fully transparent
   - No trust required beyond OASIS source

## Summary

This archive provides a **complete, auditable, reproducible historical record of UBL semantic models** from the beginning of UBL 2.0 (2006) through UBL 2.5 (2025). Everything was created with:

- ✅ Complete source documentation
- ✅ Transparent conversion methodology
- ✅ All tools included for verification
- ✅ Full reproducibility
- ✅ Git-based version control
- ✅ Zero dependency on external trust

Anyone can independently verify any aspect of this archive by re-downloading source files from OASIS and running the provided scripts.

---

**Archive Created**: February 11, 2026
**Total Coverage**: UBL 2.0-2.5 (20 years of development)
**Files Archived**: 91 content files + documentation
**Status**: Complete and auditable
