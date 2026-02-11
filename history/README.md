# UBL Semantic Model Historical Archive

This directory contains GenericCode files for all UBL releases from version 2.0 (2006) through 2.5 (2025), including all intermediate release stages.

## Documentation

For complete documentation about this archive, including:
- How UBL 2.0 was synthesized from ODS files
- Source traceability for all 30 ODS files with direct OASIS URLs
- Reproducibility instructions
- Git usage examples
- Version coverage and file organization

**See the main README: [`/README.md`](../README.md)**

## Directory Structure

Each release is organized following the official OASIS naming convention:

**Direct from OASIS (ODS source files and GenericCode files):**
```
history/
├── os-UBL-2.0/mod/
│   └── UBL-*.ods files                  (30 ODS source files from OASIS)
│
├── prd1-UBL-2.1/mod/
├── prd2-UBL-2.1/mod/
├── ... (other UBL 2.1 stages)
├── os-UBL-2.1/mod/
│
├── csprd01-UBL-2.2/mod/
├── ... (other UBL 2.2-2.5 stages)
│
└── csd02-UBL-2.5/mod/
    ├── UBL-Entities-2.5.gc
    └── UBL-Signature-Entities-2.5.gc
```

**Generated/Synthesized files (separated):**
```
history/generated/
├── os-UBL-2.0/mod/
│   └── UBL-Entities-2.0.gc              (synthesized from 30 ODS files)
```

**Total**: 28 releases, 55 GenericCode files

## Quick Links

- **Release History with URLs**: See `/docs/historical-releases.md`
- **UBL 2.0 Synthesis Details**: See `/README.md` > "UBL 2.0 GenericCode Synthesis"
- **Official OASIS Portal**: https://docs.oasis-open.org/ubl/
- **Official UBL Repository**: https://github.com/oasis-tcs/ubl

## Key Notes

- **UBL 2.0 ODS Sources** (`history/os-UBL-2.0/mod/`): 30 ODS files downloaded directly from OASIS os-UBL-2.0
- **UBL 2.0 GenericCode** (`history/generated/os-UBL-2.0/mod/`): Synthesized from ODS files using OASIS Crane-ods2obdgc tool
- **UBL 2.1-2.5**: Direct GenericCode files downloaded from OASIS archive (in `history/` root)
- **Complete Coverage**: All intermediate release stages for historical tracking
- **Source Traceability**: Every file has documented OASIS source URLs
- **Separation of Generated vs. Downloaded**: Synthesized files kept in `history/generated/` to clearly distinguish from pure OASIS files

---

For all other documentation and details, see `/README.md`
