#!/usr/bin/env python3
"""
GenericCode Semantic Differ

Computes semantic diffs between two UBL GenericCode (.gc) files
and outputs an ordered list of change operations that can be applied incrementally.

Works at the text line level to preserve exact formatting (whitespace, XML comments, etc.)
and ensures final output is byte-identical to the new file.
"""

import xml.etree.ElementTree as ET
import sys
import os
import re
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, OrderedDict
from collections import OrderedDict as ODict

sys.path.insert(0, str(Path(__file__).parent))
from gc_analyzer import GCAnalyzer


@dataclass
class ChangeOp:
    """Represents a single change operation"""
    op_type: str  # One of: metadata, column_add, column_remove, abie_add, abie_remove, abie_modify
    description: str  # Human-readable description for commit message
    details: dict  # Operation-specific data


@dataclass
class GCFileState:
    """Represents the state of a GenericCode file at a point in time"""
    header_lines: List[str] = field(default_factory=list)  # Before first <Row>
    abie_blocks: ODict = field(default_factory=ODict)  # object_class -> list of text lines
    footer_lines: List[str] = field(default_factory=list)  # After last </Row>


class GCDiff:
    """Computes semantic diffs between two GenericCode files"""

    def __init__(self, old_file: str, new_file: str):
        self.old_file = old_file
        self.new_file = new_file
        self.old_state = None
        self.new_state = None
        self._parse_both_files()

    def _parse_both_files(self) -> None:
        """Parse both files into GCFileState objects"""
        self.old_state = self.parse_file(self.old_file)
        self.new_state = self.parse_file(self.new_file)

    @staticmethod
    def parse_file(file_path: str) -> GCFileState:
        """
        Parse a GenericCode file into GCFileState.

        Extracts:
        - header_lines: Everything before the first <Row> tag
        - abie_blocks: Text blocks for each ABIE group (ABIE + all children)
        - footer_lines: Everything after the last </Row> tag
        """
        with open(file_path, 'r', encoding='utf-8') as f:
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
            # No rows, just return header and footer
            state = GCFileState()
            state.header_lines = all_lines
            state.footer_lines = []
            return state

        # Header: everything before first <Row>
        first_row_line = row_starts[0][0]
        header_lines = all_lines[:first_row_line]

        # Footer: everything after last </Row>
        last_row_end = row_ends[-1]
        footer_lines = all_lines[last_row_end + 1:]

        # Extract each row block (including <Row>...<!--N--> and </Row> lines)
        row_blocks = {}
        for idx, (start_line, row_num) in enumerate(row_starts):
            end_line = row_ends[idx]
            block = all_lines[start_line:end_line + 1]
            row_blocks[row_num] = block

        # Group rows into ABIE blocks and QDT (Qualified Data Type) blocks
        abie_blocks = ODict()
        current_object_class = None
        qdt_rows = []  # Qualified Data Type rows (no ComponentType, UBL 2.0 only)

        for row_num in sorted(row_blocks.keys()):
            block_lines = row_blocks[row_num]
            component_type = GCDiff._extract_column_value(block_lines, 'ComponentType')
            object_class = GCDiff._extract_column_value(block_lines, 'ObjectClass')

            if component_type == 'ABIE':
                current_object_class = object_class
                abie_blocks[object_class] = block_lines
            elif component_type in ('BBIE', 'ASBIE') and current_object_class:
                # Append to current ABIE's block
                abie_blocks[current_object_class].extend(block_lines)
            else:
                # Rows without ComponentType — Qualified Data Types in UBL 2.0
                qdt_rows.extend(block_lines)

        # Add QDT rows as a named block if any exist
        if qdt_rows:
            abie_blocks['QDT'] = qdt_rows

        state = GCFileState()
        state.header_lines = header_lines
        state.abie_blocks = abie_blocks
        state.footer_lines = footer_lines
        return state

    @staticmethod
    def _extract_column_value(row_lines: List[str], column_name: str) -> str:
        """Extract a column value from row text lines"""
        in_target_value = False
        for i, line in enumerate(row_lines):
            if f'ColumnRef="{column_name}"' in line:
                in_target_value = True
                # Try to find SimpleValue on this line
                if '<SimpleValue>' in line:
                    match = re.search(r'<SimpleValue>([^<]+)</SimpleValue>', line)
                    if match:
                        return match.group(1)
            elif in_target_value and '<SimpleValue>' in line:
                # SimpleValue is on the next line
                match = re.search(r'<SimpleValue>([^<]+)</SimpleValue>', line)
                if match:
                    return match.group(1)
            elif in_target_value and '</Value>' in line:
                # Value element closed without finding SimpleValue
                break
        return ""

    def compute(self) -> List[ChangeOp]:
        """
        Compute all change operations in commit order:
        1. Metadata changes (Identification section only)
        2. Column structure change (replaces ColumnSet area + strips removed col values)
        3. ABIE removals
        4. ABIE modifications (compared after column adjustment, with position fix)
        5. ABIE additions (in dependency order, inserted at correct position)
        6. ABIE moves (unmodified ABIEs that changed position)
        7. Footer update (if file footer changed)
        """
        changes = []

        # 1. Metadata changes (only Identification section, NOT entire header)
        metadata_change = self._compute_metadata_change()
        if metadata_change:
            changes.append(metadata_change)

        # 2. Column structure changes — batched into a single operation because
        # the ColumnSet formatting (indentation, whitespace) often changes between
        # versions, making individual column commits impossible without also
        # reformatting all unchanged columns.
        column_change = self._compute_column_structure_change()
        removed_cols = []
        if column_change:
            changes.append(column_change)
            removed_cols = column_change.details.get('removed_columns', [])

        # 3. Compute column-adjusted old blocks for ABIE comparison.
        # After column removals are applied, the old rows no longer have
        # removed column values. This lets ABIE modification commits contain
        # only genuine content changes (plus new column values from additions).
        adjusted_old_blocks = self._apply_column_removals_to_blocks(
            self.old_state.abie_blocks, removed_cols
        )

        # 4. ABIE removals
        abie_removals = self._compute_abie_removals()
        changes.extend(abie_removals)

        # 5. ABIE modifications (using column-adjusted old blocks)
        abie_modifications = self._compute_abie_modifications(adjusted_old_blocks)
        changes.extend(abie_modifications)

        # 6. ABIE additions (in dependency order)
        abie_additions = self._compute_abie_additions()
        changes.extend(abie_additions)

        # 7. Compute moves by simulating the state after all prior changes.
        # Additions, removals, and modifications already handle their own
        # positioning via new_file_order, so we only need to move ABIEs
        # that are genuinely still out of position after those operations.
        move_ops = self._compute_abie_moves(changes)
        changes.extend(move_ops)

        # 8. Footer update if needed (the new file may have a different footer)
        footer_change = self._compute_footer_change()
        if footer_change:
            changes.append(footer_change)

        return changes

    def _compute_column_structure_change(self) -> Optional[ChangeOp]:
        """
        Detect column structure changes between old and new files.
        Returns a single ChangeOp that replaces the entire ColumnSet area
        and strips removed column values from all rows.
        """
        old_columns = self._get_column_set(self.old_file)
        new_columns = self._get_column_set(self.new_file)

        removed = [c for c in old_columns if c not in new_columns]
        added = [c for c in new_columns if c not in old_columns]

        # Also check if the ColumnSet area formatting changed even without
        # column additions/removals
        old_cs_text = ''.join(self._extract_columnset_area(self.old_state.header_lines))
        new_cs_text = ''.join(self._extract_columnset_area(self.new_state.header_lines))

        if old_cs_text == new_cs_text:
            return None

        # Build description
        parts = []
        if removed:
            parts.append(f'remove {", ".join(removed)}')
        if added:
            parts.append(f'add {", ".join(added)}')
        if not removed and not added:
            parts.append('update formatting')
        description = f'Update column structure ({"; ".join(parts)})'

        return ChangeOp(
            op_type='column_structure',
            description=description,
            details={
                'removed_columns': removed,
                'added_columns': added,
                'old_columns': old_columns,
                'new_columns': new_columns,
            }
        )

    @staticmethod
    def _extract_columnset_area(header_lines: List[str]) -> List[str]:
        """Extract lines from after </Identification> to end of header.
        This covers <ColumnSet>...</ColumnSet> and <SimpleCodeList> opening."""
        start = None
        for i, line in enumerate(header_lines):
            if '</Identification>' in line:
                start = i + 1
                break
        if start is not None:
            return header_lines[start:]
        return []

    def _apply_column_removals_to_blocks(self, abie_blocks: ODict, removed_columns: List[str]) -> ODict:
        """Apply column value removals to old blocks for comparison purposes"""
        if not removed_columns:
            return abie_blocks
        adjusted = ODict()
        for name, lines in abie_blocks.items():
            adjusted_lines = lines
            for col_name in removed_columns:
                adjusted_lines = self._remove_column_from_block(adjusted_lines, col_name)
            adjusted[name] = adjusted_lines
        return adjusted

    def _compute_metadata_change(self) -> Optional[ChangeOp]:
        """Detect changes in the Identification section by comparing text blocks"""
        _, _, old_ident = self._extract_identification_block(self.old_state.header_lines)
        _, _, new_ident = self._extract_identification_block(self.new_state.header_lines)

        old_text = ''.join(old_ident)
        new_text = ''.join(new_ident)

        if old_text == new_text:
            return None

        # Build a simple description from ShortName if available
        old_short = ''
        new_short = ''
        for line in old_ident:
            m = re.search(r'<ShortName>([^<]+)</ShortName>', line)
            if m:
                old_short = m.group(1)
        for line in new_ident:
            m = re.search(r'<ShortName>([^<]+)</ShortName>', line)
            if m:
                new_short = m.group(1)

        description = f'Update metadata ({old_short} -> {new_short})' if old_short and new_short else 'Update GenericCode metadata'

        return ChangeOp(
            op_type='metadata',
            description=description,
            details={}
        )

    @staticmethod
    def _extract_identification_block(header_lines: List[str]):
        """Return (start_idx, end_idx, lines) of the <Identification>...</Identification> block"""
        start = end = None
        for i, line in enumerate(header_lines):
            if '<Identification>' in line:
                start = i
            elif '</Identification>' in line:
                end = i
                break
        if start is not None and end is not None:
            return start, end, header_lines[start:end+1]
        return None, None, []

    @staticmethod
    def _get_column_set(file_path: str) -> List[str]:
        """Extract column names from ColumnSet"""
        tree = ET.parse(file_path)
        root = tree.getroot()

        columns = []
        for col_elem in root.findall('.//Column'):
            col_id = col_elem.get('Id')
            if col_id:
                columns.append(col_id)

        return columns

    def _compute_abie_removals(self) -> List[ChangeOp]:
        """Find ABIEs present in old file but not in new file"""
        old_abies = set(self.old_state.abie_blocks.keys())
        new_abies = set(self.new_state.abie_blocks.keys())

        removed = old_abies - new_abies
        changes = []

        for abie_name in sorted(removed):
            changes.append(ChangeOp(
                op_type='abie_remove',
                description=f'Remove ABIE "{abie_name}"',
                details={
                    'object_class': abie_name,
                    'removed_abies': removed
                }
            ))
        return changes

    def _compute_abie_additions(self) -> List[ChangeOp]:
        """Find ABIEs in new file but not in old file, ordered by dependencies"""
        old_abies = set(self.old_state.abie_blocks.keys())
        new_abies = set(self.new_state.abie_blocks.keys())

        added = new_abies - old_abies

        # Use GCAnalyzer on the new file to get dependency ordering
        added_in_order = self._get_dependency_order(self.new_file, added)

        # Include new file's ABIE order so additions can be inserted
        # at the correct position rather than appended at the end
        new_file_order = list(self.new_state.abie_blocks.keys())

        changes = []
        for abie_name in added_in_order:
            changes.append(ChangeOp(
                op_type='abie_add',
                description=f'Add ABIE "{abie_name}"',
                details={
                    'object_class': abie_name,
                    'added_abies': added,
                    'block_lines': self.new_state.abie_blocks[abie_name],
                    'new_file_order': new_file_order,
                }
            ))
        return changes

    def _compute_abie_modifications(self, old_blocks: Optional[ODict] = None) -> List[ChangeOp]:
        """Find ABIEs that changed between old and new files.

        Args:
            old_blocks: Column-adjusted old blocks for comparison. If None,
                       uses self.old_state.abie_blocks directly.
        """
        if old_blocks is None:
            old_blocks = self.old_state.abie_blocks

        old_abies = set(old_blocks.keys())
        new_abies = set(self.new_state.abie_blocks.keys())

        common = old_abies & new_abies
        new_file_order = list(self.new_state.abie_blocks.keys())

        # Maintain new file's ordering
        modified = []
        for abie_name in self.new_state.abie_blocks.keys():
            if abie_name not in common:
                continue

            old_block = old_blocks[abie_name]
            new_block = self.new_state.abie_blocks[abie_name]

            # Compare text blocks
            old_text = ''.join(old_block)
            new_text = ''.join(new_block)

            if old_text != new_text:
                modified.append(abie_name)

        changes = []
        for abie_name in modified:
            changes.append(ChangeOp(
                op_type='abie_modify',
                description=f'Modify ABIE "{abie_name}"',
                details={
                    'object_class': abie_name,
                    'old_block': self.old_state.abie_blocks[abie_name],
                    'new_block': self.new_state.abie_blocks[abie_name],
                    'new_file_order': new_file_order,
                }
            ))
        return changes

    def _compute_abie_moves(self, prior_changes: List[ChangeOp]) -> List[ChangeOp]:
        """Find ABIEs still out of position after all prior changes are applied.

        Simulates the state after removals, modifications, and additions,
        then walks the target order and generates moves only for ABIEs that
        are genuinely misplaced. Each move is simulated before checking the
        next ABIE, so moves don't interfere with each other.
        """
        # Simulate applying all prior changes to get intermediate state
        state = GCFileState(
            header_lines=self.old_state.header_lines.copy(),
            abie_blocks=ODict((k, v.copy()) for k, v in self.old_state.abie_blocks.items()),
            footer_lines=self.old_state.footer_lines.copy(),
        )
        for change in prior_changes:
            state = self.apply_change(state, change)

        new_file_order = list(self.new_state.abie_blocks.keys())

        # Walk the target order; for each ABIE that has the wrong
        # predecessor, generate a move and apply it before continuing.
        changes = []
        for name in new_file_order:
            if name not in state.abie_blocks:
                continue

            current_order = list(state.abie_blocks.keys())

            # Find expected predecessor in target order
            # (among ABIEs that exist in current state)
            target_idx = new_file_order.index(name)
            expected_prev = None
            for i in range(target_idx - 1, -1, -1):
                if new_file_order[i] in state.abie_blocks:
                    expected_prev = new_file_order[i]
                    break

            # Find actual predecessor in current state
            current_idx = current_order.index(name)
            actual_prev = current_order[current_idx - 1] if current_idx > 0 else None

            if expected_prev != actual_prev:
                move = ChangeOp(
                    op_type='abie_move',
                    description=f'Move ABIE "{name}"',
                    details={
                        'object_class': name,
                        'new_file_order': new_file_order,
                    }
                )
                changes.append(move)
                # Simulate the move so subsequent checks see updated order
                state = self.apply_change(state, move)

        return changes

    def _compute_footer_change(self) -> Optional[ChangeOp]:
        """Check if the footer (after last </Row>) changed."""
        old_footer = ''.join(self.old_state.footer_lines)
        new_footer = ''.join(self.new_state.footer_lines)
        if old_footer != new_footer:
            return ChangeOp(
                op_type='footer',
                description='Update file footer',
                details={'new_footer': self.new_state.footer_lines}
            )
        return None

    @staticmethod
    def _apply_abie_move(state: GCFileState, change: ChangeOp) -> GCFileState:
        """Move an unmodified ABIE to its correct position."""
        abie_name = change.details['object_class']
        new_file_order = change.details['new_file_order']

        if abie_name not in state.abie_blocks:
            return state

        block = state.abie_blocks[abie_name]

        # Find correct predecessor
        target_idx = new_file_order.index(abie_name)
        insert_after = None
        for i in range(target_idx - 1, -1, -1):
            if new_file_order[i] in state.abie_blocks and new_file_order[i] != abie_name:
                insert_after = new_file_order[i]
                break

        new_state = GCFileState()
        new_state.header_lines = state.header_lines.copy()
        new_state.footer_lines = state.footer_lines.copy()

        new_blocks = ODict()
        if insert_after is None:
            new_blocks[abie_name] = block.copy()
            for k, v in state.abie_blocks.items():
                if k != abie_name:
                    new_blocks[k] = v.copy()
        else:
            for k, v in state.abie_blocks.items():
                if k == abie_name:
                    continue
                new_blocks[k] = v.copy()
                if k == insert_after:
                    new_blocks[abie_name] = block.copy()

        new_state.abie_blocks = new_blocks
        return new_state

    @staticmethod
    def _apply_footer_change(state: GCFileState, change: ChangeOp) -> GCFileState:
        """Apply footer update."""
        new_state = GCFileState()
        new_state.header_lines = state.header_lines.copy()
        new_state.abie_blocks = ODict((k, v.copy()) for k, v in state.abie_blocks.items())
        new_state.footer_lines = change.details['new_footer']
        return new_state

    @staticmethod
    def _get_dependency_order(file_path: str, abie_names: set) -> List[str]:
        """
        Get optimal insertion order for ABIEs using dependency analysis.
        Uses GCAnalyzer to compute dependency graph and topological sort.
        Names not found in the analyzer (e.g., QDT) are appended at
        the end.
        """
        analyzer = GCAnalyzer(file_path)
        analyzer.parse()
        analyzer.build_abies()
        analyzer.build_dependency_graph()
        analyzer.find_sccs_tarjan()
        analyzer.topological_sort_sccs()

        # Get commit order and filter to only requested ABIEs
        commit_order = analyzer.get_abie_commit_order()
        result = []
        found = set()

        for abies in commit_order:
            for abie in abies:
                if abie.object_class in abie_names:
                    result.append(abie.object_class)
                    found.add(abie.object_class)

        # Append any names not found by the analyzer (e.g., QDT)
        for name in sorted(abie_names - found):
            result.append(name)

        return result

    def apply_change(self, state: GCFileState, change: ChangeOp) -> GCFileState:
        """Apply a single change operation to produce new state"""
        if change.op_type == 'metadata':
            return self._apply_metadata_change(state, change)
        elif change.op_type == 'column_structure':
            return self._apply_column_structure(state, change)
        elif change.op_type == 'abie_add':
            return self._apply_abie_add(state, change)
        elif change.op_type == 'abie_remove':
            return self._apply_abie_remove(state, change)
        elif change.op_type == 'abie_modify':
            return self._apply_abie_modify(state, change)
        elif change.op_type == 'abie_move':
            return self._apply_abie_move(state, change)
        elif change.op_type == 'footer':
            return self._apply_footer_change(state, change)
        else:
            return state

    def _apply_metadata_change(self, state: GCFileState, change: ChangeOp) -> GCFileState:
        """Apply metadata changes by replacing only the Identification block"""
        new_state = GCFileState()
        # Extract new Identification block from the new file
        _, _, new_ident_lines = self._extract_identification_block(self.new_state.header_lines)
        # Find and replace in current header
        start, end, _ = self._extract_identification_block(state.header_lines)
        if start is not None and end is not None:
            new_state.header_lines = state.header_lines[:start] + new_ident_lines + state.header_lines[end+1:]
        else:
            new_state.header_lines = state.header_lines.copy()
        new_state.abie_blocks = ODict((k, v.copy()) for k, v in state.abie_blocks.items())
        new_state.footer_lines = state.footer_lines.copy()
        return new_state

    def _apply_column_structure(self, state: GCFileState, change: ChangeOp) -> GCFileState:
        """
        Apply column structure change:
        1. Replace the ColumnSet area (everything after </Identification>) from new file
        2. Strip removed column values from all ABIE blocks
        """
        removed_cols = change.details.get('removed_columns', [])

        new_state = GCFileState()

        # Replace the post-Identification header with the new file's version
        old_ident_end = None
        for i, line in enumerate(state.header_lines):
            if '</Identification>' in line:
                old_ident_end = i
                break

        new_cs_area = self._extract_columnset_area(self.new_state.header_lines)
        if old_ident_end is not None:
            new_state.header_lines = state.header_lines[:old_ident_end + 1] + new_cs_area
        else:
            new_state.header_lines = self.new_state.header_lines.copy()

        new_state.footer_lines = state.footer_lines.copy()

        # Strip removed column values from all ABIE blocks
        new_abie_blocks = ODict()
        for abie_name, block_lines in state.abie_blocks.items():
            filtered_lines = block_lines
            for col_name in removed_cols:
                filtered_lines = self._remove_column_from_block(filtered_lines, col_name)
            new_abie_blocks[abie_name] = filtered_lines

        new_state.abie_blocks = new_abie_blocks
        return new_state

    @staticmethod
    def _remove_column_from_block(block_lines: List[str], col_name: str) -> List[str]:
        """Remove Value elements for a specific column from a row block"""
        result = []
        i = 0

        while i < len(block_lines):
            line = block_lines[i]

            # Check if this line starts a Value element for the column to remove
            if f'ColumnRef="{col_name}"' in line:
                # Find the matching </Value> tag
                if '</Value>' in line:
                    # Single-line value, skip it
                    i += 1
                    continue
                else:
                    # Multi-line value, skip until we find </Value>
                    while i < len(block_lines) and '</Value>' not in block_lines[i]:
                        i += 1
                    # Skip the </Value> line too
                    i += 1
                    continue

            result.append(line)
            i += 1

        return result

    @staticmethod
    def _apply_abie_add(state: GCFileState, change: ChangeOp) -> GCFileState:
        """Apply ABIE addition, inserting at the correct position based on new file ordering."""
        abie_name = change.details['object_class']
        block_lines = change.details['block_lines']
        new_file_order = change.details.get('new_file_order', [])

        new_state = GCFileState()
        new_state.header_lines = state.header_lines.copy()
        new_state.footer_lines = state.footer_lines.copy()

        if not new_file_order or abie_name not in new_file_order:
            # Fallback: append at end
            new_state.abie_blocks = ODict((k, v.copy()) for k, v in state.abie_blocks.items())
            new_state.abie_blocks[abie_name] = block_lines
            return new_state

        # Find the ABIE that should precede this one in the target order
        # (looking only at ABIEs that already exist in the current state)
        target_idx = new_file_order.index(abie_name)
        insert_after = None
        for i in range(target_idx - 1, -1, -1):
            if new_file_order[i] in state.abie_blocks:
                insert_after = new_file_order[i]
                break

        new_blocks = ODict()
        if insert_after is None:
            # Insert at the beginning
            new_blocks[abie_name] = block_lines
            for k, v in state.abie_blocks.items():
                new_blocks[k] = v.copy()
        else:
            for k, v in state.abie_blocks.items():
                new_blocks[k] = v.copy()
                if k == insert_after:
                    new_blocks[abie_name] = block_lines

        new_state.abie_blocks = new_blocks
        return new_state

    @staticmethod
    def _apply_abie_remove(state: GCFileState, change: ChangeOp) -> GCFileState:
        """Apply ABIE removal (remove ABIE block from abie_blocks)"""
        abie_name = change.details['object_class']

        new_state = GCFileState()
        new_state.header_lines = state.header_lines.copy()
        new_state.footer_lines = state.footer_lines.copy()
        # Deep copy the abie_blocks to avoid sharing list references
        new_state.abie_blocks = ODict((k, v.copy()) for k, v in state.abie_blocks.items())

        if abie_name in new_state.abie_blocks:
            del new_state.abie_blocks[abie_name]

        return new_state

    @staticmethod
    def _apply_abie_modify(state: GCFileState, change: ChangeOp) -> GCFileState:
        """Apply ABIE modification (replace content and fix position if needed)."""
        abie_name = change.details['object_class']
        new_block = change.details['new_block']
        new_file_order = change.details.get('new_file_order', [])

        new_state = GCFileState()
        new_state.header_lines = state.header_lines.copy()
        new_state.footer_lines = state.footer_lines.copy()

        if not new_file_order or abie_name not in new_file_order:
            # Fallback: replace in place
            new_state.abie_blocks = ODict((k, v.copy()) for k, v in state.abie_blocks.items())
            new_state.abie_blocks[abie_name] = new_block
            return new_state

        # Check if position needs to change
        current_keys = list(state.abie_blocks.keys())
        current_idx = current_keys.index(abie_name) if abie_name in current_keys else -1

        # Find correct position: what should come before this ABIE?
        target_idx = new_file_order.index(abie_name)
        insert_after = None
        for i in range(target_idx - 1, -1, -1):
            if new_file_order[i] in state.abie_blocks and new_file_order[i] != abie_name:
                insert_after = new_file_order[i]
                break

        # Check if it's already in the right position
        if insert_after is not None:
            expected_prev_idx = current_keys.index(insert_after) if insert_after in current_keys else -1
            if expected_prev_idx >= 0 and current_idx == expected_prev_idx + 1:
                # Already in correct position, just replace content
                new_state.abie_blocks = ODict((k, v.copy()) for k, v in state.abie_blocks.items())
                new_state.abie_blocks[abie_name] = new_block
                return new_state
        elif current_idx == 0:
            # Should be first and already is first
            new_state.abie_blocks = ODict((k, v.copy()) for k, v in state.abie_blocks.items())
            new_state.abie_blocks[abie_name] = new_block
            return new_state

        # Position needs to change: rebuild with ABIE at correct position
        new_blocks = ODict()
        if insert_after is None:
            # Should be first
            new_blocks[abie_name] = new_block
            for k, v in state.abie_blocks.items():
                if k != abie_name:
                    new_blocks[k] = v.copy()
        else:
            for k, v in state.abie_blocks.items():
                if k == abie_name:
                    continue  # Skip, will insert at correct position
                new_blocks[k] = v.copy()
                if k == insert_after:
                    new_blocks[abie_name] = new_block

        new_state.abie_blocks = new_blocks
        return new_state

    @staticmethod
    def write_state(state: GCFileState, output_path: str) -> None:
        """Write GCFileState to a file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write header
            for line in state.header_lines:
                f.write(line)

            # Write all ABIE blocks in order
            for abie_name, block_lines in state.abie_blocks.items():
                for line in block_lines:
                    f.write(line)

            # Write footer
            for line in state.footer_lines:
                f.write(line)


def main():
    if len(sys.argv) < 3:
        print("Usage: gc_diff.py <old-gc-file> <new-gc-file>")
        sys.exit(1)

    old_file = sys.argv[1]
    new_file = sys.argv[2]

    print(f"Comparing GenericCode files:")
    print(f"  Old: {old_file}")
    print(f"  New: {new_file}")
    print()

    differ = GCDiff(old_file, new_file)
    changes = differ.compute()

    print(f"Found {len(changes)} change operations:\n")
    for i, change in enumerate(changes, 1):
        print(f"  {i:3d}. [{change.op_type:15s}] {change.description}")

    # Verify by applying all changes
    print("\nVerifying by applying all changes...")
    state = GCDiff.parse_file(old_file)
    for change in changes:
        state = differ.apply_change(state, change)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.gc', delete=False) as f:
        tmp_path = f.name
    differ.write_state(state, tmp_path)

    with open(new_file, 'r') as new_f:
        new_content = new_f.read()
    with open(tmp_path, 'r') as result_f:
        result_content = result_f.read()

    os.unlink(tmp_path)

    if result_content == new_content:
        print("\nVERIFICATION PASSED: Result is byte-identical to new file")
    else:
        print("\nVERIFICATION FAILED: Result differs from new file!")
        result_lines = result_content.splitlines()
        new_lines = new_content.splitlines()
        for line_num, (a, b) in enumerate(zip(result_lines, new_lines), 1):
            if a != b:
                print(f"  First diff at line {line_num}:")
                print(f"    Got:      {a[:120]}")
                print(f"    Expected: {b[:120]}")
                break
        if len(result_lines) != len(new_lines):
            print(f"  Line count: got {len(result_lines)}, expected {len(new_lines)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
