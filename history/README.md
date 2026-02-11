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

**Direct from OASIS (ODS source files):**
```
history/
├── prd-UBL-2.0/mod/
│   ├── maindoc/                         (29 ODS files)
│   └── lib/                             (3 ODS files: Common, Procurement, Transportation libraries)
│
├── prd2-UBL-2.0/mod/
│   ├── maindoc/                         (31 ODS files - more document types, renamed directory to common)
│   └── common/                          (2 ODS files: CommonLibrary, qDT)
│
├── prd3-UBL-2.0/mod/
│   └── *.ods files                      (30 ODS files - flattened structure, no subdirectories)
│
├── os-UBL-2.0/mod/
│   └── UBL-*.ods files                  (30 ODS source files)
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
├── prd-UBL-2.0/mod/                     (to be generated)
├── prd2-UBL-2.0/mod/                    (to be generated)
├── prd3-UBL-2.0/mod/
│   └── UBL-Entities-2.0.gc
├── cs-UBL-2.0/mod/
│   └── UBL-Entities-2.0.gc
├── os-UBL-2.0/mod/
│   └── UBL-Entities-2.0.gc
└── ... (other generated GC files)
```

**Total**: 35 releases, 63+ GenericCode files (includes newly archived prd and prd2 ODS)

## Quick Links

- **Release History with URLs**: See `/docs/historical-releases.md`
- **UBL 2.0 Synthesis Details**: See `/README.md` > "UBL 2.0 GenericCode Synthesis"
- **Official OASIS Portal**: https://docs.oasis-open.org/ubl/
- **Official UBL Repository**: https://github.com/oasis-tcs/ubl

## Key Notes

- **UBL 2.0 Early Stages** (`history/prd-UBL-2.0/` and `history/prd2-UBL-2.0/`): ODS files downloaded from OASIS PRD and PRD2 releases
  - **PRD directory structure**: `mod/maindoc/` (29 files) + `mod/lib/` (3 files)
  - **PRD2 directory structure**: `mod/maindoc/` (31 files) + `mod/common/` (2 files) - directory naming changed, more document types
  - Shows semantic model evolution across early release stages

- **UBL 2.0 ODS Sources** (`history/os-UBL-2.0/mod/`, `history/prd3-UBL-2.0/mod/`): 30 ODS files from various stages
- **UBL 2.0 GenericCode** (`history/generated/*/mod/`): Synthesized from ODS files using OASIS Crane-ods2obdgc tool
- **UBL 2.1-2.5**: Direct GenericCode files downloaded from OASIS archive (in `history/` root)
- **Complete Coverage**: All intermediate release stages from first public draft (PRD) through latest release
- **Source Traceability**: Every file has documented OASIS source URLs
- **Separation of Generated vs. Downloaded**: Synthesized files kept in `history/generated/` to clearly distinguish from pure OASIS files
- **Semantic Evolution Tracking**: Compare generated GC files across PRD → PRD2 → PRD3 → OS stages to see semantic model evolution

---

## Semantic Model Evolution: PRD → PRD2 → PRD3

### Summary
The UBL 2.0 semantic model evolved significantly through the standardization process:

| Stage | ODS Files | Data Rows | Growth | Key Changes |
|-------|-----------|-----------|--------|------------|
| **PRD** | 32 (29+3) | 1,604 | — | Initial proposal; lib/ structure |
| **PRD2** | 33 (31+2) | 2,139 | +535 (+33%) | Added 2 document types; renamed lib→common |
| **PRD3** | 30 | 2,074 | -65 (-3%) | Removed conflicts; flattened structure |
| **OS** | 30 | 2,074 | — | Stable; no further changes |

### Notable Changes

**PRD → PRD2:**
- Document type growth: 29 → 31 (added Reminder, TransportationStatus)
- Directory rename: `mod/lib/` → `mod/common/`
- Library additions: ProcurementLibrary removed, qDT added
- Significant semantic expansion (+535 rows)

**PRD2 → PRD3:**
- Consolidation phase: 65 rows removed (likely conflicting/redundant definitions)
- Directory restructuring: Subdirectories flattened to single `mod/` directory
- File naming: `-2.` suffix changed to `-2.0.`
- Final stabilization: No further changes through official release

### Conclusion
This evolution demonstrates the normal standardization process: initial proposal → community feedback expansion → expert review refinement → final release with zero changes.

---

For all other documentation and details, see `/README.md`
