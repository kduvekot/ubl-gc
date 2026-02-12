#!/usr/bin/env python3
"""
GenericCode Commit Builder

Builds a GenericCode file incrementally with one git commit per ABIE group.
Creates a git history showing the semantic model being assembled
in dependency order.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import subprocess
import sys
import os
from pathlib import Path

from gc_analyzer import GCAnalyzer
from gc_builder import GCBuilder, BuildStep

SESSION_URL = "https://claude.ai/code/session_01B5kfoVeuncQaSCz9nX4H1j"


class GCCommitBuilder:
    """Creates git commits for each ABIE-level build step"""

    def __init__(self, source_gc_file: str, target_file: str, repo_path: str):
        self.source_gc_file = source_gc_file
        self.target_file = target_file
        self.repo_path = repo_path
        self.target_path = Path(repo_path) / target_file

    def create_empty_gc_file(self) -> None:
        """Create an empty GenericCode file with header and column definitions"""
        tree = ET.parse(self.source_gc_file)
        root = tree.getroot()

        new_root = ET.Element(root.tag, root.attrib)

        # Copy Identification
        identification = root.find('Identification')
        if identification is not None:
            new_root.append(identification)

        # Copy ColumnSet
        column_set = root.find('ColumnSet')
        if column_set is not None:
            new_root.append(column_set)

        # Add empty SimpleCodeList
        ET.SubElement(new_root, 'SimpleCodeList')

        self._write_xml(new_root)

    def _write_xml(self, root: ET.Element) -> None:
        """Write XML to file with consistent 3-space indentation"""
        self.target_path.parent.mkdir(parents=True, exist_ok=True)

        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent='   ')

        # Remove extra blank lines and the xml declaration added by minidom
        lines = pretty_xml.split('\n')
        cleaned = []
        for line in lines:
            # Skip minidom's xml declaration (we'll add our own)
            if line.startswith('<?xml'):
                continue
            if line.strip():
                cleaned.append(line)

        # Reassemble with proper declaration
        pretty_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + '\n'.join(cleaned) + '\n'

        with open(self.target_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)

    def _git_add_and_commit(self, message: str) -> None:
        """Add file and create git commit"""
        subprocess.run(
            ['git', 'add', self.target_file],
            cwd=self.repo_path, check=True
        )

        full_message = f"{message}\n\n{SESSION_URL}"

        subprocess.run(
            ['git', 'commit', '-m', full_message],
            cwd=self.repo_path, check=True
        )

    def add_rows(self, rows, commit_message: str) -> None:
        """Add rows to the SimpleCodeList and commit"""
        tree = ET.parse(self.target_path)
        root = tree.getroot()

        simple_code_list = root.find('SimpleCodeList')
        if simple_code_list is None:
            simple_code_list = ET.SubElement(root, 'SimpleCodeList')

        for row in rows:
            simple_code_list.append(row.xml_data)

        self._write_xml(root)
        self._git_add_and_commit(commit_message)

    def build_incremental(self, steps: list[BuildStep]) -> None:
        """Execute all build steps, creating one commit per ABIE group"""
        total = len(steps)
        print(f"\nBuilding {total} ABIE-level commits...")
        print("=" * 70)

        for i, step in enumerate(steps, 1):
            # Build commit message
            abie_count = len(step.abie_names)
            row_count = len(step.rows_to_add)

            if step.is_cycle:
                subject = (f"UBL 2.0 PRD [{step.step_num}/{total}]: "
                           f"Add cycle group: {' + '.join(step.abie_names)}")
                body_lines = [
                    f"Cycle group of {abie_count} mutually dependent ABIEs.",
                    f"These ABIEs reference each other and must be added together.",
                    "",
                ]
                for name in step.abie_names:
                    abie = self.analyzer_abies[name]
                    body_lines.append(
                        f"  {name}: {len(abie.bbies)} BBIEs, {len(abie.asbies)} ASBIEs"
                    )
            else:
                name = step.abie_names[0]
                subject = (f"UBL 2.0 PRD [{step.step_num}/{total}]: "
                           f'Add "{name}"')
                body_lines = [
                    f"ABIE: {name}",
                    f"Components: {step.bbie_count} BBIEs, {step.asbie_count} ASBIEs",
                    f"Total rows: {row_count}",
                ]

            commit_msg = subject + "\n\n" + "\n".join(body_lines)

            self.add_rows(step.rows_to_add, commit_msg)

            if i % 20 == 0 or i == total:
                print(f"  Completed {i}/{total} commits")

        print(f"\nAll {total} ABIE-level commits created!")


def main():
    if len(sys.argv) < 4:
        print("Usage: gc_commit_builder.py <source-gc-file> <target-file> <repo-path>")
        print("\nExample:")
        print("  gc_commit_builder.py \\")
        print("    history/generated/prd-UBL-2.0/mod/UBL-Entities-2.0.gc \\")
        print("    UBL-Entities.gc \\")
        print("    .")
        sys.exit(1)

    source_file = sys.argv[1]
    target_file = sys.argv[2]
    repo_path = sys.argv[3]

    print(f"Source: {source_file}")
    print(f"Target: {target_file}")
    print(f"Repo:   {repo_path}")

    # Analyze source file
    print("\n" + "=" * 70)
    print("ANALYZING SOURCE FILE")
    print("=" * 70)

    analyzer = GCAnalyzer(source_file)
    analyzer.parse()
    analyzer.build_abies()
    analyzer.build_dependency_graph()
    analyzer.find_sccs_tarjan()
    analyzer.topological_sort_sccs()

    # Plan build
    print("\n" + "=" * 70)
    print("PLANNING BUILD")
    print("=" * 70)

    builder = GCBuilder(analyzer)
    steps = builder.plan_build()

    print(builder.generate_build_plan_summary())

    # Create commits
    print("\n" + "=" * 70)
    print("CREATING COMMITS")
    print("=" * 70)

    commit_builder = GCCommitBuilder(source_file, target_file, repo_path)
    # Store analyzer reference for commit message generation
    commit_builder.analyzer_abies = analyzer.abies

    # Create initial empty file
    print("\nCreating initial empty GenericCode file...")
    commit_builder.create_empty_gc_file()
    commit_builder._git_add_and_commit(
        "UBL 2.0 PRD: Initialize GenericCode file structure\n\n"
        "Empty file with header, column definitions, and empty SimpleCodeList.\n"
        "Columns: ModelName, UBLName, DictionaryEntryName, ObjectClass,\n"
        "PropertyTerm, RepresentationTerm, DataType, AssociatedObjectClass,\n"
        "Cardinality, ComponentType, Definition, and more.\n\n"
        f"Source: UBL 2.0 Proposed Recommendation Draft (2006)"
    )

    # Build incrementally
    commit_builder.build_incremental(steps)

    print("\n" + "=" * 70)
    print("BUILD COMPLETE")
    print("=" * 70)
    print(f"\n{len(steps) + 1} commits created (1 skeleton + {len(steps)} ABIE groups)")
    print("\nView commit history with:")
    print("  git log --oneline --graph")


if __name__ == '__main__':
    main()
