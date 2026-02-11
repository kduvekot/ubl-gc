# UBL GenericCode Historical Semantic Models

## Purpose

This directory contains a complete local copy of all UBL (Universal Business Language) GenericCode semantic model files from UBL 2.1 through UBL 2.5 (including all intermediate release stages).

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

- UBL 2.0 did not provide GenericCode files (used ODS/XLS spreadsheets instead)
- CSD01 and CSD02 for UBL 2.3 were never publicly released; first public version was CSD03
- All files maintain consistent XML schema structure as defined by OASIS
- Files are read-only to preserve the official record

---

**Last Updated:** February 11, 2026
**Total Releases Archived:** 27
**Total GenericCode Files:** 54 (27 releases × 2 file types)
