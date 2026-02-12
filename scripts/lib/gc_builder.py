#!/usr/bin/env python3
"""
GenericCode File Builder

Builds a GenericCode file incrementally with one commit per ABIE group,
ensuring the file is valid at every step with no forward references.

Strategy:
- Topologically sort ABIEs using Tarjan's SCC algorithm
- One commit per ABIE group (ABIE + all its BBIEs + all its ASBIEs)
- Cycle groups (mutually dependent ABIEs) are committed together
- Self-referencing ABIEs are fine as single commits
"""

from typing import List
from dataclasses import dataclass
import sys
import os

from gc_analyzer import GCAnalyzer, ABIE, Row


@dataclass
class BuildStep:
    """Represents a single incremental build step (one git commit)"""
    step_num: int
    description: str
    rows_to_add: List[Row]
    abie_names: List[str]  # Object class names in this step
    is_cycle: bool  # Whether this is a multi-ABIE cycle group
    bbie_count: int
    asbie_count: int


class GCBuilder:
    """Incrementally builds a GenericCode file with valid ABIE-level commits"""

    def __init__(self, analyzer: GCAnalyzer):
        self.analyzer = analyzer
        self.build_steps: List[BuildStep] = []

    def plan_build(self) -> List[BuildStep]:
        """
        Plan all build steps using topological SCC ordering.
        One step per SCC group (usually one ABIE, sometimes a cycle group).
        Each step includes ABIE + all BBIEs + all ASBIEs.
        """
        commit_order = self.analyzer.get_abie_commit_order()
        steps = []

        print(f"\nPlanning {len(commit_order)} ABIE-level commits...")
        print("=" * 70)

        for step_num, abies in enumerate(commit_order, 1):
            # Collect all rows for this group
            rows = []
            abie_names = []
            total_bbies = 0
            total_asbies = 0

            for abie in abies:
                rows.append(abie.row)
                rows.extend(abie.bbies)
                rows.extend(abie.asbies)
                abie_names.append(abie.object_class)
                total_bbies += len(abie.bbies)
                total_asbies += len(abie.asbies)

            is_cycle = len(abies) > 1

            # Build description
            if is_cycle:
                desc = f"Add cycle group: {' + '.join(abie_names)}"
            else:
                desc = f'Add "{abie_names[0]}"'

            step = BuildStep(
                step_num=step_num,
                description=desc,
                rows_to_add=rows,
                abie_names=abie_names,
                is_cycle=is_cycle,
                bbie_count=total_bbies,
                asbie_count=total_asbies,
            )
            steps.append(step)

            # Print progress
            abie_count = len(abies)
            total_rows = len(rows)
            cycle_tag = " [CYCLE]" if is_cycle else ""
            print(f"  {step_num:3d}. {desc}{cycle_tag}"
                  f" ({abie_count} ABIE, {total_bbies} BBIEs,"
                  f" {total_asbies} ASBIEs = {total_rows} rows)")

        self.build_steps = steps
        return steps

    def generate_build_plan_summary(self) -> str:
        """Generate a summary of the build plan"""
        if not self.build_steps:
            self.plan_build()

        steps = self.build_steps
        total_rows = sum(len(s.rows_to_add) for s in steps)
        cycle_steps = sum(1 for s in steps if s.is_cycle)
        single_steps = len(steps) - cycle_steps

        total_abies = sum(len(s.abie_names) for s in steps)
        total_bbies = sum(s.bbie_count for s in steps)
        total_asbies = sum(s.asbie_count for s in steps)

        summary = f"""
BUILD PLAN SUMMARY
{'=' * 70}
Total commits:     {len(steps)} (+ 1 skeleton = {len(steps) + 1} total)
Total rows:        {total_rows}
  ABIEs:           {total_abies}
  BBIEs:           {total_bbies}
  ASBIEs:          {total_asbies}

Single-ABIE commits:  {single_steps}
Cycle-group commits:  {cycle_steps}

Every intermediate state is a valid GenericCode file.
No forward references at any commit.
{'=' * 70}
"""
        return summary


def main():
    if len(sys.argv) < 2:
        print("Usage: gc_builder.py <path-to-gc-file>")
        sys.exit(1)

    gc_file = sys.argv[1]
    print(f"Planning build for: {gc_file}\n")

    # Analyze the file
    analyzer = GCAnalyzer(gc_file)
    analyzer.parse()
    analyzer.build_abies()
    analyzer.build_dependency_graph()
    analyzer.find_sccs_tarjan()
    analyzer.topological_sort_sccs()

    # Plan the build
    builder = GCBuilder(analyzer)
    steps = builder.plan_build()

    # Print summary
    print(builder.generate_build_plan_summary())


if __name__ == '__main__':
    main()
