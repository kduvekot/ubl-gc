#!/usr/bin/env python3
"""
GenericCode File Analyzer

Analyzes UBL GenericCode (.gc) files to:
1. Parse the semantic model structure
2. Build dependency graphs between ABIEs
3. Perform topological sort for bottom-up ordering
4. Determine optimal insertion order for git history
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import sys


# Namespace for GenericCode XML
NS = {'gc': 'http://docs.oasis-open.org/codelist/ns/genericode/1.0/'}


@dataclass
class Row:
    """Represents a single row (element definition) in a GenericCode file"""
    row_num: int
    component_type: str  # ABIE, BBIE, ASBIE
    dictionary_entry_name: str
    object_class: str
    property_term: Optional[str] = None
    associated_object_class: Optional[str] = None  # For ASBIEs
    cardinality: Optional[str] = None
    xml_data: ET.Element = None  # Original XML element

    def __hash__(self):
        return hash((self.row_num, self.dictionary_entry_name))


@dataclass
class ABIE:
    """Represents an Aggregate Business Information Entity (complex type)"""
    name: str  # e.g., "Address. Details"
    object_class: str  # e.g., "Address"
    row: Row
    bbies: List[Row] = field(default_factory=list)  # Basic properties
    asbies: List[Row] = field(default_factory=list)  # Association properties
    depends_on: Set[str] = field(default_factory=set)  # Object classes this ABIE depends on

    def __hash__(self):
        return hash(self.name)


class GCAnalyzer:
    """Analyzes GenericCode files and builds dependency graphs"""

    def __init__(self, gc_file_path: str):
        self.file_path = gc_file_path
        self.tree = None
        self.root = None
        self.rows: List[Row] = []
        self.abies: Dict[str, ABIE] = {}  # object_class -> ABIE
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)

    def parse(self) -> None:
        """Parse the GenericCode XML file"""
        self.tree = ET.parse(self.file_path)
        self.root = self.tree.getroot()

        # Parse all rows - Row elements are NOT in gc namespace
        row_elements = self.root.findall('.//Row')

        for idx, row_elem in enumerate(row_elements, start=1):
            row_data = self._parse_row(row_elem, idx)
            if row_data:
                self.rows.append(row_data)

        print(f"Parsed {len(self.rows)} rows from {self.file_path}")

    def _parse_row(self, row_elem: ET.Element, row_num: int) -> Optional[Row]:
        """Parse a single row element"""
        values = {}
        # Value and SimpleValue are NOT in gc namespace
        for value_elem in row_elem.findall('Value'):
            col_ref = value_elem.get('ColumnRef')
            simple_value = value_elem.find('SimpleValue')
            if simple_value is not None and simple_value.text:
                values[col_ref] = simple_value.text.strip()

        component_type = values.get('ComponentType', '').strip()
        if not component_type:
            return None

        return Row(
            row_num=row_num,
            component_type=component_type,
            dictionary_entry_name=values.get('DictionaryEntryName', ''),
            object_class=values.get('ObjectClass', ''),
            property_term=values.get('PropertyTerm'),
            associated_object_class=values.get('AssociatedObjectClass'),
            cardinality=values.get('Cardinality'),
            xml_data=row_elem
        )

    def build_abies(self) -> None:
        """Group rows into ABIEs with their BBIEs and ASBIEs"""
        current_abie: Optional[ABIE] = None

        for row in self.rows:
            if row.component_type == 'ABIE':
                # Start new ABIE
                current_abie = ABIE(
                    name=row.dictionary_entry_name,
                    object_class=row.object_class,
                    row=row
                )
                self.abies[row.object_class] = current_abie

            elif row.component_type == 'BBIE' and current_abie:
                # Add BBIE to current ABIE
                current_abie.bbies.append(row)

            elif row.component_type == 'ASBIE' and current_abie:
                # Add ASBIE to current ABIE
                current_abie.asbies.append(row)

                # Track dependency
                if row.associated_object_class:
                    current_abie.depends_on.add(row.associated_object_class)

        print(f"Built {len(self.abies)} ABIEs")

        # Print dependency summary
        leaf_count = sum(1 for abie in self.abies.values() if not abie.depends_on)
        print(f"  - {leaf_count} leaf ABIEs (no dependencies)")
        print(f"  - {len(self.abies) - leaf_count} ABIEs with dependencies")

    def build_dependency_graph(self) -> None:
        """Build directed graph of ABIE dependencies"""
        for obj_class, abie in self.abies.items():
            for dep in abie.depends_on:
                # Skip self-references
                if dep != obj_class and dep in self.abies:
                    self.dependency_graph[obj_class].add(dep)

        print(f"Built dependency graph with {len(self.dependency_graph)} nodes")

    def topological_sort(self) -> List[str]:
        """
        Perform topological sort to get bottom-up ordering.
        Returns list of object class names in dependency order.

        ABIEs with no dependencies come first, then ABIEs that depend on them, etc.
        """
        # Kahn's algorithm
        in_degree = {obj_class: 0 for obj_class in self.abies}

        # Calculate in-degrees
        for obj_class in self.abies:
            for dep in self.dependency_graph[obj_class]:
                in_degree[dep] += 1

        # Start with nodes that have no incoming edges (leaves)
        queue = [obj_class for obj_class, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # Sort queue for deterministic ordering
            queue.sort()
            current = queue.pop(0)
            result.append(current)

            # For each node that depends on current
            for obj_class in self.abies:
                if current in self.dependency_graph[obj_class]:
                    in_degree[obj_class] -= 1
                    if in_degree[obj_class] == 0:
                        queue.append(obj_class)

        # Check for cycles
        if len(result) != len(self.abies):
            remaining = set(self.abies.keys()) - set(result)
            print(f"WARNING: Circular dependencies detected! {len(remaining)} ABIEs not sorted:")
            for obj_class in sorted(remaining)[:5]:
                deps = self.dependency_graph[obj_class]
                print(f"  - {obj_class} depends on: {deps}")
            # Add remaining in alphabetical order
            result.extend(sorted(remaining))

        return result

    def get_insertion_order(self) -> List[ABIE]:
        """
        Get the optimal order for inserting ABIEs (with their BBIEs/ASBIEs).
        Returns ABIEs in bottom-up dependency order.
        """
        sorted_classes = self.topological_sort()
        return [self.abies[obj_class] for obj_class in sorted_classes]

    def find_cycles(self) -> List[List[str]]:
        """Find circular dependencies using DFS"""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.dependency_graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for obj_class in self.abies:
            if obj_class not in visited:
                dfs(obj_class)

        return cycles

    def analyze_dependencies(self) -> None:
        """Print detailed dependency analysis"""
        print("\n" + "="*70)
        print("DEPENDENCY ANALYSIS")
        print("="*70)

        # Check for cycles
        cycles = self.find_cycles()
        if cycles:
            print(f"\n⚠️  Found {len(cycles)} circular dependency chain(s):")
            for i, cycle in enumerate(cycles[:5], 1):  # Show first 5
                print(f"  {i}. {' → '.join(cycle)}")
            if len(cycles) > 5:
                print(f"  ... and {len(cycles) - 5} more cycles")

        sorted_order = self.topological_sort()

        # Group by dependency level
        levels: Dict[int, List[str]] = defaultdict(list)
        level_map: Dict[str, int] = {}

        for obj_class in sorted_order:
            # Calculate level (max dependency level + 1)
            deps = self.dependency_graph[obj_class]
            if not deps:
                level = 0
            else:
                # Get levels of dependencies that have been processed
                dep_levels = [level_map[dep] for dep in deps if dep in level_map]
                if dep_levels:
                    level = max(dep_levels) + 1
                else:
                    # Dependencies not yet processed (circular dependency)
                    level = 0

            level_map[obj_class] = level
            levels[level].append(obj_class)

        # Print by level
        for level in sorted(levels.keys()):
            print(f"\nLevel {level} ({len(levels[level])} ABIEs):")
            for obj_class in sorted(levels[level])[:10]:  # Show first 10
                abie = self.abies[obj_class]
                deps = self.dependency_graph[obj_class]
                print(f"  - {abie.name}")
                print(f"    BBIEs: {len(abie.bbies)}, ASBIEs: {len(abie.asbies)}")
                if deps:
                    print(f"    Depends on: {', '.join(sorted(deps)[:3])}")
            if len(levels[level]) > 10:
                print(f"  ... and {len(levels[level]) - 10} more")

        if levels:
            print(f"\nTotal levels: {max(levels.keys()) + 1}")
        else:
            print("\nNo ABIEs found!")


def main():
    if len(sys.argv) < 2:
        print("Usage: gc_analyzer.py <path-to-gc-file>")
        sys.exit(1)

    gc_file = sys.argv[1]
    print(f"Analyzing: {gc_file}\n")

    analyzer = GCAnalyzer(gc_file)
    analyzer.parse()
    analyzer.build_abies()
    analyzer.build_dependency_graph()
    analyzer.analyze_dependencies()

    print("\n" + "="*70)
    print("INSERTION ORDER (first 20):")
    print("="*70)
    insertion_order = analyzer.get_insertion_order()
    for i, abie in enumerate(insertion_order[:20], start=1):
        print(f"{i:3d}. {abie.name}")
        print(f"     {len(abie.bbies)} BBIEs, {len(abie.asbies)} ASBIEs")


if __name__ == '__main__':
    main()
