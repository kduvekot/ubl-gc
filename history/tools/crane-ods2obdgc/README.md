# Crane-ods2obdgc XSLT Stylesheet

## Overview

Official OASIS tool for converting OpenDocument Spreadsheet (ODS) semantic model files to GenericCode XML format.

**File**: `Crane-ods2obdgc.xsl`
**Source**: https://github.com/oasis-tcs/ubl/tree/review/utilities/Crane-ods2obdgc
**License**: OASIS (see source repository)

## Purpose

The Crane-ods2obdgc stylesheet:
- Parses ODS spreadsheet files (which are ZIP archives containing XML)
- Extracts semantic model data (rows and columns)
- Generates GenericCode XML format output
- Filters unwanted sheets (e.g., "Logs" sheets marked as proprietary)

## Usage

Requires XSLT 2.0 processor (e.g., Saxon):

```bash
java -jar saxon9he.jar \
  -xsl:Crane-ods2obdgc.xsl \
  -o:output.gc \
  -it:ods-uri \
  ods-uri="file1.ods,file2.ods,file3.ods" \
  identification-uri=ident.xml \
  included-sheet-name-regex='regex-pattern'
```

## Parameters

- **ods-uri**: Comma-separated list of ODS file paths
- **identification-uri**: Path to identification XML file (defines metadata)
- **included-sheet-name-regex**: Regex pattern for sheets to include/exclude

### Example (UBL 2.0)

```bash
java -jar ../saxon9he/saxon9he.jar \
  -xsl:Crane-ods2obdgc.xsl \
  -o:UBL-Entities-2.0.gc \
  -it:ods-uri \
  ods-uri="UBL-CommonLibrary-2.0.ods,UBL-qDT-2.0.ods,UBL-Invoice-2.0.ods,..." \
  identification-uri=ident-UBL-2.0.xml \
  included-sheet-name-regex='^([Ll]($|[^o].*|o($|[^g].*|g($|[^s].*))))|^[^Ll].*'
```

The regex pattern excludes sheets named "Logs" (proprietary data).

## Output

Produces GenericCode XML file with:
- Column definitions (schema)
- Row data (semantic entities)
- Metadata (version, identification)

## References

- **Official Source**: https://github.com/oasis-tcs/ubl
- **GenericCode Spec**: https://docs.oasis-open.org/codelist/genericode/v1.0/
- **UBL Documentation**: https://docs.oasis-open.org/ubl/

## Integration with This Project

Used for:
- **UBL 2.0 GenericCode Synthesis**: Converting 30 ODS files to single unified GenericCode

See `/README.md` > "UBL 2.0 GenericCode Synthesis" for complete details.
