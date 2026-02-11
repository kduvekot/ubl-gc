# UBL GenericCode Historical Semantic Models

## Purpose

This directory contains a complete local copy of all UBL (Universal Business Language) GenericCode semantic model files from UBL 2.0 through UBL 2.5 (including all intermediate release stages).

The GenericCode (.gc) files are OASIS standard XML documents that define the semantic model entities and components for each UBL release and stage. These files are essential for tracking the evolution of the UBL semantic model over time.

## Why This Copy Exists

The official OASIS documentation site (https://docs.oasis-open.org/ubl/) is accessed for each query, which can be slow and bandwidth-intensive for large-scale analysis. By maintaining a complete local copy with proper version control through git, we can:

1. **Enable full git blame analysis** - Track exact changes to the semantic model across all versions
2. **Provide offline access** - Work with historical versions without requiring network access
3. **Preserve historical record** - Maintain a permanent snapshot of each release stage
4. **Improve performance** - Avoid repeated downloads from slow external servers

## Directory Structure

Each subdirectory follows the OASIS naming convention and contains:

```
history/
├── {release-stage}-UBL-{version}/
│   └── mod/
│       ├── UBL-Entities-{version}.gc           (Main semantic model)
│       └── UBL-Signature-Entities-{version}.gc (Signature entities model)
```

**Example:**
```
history/
├── prd1-UBL-2.1/mod/
├── prd2-UBL-2.1/mod/
├── ...
├── os-UBL-2.1/mod/
├── csprd01-UBL-2.2/mod/
└── csd02-UBL-2.5/mod/
```

## Complete Release History

### UBL 2.0 (Released: 2006)

| Stage | Directory | Status | File | Notes |
|-------|-----------|--------|------|-------|
| **Official Standard** | **os-UBL-2.0** | ✅ **Complete** | **UBL-Entities-2.0.gc** | **Synthesized from 33 ODS files via Crane-ods2obdgc** |

**Important Note**: UBL 2.0 was originally released as ODS (OpenDocument Spreadsheet) files, not GenericCode format. The GenericCode format was adopted starting with UBL 2.1 (2013).

**UBL-Entities-2.0.gc Details:**
- **File Size**: 3.3 MB
- **Entity Rows**: 2,181
- **Source Files**: 33 ODS files (2 core + 31 document types)
  - UBL-CommonLibrary-2.0.ods
  - UBL-qDT-2.0.ods (Qualified Datatypes)
  - 28 document type ODS files (Invoice, Order, CreditNote, Catalogue, etc.)
- **Conversion Tool**: OASIS Crane-ods2obdgc XSLT stylesheet (official tool)
- **Conversion Date**: February 11, 2026
- **Source**: https://docs.oasis-open.org/ubl/os-UBL-2.0/

**For Complete Details**: See `/history/os-UBL-2.0/README.md` for:
- Complete list of all 33 source ODS files with direct OASIS URLs
- Exact conversion command used
- Reproducibility instructions
- Why os-UBL-2.0 was selected over intermediate versions

---

### UBL 2.1 (Released: 2013)
1. prd1-UBL-2.1 → https://docs.oasis-open.org/ubl/prd1-UBL-2.1/mod/
2. prd2-UBL-2.1 → https://docs.oasis-open.org/ubl/prd2-UBL-2.1/mod/
3. prd3-UBL-2.1 → https://docs.oasis-open.org/ubl/prd3-UBL-2.1/mod/
4. prd4-UBL-2.1 → https://docs.oasis-open.org/ubl/prd4-UBL-2.1/mod/
5. csd4-UBL-2.1 → https://docs.oasis-open.org/ubl/csd4-UBL-2.1/mod/
6. cos1-UBL-2.1 → https://docs.oasis-open.org/ubl/cos1-UBL-2.1/mod/
7. cs1-UBL-2.1 → https://docs.oasis-open.org/ubl/cs1-UBL-2.1/mod/
8. **os-UBL-2.1** (Official Standard) → https://docs.oasis-open.org/ubl/os-UBL-2.1/mod/

### UBL 2.2 (Released: 2018)
1. csprd01-UBL-2.2 → https://docs.oasis-open.org/ubl/csprd01-UBL-2.2/mod/
2. csprd02-UBL-2.2 → https://docs.oasis-open.org/ubl/csprd02-UBL-2.2/mod/
3. csprd03-UBL-2.2 → https://docs.oasis-open.org/ubl/csprd03-UBL-2.2/mod/
4. cos01-UBL-2.2 → https://docs.oasis-open.org/ubl/cos01-UBL-2.2/mod/
5. cs01-UBL-2.2 → https://docs.oasis-open.org/ubl/cs01-UBL-2.2/mod/
6. **os-UBL-2.2** (Official Standard) → https://docs.oasis-open.org/ubl/os-UBL-2.2/mod/

### UBL 2.3 (Released: 2021)
1. csd03-UBL-2.3 → https://docs.oasis-open.org/ubl/csd03-UBL-2.3/mod/
2. csd04-UBL-2.3 → https://docs.oasis-open.org/ubl/csd04-UBL-2.3/mod/
3. csprd01-UBL-2.3 → https://docs.oasis-open.org/ubl/csprd01-UBL-2.3/mod/
4. csprd02-UBL-2.3 → https://docs.oasis-open.org/ubl/csprd02-UBL-2.3/mod/
5. cs01-UBL-2.3 → https://docs.oasis-open.org/ubl/cs01-UBL-2.3/mod/
6. cs02-UBL-2.3 → https://docs.oasis-open.org/ubl/cs02-UBL-2.3/mod/
7. **os-UBL-2.3** (Official Standard) → https://docs.oasis-open.org/ubl/os-UBL-2.3/mod/

### UBL 2.4 (Released: 2024)
1. csd01-UBL-2.4 → https://docs.oasis-open.org/ubl/csd01-UBL-2.4/mod/
2. csd02-UBL-2.4 → https://docs.oasis-open.org/ubl/csd02-UBL-2.4/mod/
3. cs01-UBL-2.4 → https://docs.oasis-open.org/ubl/cs01-UBL-2.4/mod/
4. **os-UBL-2.4** (Official Standard) → https://docs.oasis-open.org/ubl/os-UBL-2.4/mod/

### UBL 2.5 (Current - Released: December 2025)
1. csd01-UBL-2.5 → https://docs.oasis-open.org/ubl/csd01-UBL-2.5/mod/
2. **csd02-UBL-2.5** (Latest) → https://docs.oasis-open.org/ubl/csd02-UBL-2.5/mod/

## File Information

| File Type | Purpose | Size |
|-----------|---------|------|
| UBL-Entities-{version}.gc | Main semantic model with all business information entities (ABIEs) and basic information entities (BBIEs) | ~7-10 MB |
| UBL-Signature-Entities-{version}.gc | Semantic model specifically for digital signature components | ~14 KB |

## GenericCode Format

GenericCode (.gc) files are OASIS-standard XML documents that represent tabular code list and entity data. Each file contains:

- **Metadata section** - Identification, version, agency information
- **Column definitions** - Schema for the semantic model fields
- **Data rows** - Individual entity definitions with their properties

The structure and column definitions remain consistent across versions, allowing for diff analysis and change tracking.

## Using This Historical Archive

### View git blame for semantic model evolution:
```bash
cd /home/user/ubl-gc
git log -p history/os-UBL-2.1/mod/UBL-Entities-2.1.gc
```

### Compare versions:
```bash
diff history/os-UBL-2.1/mod/UBL-Entities-2.1.gc history/os-UBL-2.2/mod/UBL-Entities-2.2.gc
```

### Track a specific entity across versions:
```bash
for version in history/*/mod/UBL-Entities-*.gc; do
  echo "=== $version ==="
  grep -A 5 "EntityName" "$version" | head -20
done
```

## Source Attribution

All files have been downloaded directly from the official OASIS documentation portal:

**Base URL:** https://docs.oasis-open.org/ubl/

Individual release directories follow the pattern:
- https://docs.oasis-open.org/ubl/{release-directory}/mod/UBL-Entities-{version}.gc
- https://docs.oasis-open.org/ubl/{release-directory}/mod/UBL-Signature-Entities-{version}.gc

## Related Documentation

- Full release history with links: See `/docs/historical-releases.md`
- OASIS UBL Technical Committee: https://www.oasis-open.org/committees/tc_home.php?wg_abbrev=ubl
- Official Repository: https://github.com/oasis-tcs/ubl
- GenericCode Specification: https://docs.oasis-open.org/codelist/genericode/v1.0/

## Notes

- **UBL 2.0**: Originally provided as ODS/XLS spreadsheets (not GenericCode format). We have synthesized the GenericCode format from the original os-UBL-2.0 ODS files using the official OASIS Crane-ods2obdgc XSLT stylesheet. This is the complete 33-file consolidation (2 core + 31 document types).
- **UBL 2.1-2.5**: All versions provided directly as GenericCode format from OASIS archive
- **Signature Entities**: Not available for prd1 and prd2 of UBL 2.1 (these files were never published)
- **CSD01/CSD02 for UBL 2.3**: Never publicly released; first public version was CSD03
- **All files**: Maintain consistent XML schema structure as defined by OASIS GenericCode specification
- **Read-Only**: Files are marked read-only to preserve the official record
- **Source Traceability**: Each file has documented OASIS source URLs for complete reproducibility

---

**Last Updated:** February 11, 2026
**Total Releases Archived:** 28 (including UBL 2.0)
**Total GenericCode Files:** 55
  - UBL 2.0: 1 synthesized file (os-UBL-2.0)
  - UBL 2.1-2.5: 54 files (27 releases × 2 file types)
**Total Entity Coverage:** Complete semantic model history from UBL 2.0 (2006) through UBL 2.5 (2025)
