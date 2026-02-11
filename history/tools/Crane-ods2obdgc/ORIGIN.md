# Crane-ods2obdgc Stylesheet - Origin & Provenance

## Official Source

This directory contains the **complete Crane-ods2obdgc tool** as distributed by OASIS in the UBL Technical Committee repository.

**Official Repository:** https://github.com/oasis-tcs/ubl/tree/utilities/Crane-ods2obdgc

## Creator Information

- **Company**: Crane Softwrights Ltd.
- **Website**: http://www.CraneSoftwrights.com
- **Principal/Creator**: G. Ken Holman
- **Tool Name**: GenericCode Toolkit (GCTK)
- **Specialization**: XML, XSLT, ODS, and semantic data processing

## Version Information

From source code header (Crane-ods2obdgc.xsl):
```
$Id: Crane-ods2obdgc.xsl,v 1.8 2020/08/08 16:53:12 admin Exp $
```

- **Last Update**: August 8, 2020 (Version 1.8)
- **Status**: Actively maintained in OASIS repository

## License & Copyright

```
Copyright (C) - Crane Softwrights Ltd.
              - http://www.CraneSoftwrights.com

Portions copyright (C) - OASIS Open 2015. All Rights Reserved.
                       - http://www.oasis-open.org/who/intellectualproperty.php
```

**License Type**: Open source (see full license text in readme files)

## Directory Contents

### Main Files

1. **Crane-ods2obdgc.xsl** (16 KB)
   - Primary XSLT 2.0 stylesheet
   - Transforms ODS (OpenDocument Spreadsheet) to GenericCode XML
   - Requires Saxon XSLT 2.0 processor

2. **readme-Crane-ods2obdgc.txt** (12 KB)
   - Complete documentation for the stylesheet
   - Usage instructions and parameter explanations
   - Input/output format specifications
   - Examples and troubleshooting

3. **exampleIdentification.xml** (326 bytes)
   - Template for metadata injection
   - Example of Identification block structure
   - Used during ODS→GC conversion

4. **massageModelName-2.1.xml** (1.4 KB)
   - Name transformation rules for compatibility
   - Handles Google Docs worksheet name length limitations
   - Specifically for UBL 2.1 compatibility

5. **Empty CCTS Model.ods** (14 KB)
   - Template ODS file for semantic model editing
   - Pre-configured with proper structure and headers
   - Starting point for creating new semantic models

### Support Utilities

Located in `support/` subdirectory:

1. **odsCommon.xsl** (26 KB)
   - Common utility functions for ODS processing
   - Imported by main stylesheet
   - Handles ODS ZIP/XML parsing

2. **gcExportSubset.xsl** (11 KB)
   - Exports subset of GenericCode entities
   - Utility for selective processing
   - Used for advanced filtering operations

3. **readme-Crane-ods2obdgc.html** (87 KB)
   - HTML version of complete documentation
   - Rich formatting with examples
   - Comprehensive reference guide

## Integration with OASIS UBL

This tool is integrated into the official OASIS UBL build process:

- **Location in OASIS Repo**: `utilities/Crane-ods2obdgc/`
- **Purpose**: Converts semantic models from ODS format to GenericCode XML
- **Usage**: Part of official UBL release generation
- **Maintained By**: OASIS UBL Technical Committee with Crane Softwrights contributions

## Verification & Authenticity

### ✅ Verified Against Official Repository

This tool has been verified to match the official OASIS UBL TC repository:

**Official Repository Location:**
- **Clone**: https://github.com/oasis-tcs/ubl.git
- **Path in Repo**: `utilities/Crane-ods2obdgc/`
- **Local Backup**: `/tmp/ubl-official/utilities/Crane-ods2obdgc/`

**Verification Results:**
```
File: Crane-ods2obdgc.xsl
MD5 Hash (Local):    e017a278fcdfb9f767b8a1893bb13f6c
MD5 Hash (Official): e017a278fcdfb9f767b8a1893bb13f6c
Status: ✅ IDENTICAL
```

All support files also verified:
- ✅ Empty CCTS Model.ods
- ✅ exampleIdentification.xml
- ✅ massageModelName-2.1.xml
- ✅ readme-Crane-ods2obdgc.txt
- ✅ support/odsCommon.xsl
- ✅ support/gcExportSubset.xsl
- ✅ support/readme-Crane-ods2obdgc.html

### Additional Verification Methods

1. **Clone Official Repository**: https://github.com/oasis-tcs/ubl.git
2. **Compare File Checksums**:
   ```bash
   md5sum history/tools/Crane-ods2obdgc/Crane-ods2obdgc.xsl
   # Expected: e017a278fcdfb9f767b8a1893bb13f6c
   ```
3. **Check Copyright Headers**: All files retain original OASIS/Crane Softwrights copyright
4. **Contact**:
   - **Crane Softwrights**: info@CraneSoftwrights.com or +1 (613) 489-0999
   - **OASIS UBL TC**: ubl-development@lists.oasis-open.org

## How This Tool Was Used in This Archive

The Crane-ods2obdgc stylesheet was used to generate GenericCode files for all UBL 2.0 stages:

- **prd-UBL-2.0**: 32 ODS files → 1,604 semantic rows
- **prd2-UBL-2.0**: 33 ODS files → 2,139 semantic rows
- **prd3-UBL-2.0**: 30 ODS files → 2,074 semantic rows
- **prd3r1-UBL-2.0**: 30 ODS files → 2,074 semantic rows
- **cs-UBL-2.0**: 30 ODS files → 2,074 semantic rows
- **os-UBL-2.0**: 30 ODS files → 2,074 semantic rows
- **os-update-UBL-2.0**: 30 ODS files → 2,074 semantic rows
- **errata-UBL-2.0**: 30 ODS files → 2,074 semantic rows

All conversions verified with:
- XML validation (xmllint)
- Row count verification
- Semantic model integrity checks
- OASIS GenericCode schema compliance

## Key Acknowledgments

- **Crane Softwrights Ltd.** - For creating and maintaining this powerful tool
- **G. Ken Holman** - For pioneering work in XSLT and semantic standardization
- **OASIS** - For integrating this tool into the official UBL distribution
- **UBL Technical Committee** - For ensuring tool quality and compatibility

## References

- **Crane Softwrights Website**: http://www.CraneSoftwrights.com
- **GenericCode Specification**: https://docs.oasis-open.org/codelist/genericode/v1.0/
- **OASIS UBL Repository**: https://github.com/oasis-tcs/ubl
- **UBL Specification**: https://docs.oasis-open.org/ubl/

---

**Archive Integration Date**: February 11, 2026
**Tool Version Used**: 1.8 (2020-08-08)
**Archive Status**: Complete and verified
