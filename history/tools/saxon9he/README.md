# Saxon 9 HE - XSLT 2.0 Processor

## Overview

Open-source XSLT and XQuery processor supporting XSLT 2.0 specification.

**File**: `saxon9he.jar`
**Source**: https://sourceforge.net/projects/saxon/files/Saxon-HE/
**License**: Mozilla Public License (see source)
**Purpose**: Executes XSLT stylesheets (required for Crane-ods2obdgc)

## Purpose

Saxon 9 HE is needed to:
- Parse and execute XSLT 2.0 stylesheets
- Process XML input and transformations
- Generate XML output
- Support advanced XSLT 2.0 features used by Crane-ods2obdgc

The Crane-ods2obdgc stylesheet requires XSLT 2.0 capabilities that are not available in simpler XSLT 1.0 processors.

## Installation

This JAR file is a pre-built Java executable:

```bash
java -jar saxon9he.jar [options]
```

## Basic Usage

```bash
# Transform XML with XSLT stylesheet
java -jar saxon9he.jar \
  -xsl:stylesheet.xsl \
  -o:output.xml \
  input.xml

# Execute stylesheet with initial template (required for Crane-ods2obdgc)
java -jar saxon9he.jar \
  -xsl:stylesheet.xsl \
  -o:output.xml \
  -it:template-name \
  param1=value1 \
  param2=value2
```

## For Crane-ods2obdgc

Saxon 9 HE is used to execute the Crane-ods2obdgc XSLT stylesheet:

```bash
java -jar saxon9he.jar \
  -xsl:../crane-ods2obdgc/Crane-ods2obdgc.xsl \
  -o:output.gc \
  -it:ods-uri \
  ods-uri="file1.ods,file2.ods,..." \
  identification-uri=ident.xml
```

Key options:
- `-xsl`: Path to XSLT stylesheet
- `-o`: Output file path
- `-it`: Initial template name (must use `-it:ods-uri` for Crane-ods2obdgc)
- Additional parameters: Pass to stylesheet as needed

## System Requirements

- Java Runtime Environment (JRE) 1.6 or later
- Sufficient heap memory for large transformations:
  ```bash
  java -Xmx2G -jar saxon9he.jar ...
  ```

## Documentation

- **Official Documentation**: https://www.saxonica.com/
- **Getting Started**: https://www.saxonica.com/documentation/index.html
- **XSLT 2.0 Spec**: https://www.w3.org/TR/xslt20/

## Integration with This Project

Used for:
- **UBL 2.0 Conversion**: Executes Crane-ods2obdgc XSLT to synthesize GenericCode from ODS files
- Part of the reproducible conversion toolchain

See `/README.md` > "UBL 2.0 GenericCode Synthesis" for complete details.
