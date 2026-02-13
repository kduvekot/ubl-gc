#!/usr/bin/env python3
"""
GenericCode File Analyzer

Analyzes UBL GenericCode (.gc) files to:
1. Parse the semantic model structure
2. Build dependency graphs between ABIEs
3. Find strongly connected components (Tarjan's algorithm)
4. Produce topological ordering of SCC-condensed DAG
5. Determine optimal ABIE-group insertion order for git history
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from collections import defaultdict
import sys


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


@dataclass
class SCCGroup:
    """A strongly connected component - one or more ABIEs that form a cycle"""
    index: int
    members: List[str]  # Object class names
    is_cycle: bool  # True if more than one member, or self-referencing

    @property
    def label(self) -> str:
        if len(self.members) == 1:
            return self.members[0]
        return " + ".join(sorted(self.members))


class GCAnalyzer:
    """Analyzes GenericCode files and builds dependency graphs"""

    def __init__(self, gc_file_path: str):
        self.file_path = gc_file_path
        self.tree = None
        self.root = None
        self.rows: List[Row] = []
        self.abies: Dict[str, ABIE] = {}  # object_class -> ABIE
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.sccs: List[SCCGroup] = []
        self.scc_order: List[SCCGroup] = []  # Topologically sorted

    def parse(self) -> None:
        """Parse the GenericCode XML file"""
        self.tree = ET.parse(self.file_path)
        self.root = self.tree.getroot()

        # Parse all rows
        row_elements = self.root.findall('.//Row')

        for idx, row_elem in enumerate(row_elements, start=1):
            row_data = self._parse_row(row_elem, idx)
            if row_data:
                self.rows.append(row_data)

        print(f"Parsed {len(self.rows)} rows from {self.file_path}")

    def _parse_row(self, row_elem: ET.Element, row_num: int) -> Optional[Row]:
        """Parse a single row element"""
        values = {}
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
                current_abie = ABIE(
                    name=row.dictionary_entry_name,
                    object_class=row.object_class,
                    row=row
                )
                self.abies[row.object_class] = current_abie

            elif row.component_type == 'BBIE' and current_abie:
                current_abie.bbies.append(row)

            elif row.component_type == 'ASBIE' and current_abie:
                current_abie.asbies.append(row)
                if row.associated_object_class:
                    current_abie.depends_on.add(row.associated_object_class)

        print(f"Built {len(self.abies)} ABIEs")

        leaf_count = sum(1 for abie in self.abies.values()
                         if not abie.depends_on - {abie.object_class})
        print(f"  - {leaf_count} leaf ABIEs (no external dependencies)")
        print(f"  - {len(self.abies) - leaf_count} ABIEs with external dependencies")

    def build_dependency_graph(self) -> None:
        """Build directed graph of ABIE dependencies (excluding self-refs)"""
        for obj_class, abie in self.abies.items():
            for dep in abie.depends_on:
                if dep != obj_class and dep in self.abies:
                    self.dependency_graph[obj_class].add(dep)

        print(f"Built dependency graph with {len(self.dependency_graph)} nodes with edges")

    def find_sccs_tarjan(self) -> List[SCCGroup]:
        """
        Find strongly connected components using Tarjan's algorithm.
        Returns SCCs in reverse topological order (leaves first).
        """
        index_counter = [0]
        stack = []
        lowlink = {}
        index = {}
        on_stack = {}
        sccs_raw = []

        def strongconnect(v):
            index[v] = index_counter[0]
            lowlink[v] = index_counter[0]
            index_counter[0] += 1
            stack.append(v)
            on_stack[v] = True

            for w in self.dependency_graph.get(v, set()):
                if w not in self.abies:
                    continue
                if w not in index:
                    strongconnect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif on_stack.get(w, False):
                    lowlink[v] = min(lowlink[v], index[w])

            if lowlink[v] == index[v]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    scc.append(w)
                    if w == v:
                        break
                sccs_raw.append(scc)

        for v in sorted(self.abies.keys()):
            if v not in index:
                strongconnect(v)

        # Build SCCGroup objects
        self_refs = {oc for oc, abie in self.abies.items()
                     if oc in abie.depends_on}

        self.sccs = []
        for i, members in enumerate(sccs_raw):
            is_cycle = len(members) > 1 or (len(members) == 1 and members[0] in self_refs)
            self.sccs.append(SCCGroup(
                index=i,
                members=sorted(members),
                is_cycle=is_cycle
            ))

        print(f"Found {len(self.sccs)} SCCs ({sum(1 for s in self.sccs if s.is_cycle)} with cycles)")
        return self.sccs

    def topological_sort_sccs(self) -> List[SCCGroup]:
        """
        Topologically sort the SCC-condensed DAG.
        Returns SCCs in dependency order (leaves first, documents last).
        """
        if not self.sccs:
            self.find_sccs_tarjan()

        # Map each ABIE to its SCC
        scc_map = {}
        for scc in self.sccs:
            for member in scc.members:
                scc_map[member] = scc.index

        # Build SCC-level DAG
        scc_deps = defaultdict(set)
        for node in self.abies:
            for ref in self.dependency_graph.get(node, set()):
                if ref in self.abies and scc_map[node] != scc_map[ref]:
                    scc_deps[scc_map[node]].add(scc_map[ref])

        # Topological sort via DFS (post-order)
        visited = set()
        topo_order = []

        def dfs(n):
            if n in visited:
                return
            visited.add(n)
            for dep in scc_deps[n]:
                dfs(dep)
            topo_order.append(n)

        for scc in self.sccs:
            dfs(scc.index)

        # Map back to SCCGroup objects
        scc_by_index = {scc.index: scc for scc in self.sccs}
        self.scc_order = [scc_by_index[i] for i in topo_order]

        print(f"Topological order: {len(self.scc_order)} groups")
        return self.scc_order

    def get_abie_commit_order(self) -> List[List[ABIE]]:
        """
        Get the optimal commit order: one commit per SCC group.
        Each entry is a list of ABIEs to commit together.
        Most entries will be a single ABIE; cycle groups have multiple.
        """
        if not self.scc_order:
            self.topological_sort_sccs()

        commit_order = []
        for scc in self.scc_order:
            abies = [self.abies[oc] for oc in scc.members]
            # Sort within group by original row order
            abies.sort(key=lambda a: a.row.row_num)
            commit_order.append(abies)

        return commit_order

    def analyze_dependencies(self) -> None:
        """Print detailed dependency analysis"""
        print("\n" + "=" * 70)
        print("DEPENDENCY ANALYSIS")
        print("=" * 70)

        if not self.scc_order:
            self.topological_sort_sccs()

        # Summary
        single_count = sum(1 for scc in self.sccs if not scc.is_cycle)
        cycle_count = sum(1 for scc in self.sccs if scc.is_cycle)
        self_ref_only = sum(1 for scc in self.sccs
                           if scc.is_cycle and len(scc.members) == 1)
        multi_cycles = [scc for scc in self.sccs
                        if scc.is_cycle and len(scc.members) > 1]

        print(f"\nSCC Summary:")
        print(f"  Single ABIEs (no cycles):  {single_count}")
        print(f"  Self-referencing ABIEs:    {self_ref_only}")
        print(f"  Multi-ABIE cycles:         {len(multi_cycles)}")

        for mc in multi_cycles:
            print(f"    Cycle: {mc.label}")

        # Commit order
        commit_order = self.get_abie_commit_order()
        print(f"\nCommit order ({len(commit_order)} commits):")
        for i, abies in enumerate(commit_order[:10], 1):
            if len(abies) == 1:
                a = abies[0]
                print(f"  {i:3d}. {a.object_class}"
                      f" ({len(a.bbies)} BBIEs, {len(a.asbies)} ASBIEs)")
            else:
                names = [a.object_class for a in abies]
                total_bbies = sum(len(a.bbies) for a in abies)
                total_asbies = sum(len(a.asbies) for a in abies)
                print(f"  {i:3d}. [CYCLE] {' + '.join(names)}"
                      f" ({total_bbies} BBIEs, {total_asbies} ASBIEs)")
        if len(commit_order) > 10:
            print(f"  ... and {len(commit_order) - 10} more")


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
    analyzer.find_sccs_tarjan()
    analyzer.topological_sort_sccs()
    analyzer.analyze_dependencies()

    print("\n" + "=" * 70)
    print("COMMIT ORDER (first 20):")
    print("=" * 70)
    commit_order = analyzer.get_abie_commit_order()
    for i, abies in enumerate(commit_order[:20], start=1):
        if len(abies) == 1:
            a = abies[0]
            print(f"{i:3d}. {a.name}")
            print(f"     {len(a.bbies)} BBIEs, {len(a.asbies)} ASBIEs")
        else:
            print(f"{i:3d}. [CYCLE GROUP]")
            for a in abies:
                print(f"     - {a.name} ({len(a.bbies)} BBIEs, {len(a.asbies)} ASBIEs)")


if __name__ == '__main__':
    main()
