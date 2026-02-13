#!/usr/bin/env python3
"""
GenericCode Commit Builder

Builds a GenericCode file incrementally with one git commit per ABIE group.
Creates a git history showing the semantic model being assembled
in dependency order.

Instead of DOM manipulation, works directly with the source file's text lines.
This preserves exact formatting, XML comments, namespace prefixes, and row order.
The final commit produces a file byte-identical to the original source.
"""

import xml.etree.ElementTree as ET
import subprocess
import sys
import os
import re
from pathlib import Path

from gc_analyzer import GCAnalyzer
from gc_builder import GCBuilder, BuildStep

class GCCommitBuilder:
    """Creates git commits by inserting raw text blocks from the source file"""

    def __init__(self, source_gc_file: str, target_file: str, repo_path: str):
        self.source_gc_file = source_gc_file
        self.target_file = target_file
        self.repo_path = repo_path
        self.target_path = Path(repo_path) / target_file

        # Parse the source file into header, row blocks, and footer
        self.header_lines = []    # Everything before first <Row>
        self.footer_lines = []    # Everything after last </Row>
        self.row_blocks = {}      # row_num -> list of text lines for that row

        self._parse_source_text()

    def _parse_source_text(self) -> None:
        """Parse source file into text blocks: header, per-row blocks, footer"""
        with open(self.source_gc_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()

        # Find all <Row> and </Row> boundaries
        row_starts = []  # (line_index, row_num)
        row_ends = []    # line_index of </Row>

        row_counter = 0
        for i, line in enumerate(all_lines):
            stripped = line.strip()
            if stripped.startswith('<Row>') or stripped.startswith('<Row '):
                row_counter += 1
                row_starts.append((i, row_counter))
            elif stripped == '</Row>':
                row_ends.append(i)

        if not row_starts:
            raise ValueError(f"No <Row> elements found in {self.source_gc_file}")

        # Header: everything before first <Row>
        first_row_line = row_starts[0][0]
        self.header_lines = all_lines[:first_row_line]

        # Footer: everything after last </Row>
        last_row_end = row_ends[-1]
        self.footer_lines = all_lines[last_row_end + 1:]

        # Extract each row block (including the <Row><!--N--> and </Row> lines)
        for idx, (start_line, row_num) in enumerate(row_starts):
            end_line = row_ends[idx]
            block = all_lines[start_line:end_line + 1]
            self.row_blocks[row_num] = block

        print(f"Parsed source: {len(self.header_lines)} header lines, "
              f"{len(self.row_blocks)} row blocks, "
              f"{len(self.footer_lines)} footer lines")

    def _write_file(self, row_nums: list[int]) -> None:
        """Write the GC file with header + selected rows (in order) + footer"""
        self.target_path.parent.mkdir(parents=True, exist_ok=True)

        # Sort row_nums to maintain original file order
        sorted_nums = sorted(row_nums)

        with open(self.target_path, 'w', encoding='utf-8') as f:
            # Header
            for line in self.header_lines:
                f.write(line)

            # Row blocks in original order
            for num in sorted_nums:
                for line in self.row_blocks[num]:
                    f.write(line)

            # Footer
            for line in self.footer_lines:
                f.write(line)

    def _git_add_and_commit(self, message: str) -> None:
        """Add file and create git commit"""
        subprocess.run(
            ['git', 'add', self.target_file],
            cwd=self.repo_path, check=True
        )

        subprocess.run(
            ['git', 'commit', '-m', message],
            cwd=self.repo_path, check=True
        )

    def create_empty_gc_file(self) -> None:
        """Create the GC file with header and empty SimpleCodeList (no rows)"""
        self._write_file([])

    def add_rows(self, row_nums: list[int], all_row_nums: list[int],
                 commit_message: str) -> None:
        """Write the file with all accumulated rows and commit"""
        self._write_file(all_row_nums)
        self._git_add_and_commit(commit_message)

    def build_incremental(self, steps: list[BuildStep],
                          release_prefix: str, release_label: str,
                          release_date: str) -> None:
        """Execute all build steps, creating one commit per ABIE group.

        Args:
            steps: Build steps from GCBuilder.plan_build()
            release_prefix: e.g. "UBL 2.0 PRD" or "UBL 2.5 CSD01"
            release_label: e.g. "prd-UBL-2.0" or "csd01-UBL-2.5"
            release_date: e.g. "2006-01-19"
        """
        total = len(steps)
        print(f"\nBuilding {total} ABIE-level commits...")
        print("=" * 70)

        # Track all row_nums added so far
        accumulated_rows = []

        for i, step in enumerate(steps, 1):
            # Collect row_nums for this step
            new_row_nums = [row.row_num for row in step.rows_to_add]
            accumulated_rows.extend(new_row_nums)

            # Build commit message
            abie_count = len(step.abie_names)
            row_count = len(step.rows_to_add)

            if step.is_cycle:
                subject = (f"{release_prefix}: "
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
                subject = (f"{release_prefix}: "
                           f'Add "{name}"')
                body_lines = [
                    f"ABIE: {name}",
                    f"Components: {step.bbie_count} BBIEs, {step.asbie_count} ASBIEs",
                    f"Total rows: {row_count}",
                ]

            body_lines.extend(["", f"Release: {release_label}",
                               f"File: {self.target_file}",
                               f"Date: {release_date}"])
            commit_msg = subject + "\n\n" + "\n".join(body_lines)

            self.add_rows(new_row_nums, accumulated_rows, commit_msg)

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
        "Source: UBL 2.0 Proposed Recommendation Draft (2006)"
    )

    # Build incrementally
    commit_builder.build_incremental(
        steps, "UBL 2.0 PRD", "prd-UBL-2.0", "2006-01-19")

    print("\n" + "=" * 70)
    print("BUILD COMPLETE")
    print("=" * 70)
    print(f"\n{len(steps) + 1} commits created (1 skeleton + {len(steps)} ABIE groups)")
    print("\nView commit history with:")
    print("  git log --oneline --graph")


if __name__ == '__main__':
    main()
