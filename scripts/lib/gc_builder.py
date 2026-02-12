#!/usr/bin/env python3
"""
GenericCode File Builder

Builds a GenericCode file incrementally, element by element,
ensuring the file is valid at every step with no forward references.

Strategy:
1. Phase 1: Add leaf ABIEs (no dependencies) completely
2. Phase 2: Add remaining ABIEs + BBIEs (creates all types)
3. Phase 3: Add ASBIEs for remaining ABIEs (all refs now valid)
"""

import xml.etree.ElementTree as ET
from typing import List, Set, Dict
from dataclasses import dataclass
import sys
import os

from gc_analyzer import GCAnalyzer, ABIE, Row


@dataclass
class BuildStep:
    """Represents a single incremental build step (commit)"""
    step_num: int
    description: str
    rows_to_add: List[Row]
    phase: str  # 'leaf', 'abie+bbie', 'asbie'


class GCBuilder:
    """Incrementally builds a GenericCode file with valid commits"""

    def __init__(self, analyzer: GCAnalyzer):
        self.analyzer = analyzer
        self.build_steps: List[BuildStep] = []

    def identify_leaf_abies(self) -> List[ABIE]:
        """
        Find ABIEs with no external ASBIE dependencies.
        These can be added completely in Phase 1.
        """
        leaf_abies = []

        for abie in self.analyzer.abies.values():
            # Check if it has any external dependencies
            external_deps = [dep for dep in abie.depends_on if dep != abie.object_class]

            if not external_deps:
                leaf_abies.append(abie)

        # Sort by original order (row number)
        leaf_abies.sort(key=lambda a: a.row.row_num)
        return leaf_abies

    def identify_non_leaf_abies(self) -> List[ABIE]:
        """
        Find ABIEs with external dependencies.
        These are added in Phases 2 and 3.
        """
        leaf_names = {abie.object_class for abie in self.identify_leaf_abies()}

        non_leaf_abies = [
            abie for abie in self.analyzer.abies.values()
            if abie.object_class not in leaf_names
        ]

        # Sort by original order
        non_leaf_abies.sort(key=lambda a: a.row.row_num)
        return non_leaf_abies

    def plan_build(self) -> List[BuildStep]:
        """
        Plan all build steps in correct order.
        Returns list of BuildSteps.
        """
        steps = []
        step_num = 1

        # Phase 1: Leaf ABIEs (complete)
        print("\n" + "="*70)
        print("PHASE 1: Leaf ABIEs (no dependencies)")
        print("="*70)

        leaf_abies = self.identify_leaf_abies()
        print(f"Found {len(leaf_abies)} leaf ABIEs\n")

        for abie in leaf_abies:
            # Add ABIE + all BBIEs + all ASBIEs in one step
            rows = [abie.row] + abie.bbies + abie.asbies

            steps.append(BuildStep(
                step_num=step_num,
                description=f"Add leaf ABIE: {abie.name}",
                rows_to_add=rows,
                phase='leaf'
            ))

            print(f"  {step_num}. {abie.name} ({len(abie.bbies)} BBIEs, {len(abie.asbies)} ASBIEs)")
            step_num += 1

        # Phase 2: Non-leaf ABIEs + BBIEs only
        print("\n" + "="*70)
        print("PHASE 2: Non-leaf ABIEs + BBIEs (defer ASBIEs)")
        print("="*70)

        non_leaf_abies = self.identify_non_leaf_abies()
        print(f"Found {len(non_leaf_abies)} non-leaf ABIEs\n")

        for abie in non_leaf_abies:
            # Add ABIE + BBIEs only (no ASBIEs yet)
            rows = [abie.row] + abie.bbies

            steps.append(BuildStep(
                step_num=step_num,
                description=f"Add ABIE+BBIEs: {abie.name}",
                rows_to_add=rows,
                phase='abie+bbie'
            ))

            deps_str = ', '.join(sorted(abie.depends_on)[:3])
            if len(abie.depends_on) > 3:
                deps_str += f", +{len(abie.depends_on)-3} more"

            print(f"  {step_num}. {abie.name} ({len(abie.bbies)} BBIEs, {len(abie.asbies)} ASBIEs deferred)")
            print(f"       Depends on: {deps_str}")
            step_num += 1

        # Phase 3: ASBIEs for non-leaf ABIEs
        print("\n" + "="*70)
        print("PHASE 3: ASBIEs for non-leaf ABIEs (all types now exist)")
        print("="*70)
        print(f"Adding ASBIEs for {len(non_leaf_abies)} ABIEs\n")

        for abie in non_leaf_abies:
            if abie.asbies:  # Only if there are ASBIEs
                steps.append(BuildStep(
                    step_num=step_num,
                    description=f"Add ASBIEs: {abie.name}",
                    rows_to_add=abie.asbies,
                    phase='asbie'
                ))

                print(f"  {step_num}. {abie.name} ({len(abie.asbies)} ASBIEs)")
                step_num += 1

        return steps

    def generate_build_plan_summary(self) -> str:
        """Generate a summary of the build plan"""
        steps = self.plan_build()

        phase1_count = sum(1 for s in steps if s.phase == 'leaf')
        phase2_count = sum(1 for s in steps if s.phase == 'abie+bbie')
        phase3_count = sum(1 for s in steps if s.phase == 'asbie')

        total_rows = sum(len(s.rows_to_add) for s in steps)

        summary = f"""
BUILD PLAN SUMMARY
{'='*70}
Total steps: {len(steps)}
Total rows to add: {total_rows}

Phase 1 (Leaf ABIEs):           {phase1_count:4d} steps
Phase 2 (Non-leaf ABIE+BBIEs):  {phase2_count:4d} steps
Phase 3 (Non-leaf ASBIEs):      {phase3_count:4d} steps

File will be valid at every step!
{'='*70}
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

    # Plan the build
    builder = GCBuilder(analyzer)
    steps = builder.plan_build()

    # Print summary
    print(builder.generate_build_plan_summary())

    # Show first few steps
    print("\nFIRST 10 STEPS:")
    print("="*70)
    for step in steps[:10]:
        row_count = len(step.rows_to_add)
        print(f"Step {step.step_num:3d} [{step.phase:12s}]: {step.description}")
        print(f"          ({row_count} rows)")


if __name__ == '__main__':
    main()
