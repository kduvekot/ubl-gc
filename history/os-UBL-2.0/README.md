# UBL 2.0 GenericCode Conversion

## Overview

This directory contains **UBL-Entities-2.0.gc**, a **synthesized GenericCode file** created by reverse-engineering the official UBL 2.0 ODS (OpenDocument Spreadsheet) semantic model files into the GenericCode format.

## Why Synthesized?

The official OASIS UBL 2.0 release (2006) used **ODS spreadsheets** as the primary semantic model format:
- `UBL-CommonLibrary-2.0.ods`
- `UBL-qDT-2.0.ods` (Qualified Datatypes)

GenericCode format was not adopted until **UBL 2.1** (2013).

This file enables **complete git history tracking from UBL 2.0 through 2.5** by converting the original semantic model data into the GenericCode format used by all subsequent versions.

## Conversion Process

### Tools Used
- **OASIS Crane-ods2obdgc** - Official XSLT stylesheet for ODS to GenericCode conversion
  - Located in: https://github.com/oasis-tcs/ubl/tree/review/utilities/Crane-ods2obdgc
  - Version: From OASIS UBL official repository

- **Saxon 9 HE** - XSLT 2.0 processor
  - Required for XSLT transformation

### Conversion Method

```bash
java -jar saxon9he.jar \
  -xsl:Crane-ods2obdgc.xsl \
  -o:UBL-Entities-2.0.gc \
  -it:ods-uri \
  ods-uri=UBL-CommonLibrary-2.0.ods,UBL-qDT-2.0.ods \
  identification-uri=ident-UBL-2.0.xml
```

### Source Data
- **UBL-CommonLibrary-2.0.ods** - Core component entities, common types
- **UBL-qDT-2.0.ods** - Qualified datatype definitions

Both downloaded from official OASIS archive:
https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/

## File Statistics

| Metric | Value |
|--------|-------|
| File size | 1.8 MB |
| Total rows | 1,274 |
| Total columns | 33 |
| Models | 2 (Common Library + Qualified Datatypes) |
| Valid XML | ✅ Yes |

## Schema Compatibility

**Column Structure (identical to UBL 2.1):**
- ModelName
- UBLName
- DictionaryEntryName
- ObjectClassQualifier
- ObjectClass
- PropertyTermQualifier
- PropertyTermPossessiveNoun
- PropertyTermPrimaryNoun
- PropertyTerm
- RepresentationTerm
- DataTypeQualifier
- DataType
- AssociatedObjectClassQualifier
- AssociatedObjectClass
- AlternativeBusinessTerms
- Cardinality
- ComponentType
- Definition
- Examples
- UNTDEDCode
- ... (and others)

## Validation

✅ **All checks passed:**
- Valid XML 1.0 declaration and structure
- 1,274 opening `<Row>` tags = 1,274 closing `</Row>` tags (balanced)
- Proper opening and closing of `<gc:CodeList>`
- 33 column definitions with proper structure

## Notes

1. **No Signature Entities**: UBL 2.0 did not have a separate signature entities file. All entities are included in the main model.

2. **Data Integrity**: The conversion uses the official OASIS Crane-ods2obdgc XSLT stylesheet, the same tool used by the official OASIS UBL repository for current versions.

3. **Historical Record**: This synthesized file preserves the semantic structure of UBL 2.0 in a machine-readable format compatible with modern version control systems.

4. **Limitations**:
   - This is a **reconstructed** format, not the original published format
   - Minor formatting differences from manually-created GenericCode may exist
   - For official UBL 2.0 semantics, refer to the original ODS files

## Git Integration

This file enables:
- ✅ Full git blame tracking across UBL 2.0 → 2.5
- ✅ Diff analysis between UBL 2.0 and 2.1
- ✅ Historical entity tracking from first release
- ✅ Version control of semantic model evolution

## References

- **OASIS UBL 2.0 Archive**: https://docs.oasis-open.org/ubl/os-UBL-2.0/
- **Official Repository**: https://github.com/oasis-tcs/ubl
- **Crane-ods2obdgc Tool**: https://cranesoftwrights.github.io/resources/ubl/
- **GenericCode Specification**: https://docs.oasis-open.org/codelist/genericode/v1.0/

---

**Generated**: February 11, 2026
**Tool**: Crane-ods2obdgc XSLT stylesheet (official OASIS tool)
**Method**: Reverse engineering ODS source files to GenericCode format
