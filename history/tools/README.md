# UBL Conversion Tools

This directory contains all tools and scripts used to generate GenericCode files from ODS sources.

## Directory Structure

```
tools/
├── README.md                          (this file)
├── crane-ods2obdgc/
│   ├── Crane-ods2obdgc.xsl            (Official OASIS XSLT stylesheet)
│   └── README.md                      (Tool documentation)
├── saxon9he/
│   ├── saxon9he.jar                   (Saxon 9 HE XSLT processor)
│   └── README.md                      (Tool documentation)
└── scripts/
    ├── ubl20-ods-to-gc-convert.sh    (Conversion script for UBL 2.0)
    └── README.md                      (Script documentation)
```

## Purpose

These tools enable reproducible conversion of UBL ODS (OpenDocument Spreadsheet) semantic model files to GenericCode (GC) XML format.

Currently used for:
- **UBL 2.0 GenericCode Synthesis**: Converting 30 ODS files to single unified GenericCode file

## Tools Overview

### Crane-ods2obdgc XSLT Stylesheet
Official OASIS tool for converting ODS to GenericCode format
- Source: https://github.com/oasis-tcs/ubl/tree/review/utilities/Crane-ods2obdgc
- License: OASIS (see source repository)
- Purpose: Extracts semantic model data from ODS spreadsheets and generates GenericCode XML

### Saxon 9 HE XSLT Processor
Open-source XSLT 2.0 processor required to execute the Crane-ods2obdgc stylesheet
- Source: https://sourceforge.net/projects/saxon/
- License: Mozilla Public License (see source)
- Version: 9 HE (Home Edition)

### Conversion Scripts
Bash scripts that orchestrate the full conversion process:
- Download ODS files from OASIS
- Run XSLT transformation via Saxon
- Validate output

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

📋 **[TOOL_VERIFICATION.md](TOOL_VERIFICATION.md)** - Tools and verification report
- Tool inventory and status
- Verification results for all 8 UBL 2.0 stages
- Known issues and workarounds
- Quality assurance procedures
- Performance characteristics

## License and Attribution

### Tools Authors & Credits

**Crane-ods2obdgc XSLT Stylesheet**
- **Creator**: Crane Softwrights Ltd. (http://www.CraneSoftwrights.com)
- **Principal**: G. Ken Holman - Expert in XML, XSLT, and UBL
- **Part of**: GenericCode Toolkit
- **License**: Copyright © Crane Softwrights Ltd. | Portions © OASIS Open 2015
- **Source**: https://github.com/oasis-tcs/ubl/tree/review/utilities/Crane-ods2obdgc

**Saxon 9 HE XSLT Processor**
- **Creator**: Saxonica Ltd. (https://www.saxonica.com/)
- **License**: Mozilla Public License
- **Source**: https://sourceforge.net/projects/saxon/

**Conversion Scripts & Documentation**
- **Created for**: This UBL semantic model archive
- **License**: Same as repository

### Acknowledgments

This project would not be possible without:
- **Crane Softwrights Ltd.** for the powerful GenericCode conversion toolkit
- **G. Ken Holman** for pioneering work in XML/XSLT and standardization
- **OASIS** for the UBL specification and related tools
- **Saxonica** for the robust XSLT processor

### Official Sources

For official source code and licenses:
- OASIS UBL Repository: https://github.com/oasis-tcs/ubl
- Crane Softwrights: http://www.CraneSoftwrights.com
- Saxon XSLT Processor: https://www.saxonica.com/

## Auditability

Every generated file references these tools:
- Which tool was used
- Exact tool version/location
- Input files used
- Complete conversion command

This enables full verification that outputs can be reproduced using the documented tools and inputs.
