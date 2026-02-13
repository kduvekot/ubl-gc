#!/usr/bin/env python3
"""
UBL GenericCode Git History Orchestrator

Processes all 35 UBL releases and creates git commits showing the complete
evolution of UBL GenericCode semantic models.

Strategy:
1. First release (UBL 2.0 PRD): Use ABIE-by-ABIE creation (~131 commits)
2. Subsequent releases: Use gc_diff to compute changes, create commits per change
3. File types: Track Entities, Signature-Entities, Endorsed-Entities separately
4. Versioning: All files in history branch use version-free names:
   - UBL-Entities.gc
   - UBL-Signature-Entities.gc
   - UBL-Endorsed-Entities.gc
"""

import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Tuple, List
import argparse

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

from release_manifest import RELEASES, get_release_pairs
from gc_diff import GCDiff, GCFileState
from gc_analyzer import GCAnalyzer
from gc_builder import GCBuilder
from gc_commit_builder import GCCommitBuilder

SESSION_URL = "https://claude.ai/code/session_01B5kfoVeuncQaSCz9nX4H1j"
BRANCH_NAME = "claude/git-history-exploration-bunUn"


class HistoryBuilder:
    """Orchestrates the building of git history from UBL releases"""

    def __init__(self, repo_root: str, work_dir: str, dry_run: bool = False):
        self.repo_root = Path(repo_root)
        self.work_dir = Path(work_dir)
        self.dry_run = dry_run
        self.commits_created = 0

    def get_source_path(
        self, release: dict, file_type: str
    ) -> Optional[Path]:
        """Get the source file path for a release file type.

        Args:
            release: Release dict from manifest
            file_type: One of 'entities', 'signature', 'endorsed'

        Returns:
            Path to source file, or None if not applicable
        """
        if file_type == "entities":
            key = "entities_file"
        elif file_type == "signature":
            key = "signature_file"
        elif file_type == "endorsed":
            key = "endorsed_file"
        else:
            raise ValueError(f"Unknown file type: {file_type}")

        filename = release.get(key)
        if filename is None:
            return None

        return self.repo_root / release["dir"] / filename

    @staticmethod
    def get_target_name(file_type: str) -> str:
        """Get the version-free target filename for a file type."""
        if file_type == "entities":
            return "UBL-Entities.gc"
        elif file_type == "signature":
            return "UBL-Signature-Entities.gc"
        elif file_type == "endorsed":
            return "UBL-Endorsed-Entities.gc"
        else:
            raise ValueError(f"Unknown file type: {file_type}")

    def set_git_env(self, release: dict) -> dict:
        """Set git environment variables for commit author/date."""
        env = os.environ.copy()
        date = release["date"]
        env["GIT_AUTHOR_DATE"] = f"{date}T12:00:00+00:00"
        env["GIT_COMMITTER_DATE"] = f"{date}T12:00:00+00:00"
        env["GIT_AUTHOR_NAME"] = "OASIS UBL TC"
        env["GIT_AUTHOR_EMAIL"] = "ubl-tc@oasis-open.org"
        env["GIT_COMMITTER_NAME"] = "OASIS UBL TC"
        env["GIT_COMMITTER_EMAIL"] = "ubl-tc@oasis-open.org"
        return env

    def git_add_and_commit(
        self, filename: str, message: str, release: dict, env: dict
    ) -> None:
        """Add a file and create a git commit with proper author/date."""
        if self.dry_run:
            print(f"  [DRY-RUN] git add {filename}")
            print(f"  [DRY-RUN] git commit: {message.splitlines()[0]}")
            return

        subprocess.run(
            ["git", "add", filename],
            cwd=self.work_dir,
            check=True,
            capture_output=True,
        )

        full_message = f"{message}\n\n{SESSION_URL}"
        subprocess.run(
            ["git", "commit", "-m", full_message],
            cwd=self.work_dir,
            check=True,
            capture_output=True,
            env=env,
        )
        self.commits_created += 1

    def git_commit_empty(
        self, message: str, release: dict, env: dict
    ) -> None:
        """Create an empty commit (no file changes)."""
        if self.dry_run:
            print(f"  [DRY-RUN] git commit --allow-empty: {message}")
            return

        full_message = f"{message}\n\n{SESSION_URL}"
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", full_message],
            cwd=self.work_dir,
            check=True,
            capture_output=True,
            env=env,
        )
        self.commits_created += 1

    def _set_git_env_global(self, release: dict) -> dict:
        """Set git author/date env vars on os.environ so subprocess inherits them.
        Returns the old values for restoration."""
        keys = ['GIT_AUTHOR_DATE', 'GIT_COMMITTER_DATE',
                'GIT_AUTHOR_NAME', 'GIT_AUTHOR_EMAIL',
                'GIT_COMMITTER_NAME', 'GIT_COMMITTER_EMAIL']
        old_vals = {k: os.environ.get(k) for k in keys}

        date = release['date']
        os.environ['GIT_AUTHOR_DATE'] = f'{date}T12:00:00+00:00'
        os.environ['GIT_COMMITTER_DATE'] = f'{date}T12:00:00+00:00'
        os.environ['GIT_AUTHOR_NAME'] = 'OASIS UBL TC'
        os.environ['GIT_AUTHOR_EMAIL'] = 'ubl-tc@oasis-open.org'
        os.environ['GIT_COMMITTER_NAME'] = 'OASIS UBL TC'
        os.environ['GIT_COMMITTER_EMAIL'] = 'ubl-tc@oasis-open.org'
        return old_vals

    @staticmethod
    def _restore_git_env(old_vals: dict) -> None:
        """Restore git env vars to previous values."""
        for k, v in old_vals.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def git_commit_staged(self, message: str, release: dict, env: dict) -> None:
        """Commit whatever is already staged (used after git rm)."""
        if self.dry_run:
            print(f"  [DRY-RUN] git commit: {message.splitlines()[0]}")
            return

        full_message = f"{message}\n\n{SESSION_URL}"
        subprocess.run(
            ["git", "commit", "-m", full_message],
            cwd=self.work_dir,
            check=True,
            capture_output=True,
            env=env,
        )
        self.commits_created += 1

    def process_first_release(
        self, release: dict
    ) -> None:
        """Process UBL 2.0 PRD using ABIE-by-ABIE creation.

        Creates ~131 commits (1 skeleton + 130 ABIE groups).
        """
        print(f"\nProcessing first release: {release['label']}")
        print("=" * 70)

        source_file = self.get_source_path(release, "entities")
        if source_file is None:
            raise ValueError(f"No entities file for {release['label']}")

        target_name = self.get_target_name("entities")

        if self.dry_run:
            print(f"  [DRY-RUN] Would analyze {source_file}")
            print(f"  [DRY-RUN] Would create ~131 ABIE-by-ABIE commits to {target_name}")
            self.commits_created += 131
            return

        # Analyze source file
        print(f"  Analyzing {source_file.name}...")
        analyzer = GCAnalyzer(str(source_file))
        analyzer.parse()
        analyzer.build_abies()
        analyzer.build_dependency_graph()
        analyzer.find_sccs_tarjan()
        analyzer.topological_sort_sccs()

        # Plan build
        print(f"  Planning build...")
        builder = GCBuilder(analyzer)
        steps = builder.plan_build()

        # Set git env globally so GCCommitBuilder inherits proper dates/author
        old_env = self._set_git_env_global(release)

        try:
            # Create commits using GCCommitBuilder
            print(f"  Creating {len(steps) + 1} commits...")
            commit_builder = GCCommitBuilder(str(source_file), target_name, str(self.work_dir))
            commit_builder.analyzer_abies = analyzer.abies

            # Create initial empty file
            commit_builder.create_empty_gc_file()
            commit_builder._git_add_and_commit(
                "UBL 2.0 PRD: Initialize GenericCode file structure\n\n"
                "Empty file with header, column definitions, and empty SimpleCodeList.\n"
                "Columns: ModelName, UBLName, DictionaryEntryName, ObjectClass,\n"
                "PropertyTerm, RepresentationTerm, DataType, AssociatedObjectClass,\n"
                "Cardinality, ComponentType, Definition, and more.\n\n"
                "Source: UBL 2.0 Proposed Recommendation Draft (2006)"
            )
            self.commits_created += 1

            # Build incrementally
            commit_builder.build_incremental(steps)
            self.commits_created += len(steps)
        finally:
            self._restore_git_env(old_env)

        print(f"  Created {len(steps) + 1} commits for first release")

    def process_transition(self, old_rel: dict, new_rel: dict) -> None:
        """Process a transition between two releases.

        For each file type (entities, signature, endorsed):
        - If file didn't exist before but exists now: add it
        - If file existed before and exists now: compute diff and create commits
        - If file existed before but doesn't exist now: remove it
        - If both are None: skip
        """
        rel_label = f"{old_rel['label']} -> {new_rel['label']}"
        print(f"\nProcessing: {rel_label}")
        print("=" * 70)

        for file_type in ["entities", "signature", "endorsed"]:
            old_file = self.get_source_path(old_rel, file_type)
            new_file = self.get_source_path(new_rel, file_type)
            target_name = self.get_target_name(file_type)

            if old_file is None and new_file is None:
                continue

            elif old_file is None and new_file is not None:
                self._add_new_file(new_file, target_name, new_rel)

            elif old_file is not None and new_file is None:
                self._remove_file(target_name, new_rel)

            else:
                self._diff_and_commit(
                    old_file, new_file, target_name, old_rel, new_rel
                )

    def _add_new_file(
        self, new_file: Path, target_name: str, release: dict
    ) -> None:
        """Add a new file to the history."""
        print(f"  Adding new file: {target_name}")

        if target_name == "UBL-Endorsed-Entities.gc":
            # Large file: use ABIE-by-ABIE creation
            self._add_large_file(new_file, target_name, release)
        else:
            # Small file (Signature): just copy the whole thing
            self._add_small_file(new_file, target_name, release)

    def _add_small_file(
        self, new_file: Path, target_name: str, release: dict
    ) -> None:
        """Add a small file (Signature-Entities) in one commit."""
        if self.dry_run:
            print(f"    [DRY-RUN] Copy {new_file.name} -> {target_name}")
            self.commits_created += 1
            return

        target_path = self.work_dir / target_name
        shutil.copy2(new_file, target_path)

        env = self.set_git_env(release)
        version = release["version"]
        stage = release["stage"].upper()
        msg = f"UBL {version} {stage}: Add {target_name}\n\nRelease: {release['label']}\nDate: {release['date']}"
        self.git_add_and_commit(target_name, msg, release, env)

    def _add_large_file(
        self, new_file: Path, target_name: str, release: dict
    ) -> None:
        """Add a large file (Endorsed-Entities) using ABIE-by-ABIE creation."""
        print(f"    Using ABIE-by-ABIE creation for {target_name}")

        if self.dry_run:
            print(f"    [DRY-RUN] Would analyze {new_file.name}")
            print(f"    [DRY-RUN] Would create multiple ABIE commits")
            self.commits_created += 10  # Rough estimate
            return

        analyzer = GCAnalyzer(str(new_file))
        analyzer.parse()
        analyzer.build_abies()
        analyzer.build_dependency_graph()
        analyzer.find_sccs_tarjan()
        analyzer.topological_sort_sccs()

        builder = GCBuilder(analyzer)
        steps = builder.plan_build()

        # Set git env globally so GCCommitBuilder inherits proper dates/author
        old_env = self._set_git_env_global(release)

        try:
            commit_builder = GCCommitBuilder(str(new_file), target_name, str(self.work_dir))
            commit_builder.analyzer_abies = analyzer.abies

            # Create initial empty file
            commit_builder.create_empty_gc_file()
            version = release["version"]
            stage = release["stage"].upper()
            msg = (f"UBL {version} {stage}: Initialize {target_name}\n\n"
                   f"Release: {release['label']}\nDate: {release['date']}")
            commit_builder._git_add_and_commit(msg)
            self.commits_created += 1

            # Build incrementally
            commit_builder.build_incremental(steps)
            self.commits_created += len(steps)
        finally:
            self._restore_git_env(old_env)

        print(f"    Created {len(steps) + 1} commits for {target_name}")

    def _remove_file(self, target_name: str, release: dict) -> None:
        """Remove a file from the history."""
        print(f"  Removing file: {target_name}")

        if self.dry_run:
            print(f"    [DRY-RUN] git rm {target_name}")
            self.commits_created += 1
            return

        target_path = self.work_dir / target_name
        if target_path.exists():
            subprocess.run(
                ["git", "rm", target_name],
                cwd=self.work_dir,
                check=True,
                capture_output=True,
            )

            env = self.set_git_env(release)
            version = release["version"]
            stage = release["stage"].upper()
            msg = (f"UBL {version} {stage}: Remove {target_name}\n\n"
                   f"Release: {release['label']}\nDate: {release['date']}")
            self.git_commit_staged(msg, release, env)

    def _diff_and_commit(
        self,
        old_file: Path,
        new_file: Path,
        target_name: str,
        old_rel: dict,
        new_rel: dict,
    ) -> None:
        """Compute diff and create commits for each change."""
        print(f"  Diffing {target_name}...")

        if self.dry_run:
            print(f"    [DRY-RUN] Would compute diff for {target_name}")
            self.commits_created += 1  # Conservative estimate
            return

        differ = GCDiff(str(old_file), str(new_file))
        changes = differ.compute()

        if not changes:
            # Empty commit for identical files
            env = self.set_git_env(new_rel)
            version = new_rel["version"]
            stage = new_rel["stage"].upper()
            msg = (f"UBL {version} {stage}: No changes to {target_name} "
                   f"(identical to {old_rel['stage'].upper()})\n\n"
                   f"Release: {new_rel['label']}\nDate: {new_rel['date']}")
            self.git_commit_empty(msg, new_rel, env)
            return

        # Apply changes incrementally
        state = GCDiff.parse_file(str(old_file))
        env = self.set_git_env(new_rel)
        version = new_rel["version"]
        stage = new_rel["stage"].upper()

        for i, change in enumerate(changes, 1):
            # Apply the change
            state = differ.apply_change(state, change)

            # Write the updated state
            target_path = self.work_dir / target_name
            GCDiff.write_state(state, str(target_path))

            # Create commit
            msg = (f"UBL {version} {stage}: {change.description}\n\n"
                   f"Release: {new_rel['label']}\nFile: {target_name}\n"
                   f"Date: {new_rel['date']}")
            self.git_add_and_commit(target_name, msg, new_rel, env)

        print(f"    Created {len(changes)} commits for {target_name}")

    def build(self, start_at: int = 0) -> None:
        """Build the entire history starting from a specific release index."""
        print("\n" + "=" * 70)
        print("UBL GENERICCODE GIT HISTORY BUILDER")
        print("=" * 70)

        print(f"Processing {len(RELEASES)} releases...")
        print(f"Starting at index {start_at}")

        # Process first release separately
        if start_at == 0:
            self.process_first_release(RELEASES[0])

        # Process remaining releases as transitions
        for old_rel, new_rel in get_release_pairs():
            old_idx = RELEASES.index(old_rel)
            if old_idx < start_at:
                continue

            self.process_transition(old_rel, new_rel)

        print("\n" + "=" * 70)
        print("BUILD COMPLETE")
        print("=" * 70)
        print(f"Total commits created: {self.commits_created}")


def setup_work_dir(repo_root: Path) -> Path:
    """Create temporary directory and clone repo."""
    work_dir = Path(tempfile.mkdtemp(prefix="ubl-history-"))
    print(f"\nSetting up work directory: {work_dir}")

    # Clone the repo (use --no-hardlinks to avoid filesystem issues)
    subprocess.run(
        ["git", "clone", "--no-hardlinks", str(repo_root), str(work_dir)],
        check=True,
        capture_output=True,
    )

    # Create orphan branch
    subprocess.run(
        ["git", "checkout", "--orphan", BRANCH_NAME],
        cwd=work_dir,
        check=True,
        capture_output=True,
    )

    # Remove all files from index
    subprocess.run(
        ["git", "rm", "-rf", "."],
        cwd=work_dir,
        check=True,
        capture_output=True,
    )

    # Disable commit signing in work directory (sandbox may not have signing keys)
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"],
        cwd=work_dir,
        check=True,
        capture_output=True,
    )

    print(f"Created orphan branch: {BRANCH_NAME}")

    return work_dir


def push_results(work_dir: Path) -> None:
    """Push the history branch to remote."""
    print("\n" + "=" * 70)
    print("PUSH INSTRUCTIONS")
    print("=" * 70)
    print(f"\nTo push the history branch, run:")
    print(f"  git -C {work_dir} push -u origin {BRANCH_NAME}")
    print(f"\nOr manually:")
    print(f"  cd {work_dir}")
    print(f"  git push -u origin {BRANCH_NAME}")


def cleanup(work_dir: Path) -> None:
    """Remove temporary directory."""
    if work_dir.exists():
        print(f"\nCleaning up temporary directory: {work_dir}")
        shutil.rmtree(work_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Build UBL GenericCode git history from 35 releases"
    )
    parser.add_argument(
        "--start-at",
        type=int,
        default=0,
        help="Start processing at this release index (for debugging/resuming)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without creating commits",
    )
    parser.add_argument(
        "--keep-work-dir",
        action="store_true",
        help="Keep temporary work directory for inspection",
    )

    args = parser.parse_args()

    # Find repo root: go up from scripts/lib to repository root
    script_file = Path(__file__).resolve()
    repo_root = script_file.parent.parent

    # Validate that we're in the right place
    if not (repo_root / "history").exists():
        print(f"Error: Not in ubl-gc repository root")
        print(f"Expected history/ directory at {repo_root}")
        print(f"Script location: {script_file}")
        sys.exit(1)

    work_dir = None
    try:
        work_dir = setup_work_dir(repo_root)

        builder = HistoryBuilder(repo_root, work_dir, dry_run=args.dry_run)
        builder.build(start_at=args.start_at)

        if not args.dry_run:
            push_results(work_dir)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if work_dir and not args.keep_work_dir:
            cleanup(work_dir)
        elif work_dir and args.keep_work_dir:
            print(f"\nWork directory preserved at: {work_dir}")


if __name__ == "__main__":
    main()
