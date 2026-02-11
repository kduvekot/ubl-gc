# UBL Conversion Tools

This directory contains all tools and scripts used to generate GenericCode files from ODS sources.

## Directory Structure

```
tools/
├── README.md                          (this file - complete reference)
├── Crane-ods2obdgc/
│   ├── Crane-ods2obdgc.xsl            (Official OASIS XSLT stylesheet)
│   └── support/                       (Supporting files and utilities)
├── saxon9he/
│   └── saxon9he.jar                   (Saxon 9 HE XSLT processor)
└── scripts/
    └── ubl20-ods-to-gc-convert.sh    (Conversion script for UBL 2.0)
```

## Purpose

These tools enable reproducible conversion of UBL ODS (OpenDocument Spreadsheet) semantic model files to GenericCode (GC) XML format.

Currently used for:
- **UBL 2.0 GenericCode Synthesis**: Converting 30+ ODS files to unified GenericCode files

---

## Tool #1: Crane-ods2obdgc XSLT Stylesheet

**Purpose:** Official OASIS tool that converts ODS spreadsheets to GenericCode XML format

### Creator Information

- **Company**: Crane Softwrights Ltd. (http://www.CraneSoftwrights.com)
- **Creator**: G. Ken Holman - Expert in XML, XSLT, and semantic standardization
- **Tool Name**: GenericCode Toolkit (GCTK)
- **Specialization**: XML, XSLT, ODS, and semantic data processing

### Version Information

```
$Id: Crane-ods2obdgc.xsl,v 1.8 2020/08/08 16:53:12 admin Exp $
```

- **Version**: 1.8
- **Last Update**: August 8, 2020
- **Status**: Actively maintained in OASIS repository

### License & Copyright

```
Copyright (C) - Crane Softwrights Ltd.
              - http://www.CraneSoftwrights.com

Portions copyright (C) - OASIS Open 2015. All Rights Reserved.
                       - http://www.oasis-open.org/who/intellectualproperty.php
```

### Features

- Extracts semantic model data from ODS worksheets
- Generates valid GenericCode XML structure
- Supports metadata injection (Identification block)
- Configurable worksheet filtering via regex
- Comprehensive documentation included

### Verification Status

✅ **Verified against official OASIS UBL TC repository**

- **Official Source**: https://github.com/oasis-tcs/ubl/tree/utilities/Crane-ods2obdgc
- **MD5 Hash Match**: `e017a278fcdfb9f767b8a1893bb13f6c` (IDENTICAL)
- **Local Verification**: All support files verified
- **Integration**: Part of official OASIS UBL release generation

### Supporting Files

Located in `Crane-ods2obdgc/` directory:

1. **Crane-ods2obdgc.xsl** (16 KB) - Primary XSLT 2.0 stylesheet
2. **readme-Crane-ods2obdgc.txt** (12 KB) - Complete documentation
3. **exampleIdentification.xml** - Metadata template
4. **massageModelName-2.1.xml** - Name transformation rules
5. **Empty CCTS Model.ods** - ODS template for semantic model editing
6. **support/odsCommon.xsl** (26 KB) - Common utility functions
7. **support/gcExportSubset.xsl** (11 KB) - Entity filtering utilities
8. **support/readme-Crane-ods2obdgc.html** (87 KB) - HTML documentation

### Contact Information

- **Crane Softwrights**: info@CraneSoftwrights.com or +1 (613) 489-0999
- **OASIS UBL TC**: ubl-development@lists.oasis-open.org

---

## Tool #2: Saxon 9 HE XSLT Processor

**Purpose:** Required XSLT 2.0 processor to execute the Crane-ods2obdgc stylesheet

### Creator Information

- **Company**: Saxonica Ltd. (https://www.saxonica.com/)
- **Creator**: Michael Kay
- **Product**: Saxon XSLT and XQuery Processor
- **Editions**: HE (Home Edition - open source), PE (Professional), EE (Enterprise)

### Version Information

- **Version**: Saxon 9 HE
- **Edition**: Home Edition (Free, Open Source)
- **JAR File**: saxon9he.jar (4.9 MB)
- **License**: Mozilla Public License 2.0

### System Requirements

- **Java Runtime**: JRE 8 or later
- **Minimum Memory**: 256 MB heap (typical usage)
- **No External Dependencies**: Self-contained JAR file

### Features & Capabilities

- **XSLT Version**: 2.0 support (full W3C specification)
- **XPath Support**: 2.0 level with extensions
- **Performance**: Excellent for semantic model processing
- **Stability**: Production-ready, widely used in enterprise systems
- **Only processor** fully supporting XSLT 2.0 (required by Crane stylesheet)

### Verification Status

✅ **Successfully used for all 8 UBL 2.0 stage conversions**

| Stage | ODS Files | Result | Status |
|-------|-----------|--------|--------|
| prd-UBL-2.0 | 32 | 1,604 rows | ✅ Verified |
| prd2-UBL-2.0 | 33 | 2,139 rows | ✅ Verified |
| prd3-UBL-2.0 | 30 | 2,074 rows | ✅ Verified |
| prd3r1-UBL-2.0 | 30 | 2,074 rows | ✅ Verified |
| cs-UBL-2.0 | 30 | 2,074 rows | ✅ Verified |
| os-UBL-2.0 | 30 | 2,074 rows | ✅ Verified |
| os-update-UBL-2.0 | 30 | 2,074 rows | ✅ Verified |
| errata-UBL-2.0 | 30 | 2,074 rows | ✅ Verified |

**Total**: 245 ODS files processed, 100% success rate

### Installation & Verification

**Check Java Installation:**
```bash
java -version
# Output: openjdk version "11.0.13" 2021-10-19 (or newer)
```

**Verify Saxon JAR:**
```bash
ls -lh history/tools/saxon9he/saxon9he.jar
# Output: -rw-r--r-- 1 root root 4.9M Feb 11 2026 saxon9he.jar

java -jar history/tools/saxon9he/saxon9he.jar -version
# Output: Saxon-HE 9.x.x (version information)
```

---

## Tool #3: Conversion Scripts

**Purpose:** Bash scripts that orchestrate the full conversion process

**Available Scripts:**
- `ubl20-ods-to-gc-convert.sh` - Single-stage ODS to GenericCode conversion
- `ubl20-all-stages-convert.sh` - Batch conversion of multiple UBL 2.0 stages

**Features:**
- Download ODS files from OASIS
- Run XSLT transformation via Saxon
- Validate output
- Proper error handling and logging

---

## Usage

### Quick Start

**For UBL 2.0 conversion:**
```bash
./scripts/ubl20-ods-to-gc-convert.sh [output_dir] [input_dir]
```

**For manual conversion:**
```bash
java -jar saxon9he/saxon9he.jar \
  -xsl:Crane-ods2obdgc/Crane-ods2obdgc.xsl \
  -o:output.gc \
  -it:ods-uri \
  ods-uri="file1.ods,file2.ods,..." \
  identification-uri=ident.xml
```

### Complete Documentation

📖 **[CONVERSION_GUIDE.md](CONVERSION_GUIDE.md)** - Step-by-step conversion instructions
- Quick start for UBL 2.0
- Manual conversion walkthrough
- Parameter explanations
- Detailed examples
- Troubleshooting guide

📋 **[TOOL_VERIFICATION.md](TOOL_VERIFICATION.md)** - Tool verification and known issues
- Known issues and workarounds
- Performance characteristics
- Quality assurance procedures

---

## License and Attribution

### Tools Authors & Credits

**Crane-ods2obdgc XSLT Stylesheet**
- **Creator**: Crane Softwrights Ltd. (http://www.CraneSoftwrights.com)
- **Principal**: G. Ken Holman - Expert in XML, XSLT, and UBL
- **License**: Copyright © Crane Softwrights Ltd. | Portions © OASIS Open 2015
- **Source**: https://github.com/oasis-tcs/ubl/tree/utilities/Crane-ods2obdgc

**Saxon 9 HE XSLT Processor**
- **Creator**: Saxonica Ltd. (https://www.saxonica.com/)
- **Creator**: Michael Kay
- **License**: Mozilla Public License 2.0
- **Source**: https://sourceforge.net/projects/saxon/

**Conversion Scripts & Documentation**
- **Created for**: This UBL semantic model archive
- **License**: Same as repository

### Acknowledgments

This project would not be possible without:
- **Crane Softwrights Ltd.** for the powerful GenericCode conversion toolkit
- **G. Ken Holman** for pioneering work in XML/XSLT and standardization
- **Saxonica Ltd.** for the robust Saxon XSLT processor
- **Michael Kay** for XSLT 2.0 processor development
- **OASIS** for the UBL specification and related tools
- **Mozilla Foundation** for the permissive MPL 2.0 license
- **UBL Technical Committee** for 20 years of semantic model development

### Official Sources

For official source code and licenses:
- **OASIS UBL Repository**: https://github.com/oasis-tcs/ubl
- **Crane Softwrights**: http://www.CraneSoftwrights.com
- **Saxon XSLT Processor**: https://www.saxonica.com/
- **GenericCode Specification**: https://docs.oasis-open.org/codelist/genericode/v1.0/
- **XSLT 2.0 Specification**: https://www.w3.org/TR/xslt20/
- **XPath 2.0 Specification**: https://www.w3.org/TR/xpath20/
- **MPL 2.0 License**: https://www.mozilla.org/en-US/MPL/2.0/

---

## Auditability

Every generated file references these tools:
- Which tool was used
- Exact tool version/location
- Input files used
- Complete conversion command

This enables full verification that outputs can be reproduced using the documented tools and inputs.

---

**Last Updated**: February 11, 2026
**Status**: All tools verified and production-ready ✅
