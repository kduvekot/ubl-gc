#!/usr/bin/env python3
"""
GenericCode Commit Builder

Builds a GenericCode file incrementally with one git commit per step.
Creates an ultra-granular git history showing element-by-element evolution.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import subprocess
import sys
import os
from pathlib import Path

from gc_analyzer import GCAnalyzer
from gc_builder import GCBuilder, BuildStep


class GCCommitBuilder:
    """Creates git commits for each incremental build step"""

    def __init__(self, source_gc_file: str, target_file: str, repo_path: str):
        self.source_gc_file = source_gc_file
        self.target_file = target_file
        self.repo_path = repo_path
        self.target_path = Path(repo_path) / target_file

    def create_empty_gc_file(self) -> None:
        """Create an empty GenericCode file with header and column definitions"""
        # Parse source to get structure
        tree = ET.parse(self.source_gc_file)
        root = tree.getroot()

        # Create new document with same namespace
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
        simple_code_list = ET.SubElement(new_root, 'SimpleCodeList')

        # Write to file
        self._write_xml(new_root, "Create empty GenericCode file with header and columns")

    def _write_xml(self, root: ET.Element, commit_message: str) -> None:
        """Write XML to file and create git commit"""
        # Ensure directory exists
        self.target_path.parent.mkdir(parents=True, exist_ok=True)

        # Pretty print XML
        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent='   ')

        # Remove extra blank lines
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        pretty_xml = '\n'.join(lines) + '\n'

        # Write to file
        with open(self.target_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)

    def _git_add_and_commit(self, message: str) -> None:
        """Add file and create git commit"""
        subprocess.run(['git', 'add', self.target_file], cwd=self.repo_path, check=True)

        full_message = f"{message}\n\nhttps://claude.ai/code/session_01J8Cq8ZxE5GAVoSg2e5LFvK"

        subprocess.run(
            ['git', 'commit', '-m', full_message],
            cwd=self.repo_path,
            check=True
        )

    def add_rows(self, rows, commit_message: str) -> None:
        """Add rows to the SimpleCodeList and commit"""
        # Parse current file
        tree = ET.parse(self.target_path)
        root = tree.getroot()

        # Find SimpleCodeList
        simple_code_list = root.find('SimpleCodeList')
        if simple_code_list is None:
            simple_code_list = ET.SubElement(root, 'SimpleCodeList')

        # Add new rows
        for row in rows:
            simple_code_list.append(row.xml_data)

        # Write and commit
        self._write_xml(root, commit_message)
        self._git_add_and_commit(commit_message)

    def build_incremental(self, steps: list[BuildStep]) -> None:
        """Execute all build steps, creating one commit per step"""
        print(f"\nBuilding {len(steps)} incremental commits...")
        print("="*70)

        for i, step in enumerate(steps, 1):
            # Create commit message
            phase_prefix = {
                'leaf': '🌱',
                'abie+bbie': '🏗️',
                'asbie': '🔗'
            }.get(step.phase, '📝')

            commit_msg = f"{phase_prefix} Step {step.step_num}/{len(steps)}: {step.description}"

            # Add rows and commit
            self.add_rows(step.rows_to_add, commit_msg)

            # Progress indicator
            if i % 10 == 0:
                print(f"  ✓ Completed {i}/{len(steps)} steps")

        print(f"\n✓ All {len(steps)} commits created!")


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
    print("\n" + "="*70)
    print("ANALYZING SOURCE FILE")
    print("="*70)

    analyzer = GCAnalyzer(source_file)
    analyzer.parse()
    analyzer.build_abies()
    analyzer.build_dependency_graph()

    # Plan build
    print("\n" + "="*70)
    print("PLANNING BUILD")
    print("="*70)

    builder = GCBuilder(analyzer)
    steps = builder.plan_build()

    print(builder.generate_build_plan_summary())

    # Create commits
    print("\n" + "="*70)
    print("CREATING COMMITS")
    print("="*70)

    commit_builder = GCCommitBuilder(source_file, target_file, repo_path)

    # Create initial empty file
    print("\nCreating initial empty GenericCode file...")
    commit_builder.create_empty_gc_file()
    commit_builder._git_add_and_commit("📋 Initialize empty GenericCode file structure")

    # Build incrementally
    commit_builder.build_incremental(steps)

    print("\n" + "="*70)
    print("✓ BUILD COMPLETE")
    print("="*70)
    print("\nView commit history with:")
    print(f"  git log --oneline --graph")


if __name__ == '__main__':
    main()
