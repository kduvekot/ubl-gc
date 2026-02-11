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

For complete usage instructions, see `/README.md` > "UBL 2.0 GenericCode Synthesis" > "Reproducibility"

Quick example:
```bash
java -jar tools/saxon9he/saxon9he.jar \
  -xsl:tools/crane-ods2obdgc/Crane-ods2obdgc.xsl \
  -o:output.gc \
  -it:ods-uri \
  ods-uri="file1.ods,file2.ods,..." \
  identification-uri=ident.xml
```

## License and Attribution

All tools are used under their respective licenses:
- Crane-ods2obdgc: OASIS license (official UBL repository)
- Saxon 9 HE: Mozilla Public License
- Scripts: Created for this project

For official source code and licenses, see:
- OASIS UBL: https://github.com/oasis-tcs/ubl
- Saxon: https://sourceforge.net/projects/saxon/

## Auditability

Every generated file references these tools:
- Which tool was used
- Exact tool version/location
- Input files used
- Complete conversion command

This enables full verification that outputs can be reproduced using the documented tools and inputs.
