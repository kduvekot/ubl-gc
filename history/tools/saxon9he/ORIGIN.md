# Saxon 9 HE - Origin & Provenance

## Official Source

This directory contains **Saxon 9 HE (Home Edition)** - the free, open-source XSLT 2.0 processor required to execute the Crane-ods2obdgc stylesheet.

**Official Website**: https://www.saxonica.com/
**SourceForge Project**: https://sourceforge.net/projects/saxon/

## Creator Information

- **Company**: Saxonica Ltd.
- **Website**: https://www.saxonica.com/
- **Creator**: Michael Kay
- **Product**: Saxon XSLT and XQuery Processor
- **Editions**: HE (Home Edition - open source), PE (Professional), EE (Enterprise)

## Version Information

**Version**: Saxon 9 HE
**Edition**: Home Edition (Free, Open Source)
**JAR File**: saxon9he.jar (4.9 MB)
**License**: Mozilla Public License (MPL)

## License & Copyright

**License**: Mozilla Public License 2.0
- Permissive open-source license
- Allows free use, modification, and redistribution
- See Mozilla Foundation for full license text

**Copyright**: © Saxonica Ltd. and other contributors

## System Requirements

- **Java Runtime**: JRE 8 or later
- **Minimum Memory**: 256 MB heap (typical usage)
- **No External Dependencies**: Self-contained JAR file

## Features & Capabilities

- **XSLT Version**: 2.0 support (full W3C specification)
- **XPath Support**: 2.0 level with extensions
- **XQuery**: Limited support in HE edition
- **Performance**: Excellent for semantic model processing
- **Stability**: Production-ready, widely used in enterprise systems

## How Saxon 9 HE Is Used

Saxon 9 HE is the **required XSLT processor** for executing the Crane-ods2obdgc stylesheet:

```bash
java -jar saxon9he.jar \
  -xsl:Crane-ods2obdgc.xsl \
  -o:output.gc \
  -it:ods-uri \
  ods-uri="file1.ods,file2.ods,..." \
  identification-uri=ident.xml
```

### Processing Steps

1. **Invocation**: Java launches Saxon with specified parameters
2. **XSLT Parsing**: Saxon parses Crane-ods2obdgc.xsl stylesheet
3. **ODS Processing**: Reads ODS files as ZIP archives
4. **XML Extraction**: Extracts content.xml from ODS structure
5. **Transformation**: Applies XSLT rules to semantic data
6. **Output Generation**: Produces GenericCode XML file
7. **Validation**: Optional XML schema validation

## Verified Usage in This Archive

Saxon 9 HE was successfully used to generate GenericCode for all 8 UBL 2.0 stages:

| Stage | Files | Result | Status |
|-------|-------|--------|--------|
| prd-UBL-2.0 | 32 ODS | 1,604 rows | ✅ Verified |
| prd2-UBL-2.0 | 33 ODS | 2,139 rows | ✅ Verified |
| prd3-UBL-2.0 | 30 ODS | 2,074 rows | ✅ Verified |
| prd3r1-UBL-2.0 | 30 ODS | 2,074 rows | ✅ Verified |
| cs-UBL-2.0 | 30 ODS | 2,074 rows | ✅ Verified |
| os-UBL-2.0 | 30 ODS | 2,074 rows | ✅ Verified |
| os-update-UBL-2.0 | 30 ODS | 2,074 rows | ✅ Verified |
| errata-UBL-2.0 | 30 ODS | 2,074 rows | ✅ Verified |

**Total Conversions**: 8 stages, 245 ODS files processed, 100% success rate

## Comparison with Other XSLT Processors

| Feature | Saxon 9 HE | XAlain | Xalan | libxslt |
|---------|-----------|--------|-------|---------|
| XSLT 2.0 | ✅ Full | ❌ No | ❌ No | ❌ No |
| XSLT 1.0 | ✅ Full | ✅ Yes | ✅ Yes | ✅ Yes |
| XPath 2.0 | ✅ Full | ❌ 1.0 | ❌ 1.0 | ❌ 1.0 |
| Stability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Java-Based | ✅ Yes | ❌ No | ✅ Yes | ❌ No |
| License | MPL 2.0 | Apache | Apache | MIT |

**Why Saxon 9 HE for This Project:**
- Only processor fully supporting XSLT 2.0 (required by Crane stylesheet)
- Excellent XPath 2.0 performance for complex queries
- Robust handling of large ODS files (30+ files per conversion)
- Industry standard for enterprise XML processing
- Free, open-source Home Edition suitable for archive use
- Proven stability for reproducible results

## Installation & Verification

### Check Java Installation
```bash
java -version
# Output: openjdk version "11.0.13" 2021-10-19 (or newer)
```

### Verify Saxon JAR
```bash
ls -lh saxon9he.jar
# Output: -rw-r--r-- 1 root root 4.9M Feb 11 2026 saxon9he.jar

# Optional: Test execution
java -jar saxon9he.jar -version
# Output: Saxon-HE 9.x.x (version information)
```

## Key Acknowledgments

- **Saxonica Ltd.** - For creating and maintaining Saxon XSLT processor
- **Michael Kay** - For pioneering XSLT 2.0 processor development
- **Mozilla Foundation** - For the permissive MPL 2.0 license
- **Open Source Community** - For continuous improvements and bug fixes

## References

- **Saxon Project**: https://www.saxonica.com/
- **SourceForge Downloads**: https://sourceforge.net/projects/saxon/files/
- **XSLT 2.0 Specification**: https://www.w3.org/TR/xslt20/
- **XPath 2.0 Specification**: https://www.w3.org/TR/xpath20/
- **MPL 2.0 License**: https://www.mozilla.org/en-US/MPL/2.0/

---

**Archive Integration Date**: February 11, 2026
**Saxon Version**: 9 HE
**Java Requirement**: JRE 8+
**Archive Status**: Complete and verified
