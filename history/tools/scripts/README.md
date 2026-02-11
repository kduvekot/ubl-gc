# Conversion Scripts

Scripts that orchestrate the UBL ODS to GenericCode conversion process.

## Scripts

### ubl20-ods-to-gc-convert.sh

Converts 30 UBL 2.0 ODS files to a single unified GenericCode file.

**Usage:**
```bash
./ubl20-ods-to-gc-convert.sh [output_directory] [input_directory]
```

**Parameters:**
- `output_directory` (optional): Where to write the GenericCode file. Default: current directory
- `input_directory` (optional): Directory containing ODS files. Default: current directory

**Example:**
```bash
cd /home/user/ubl-gc/history/os-UBL-2.0/mod

# Download ODS files first
for doc in Invoice Order CreditNote Quotation ApplicationResponse ...; do
  curl -A "Mozilla/5.0" -O "https://docs.oasis-open.org/ubl/os-UBL-2.0/mod/maindoc/UBL-$doc-2.0.ods"
done

# Run conversion
bash ../../tools/scripts/ubl20-ods-to-gc-convert.sh . .
```

**What it does:**
1. Validates tools (Saxon, Crane-ods2obdgc) are available
2. Copies ODS files to temporary directory
3. Creates identification file with metadata
4. Executes Saxon XSLT transformation
5. Validates output XML structure
6. Reports file statistics (size, row count)

**Requirements:**
- Java (for Saxon)
- xmllint (for validation)
- Bash shell

**Output:**
Creates `UBL-Entities-2.0.gc` file with:
- 3.3 MB file size (approximately)
- 88,492 lines of XML
- 2,181 data rows (entities)
- Proper GenericCode XML structure

## Integration

These scripts are part of the reproducible conversion toolchain:
1. **Input**: 30 ODS files from OASIS (in `history/os-UBL-2.0/mod/`)
2. **Tools**: Crane-ods2obdgc XSLT + Saxon9HE processor
3. **Output**: Synthesized GenericCode (in `history/generated/os-UBL-2.0/mod/`)

## Customization

To use these scripts for other conversions:

1. Modify the ODS file list if different document types are needed
2. Update the identification file with appropriate metadata
3. Adjust the `included-sheet-name-regex` pattern if needed
4. Ensure Saxon is called with `-it:ods-uri` for Crane-ods2obdgc

## Auditability

These scripts are stored alongside the tools to ensure:
- Full transparency of the conversion process
- Anyone can reproduce the conversion
- Exact commands used are documented and preserved
- No manual steps or undocumented modifications

For complete audit trail, see:
- `/README.md` - Full project documentation
- `history/generated/os-UBL-2.0/mod/` - Output file
- `history/os-UBL-2.0/mod/` - Input ODS files
