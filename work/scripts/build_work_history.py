#!/usr/bin/env python3
"""
UBL Work History Builder

Standalone build script for the expanded work-history branch.
Uses the work_release_manifest (44 releases = 35 official + 9 intermediate)
with the HistoryBuilder from scripts/build_history.py.

This script lives entirely under work/ and does NOT modify anything in scripts/.
The only dependency on scripts/ is importing the HistoryBuilder class and
supporting library modules (gc_diff, gc_analyzer, etc.).

Timestamp support:
  Intermediate releases have a 'timestamp' field with exact ISO 8601 times
  from the CI artifacts. This script monkey-patches the HistoryBuilder's
  set_git_env and _set_git_env_global methods to use these timestamps for
  accurate git commit dates.
"""

import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path
import argparse

# Set up import paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / 'scripts'
SCRIPTS_LIB = SCRIPTS_DIR / 'lib'
WORK_SCRIPTS = Path(__file__).resolve().parent

sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_LIB))
sys.path.insert(0, str(WORK_SCRIPTS))

from work_release_manifest import RELEASES, get_release_pairs
from build_history import HistoryBuilder, setup_work_dir, push_results, cleanup

DEFAULT_BRANCH = "work-history"


class WorkHistoryBuilder(HistoryBuilder):
    """Extended HistoryBuilder with timestamp support for intermediate releases.

    Overrides the git env methods to use exact timestamps from CI artifacts
    when the 'timestamp' field is present in a release entry.
    """

    def set_git_env(self, release: dict) -> dict:
        """Set git environment variables for commit author/date.

        Uses 'timestamp' field if present (intermediate working drafts),
        otherwise falls back to date at noon UTC (official releases).
        """
        env = os.environ.copy()
        timestamp = release.get("timestamp")
        if timestamp:
            env["GIT_AUTHOR_DATE"] = timestamp
            env["GIT_COMMITTER_DATE"] = timestamp
        else:
            date = release["date"]
            env["GIT_AUTHOR_DATE"] = f"{date}T12:00:00+00:00"
            env["GIT_COMMITTER_DATE"] = f"{date}T12:00:00+00:00"
        env["GIT_AUTHOR_NAME"] = "OASIS UBL TC"
        env["GIT_AUTHOR_EMAIL"] = "ubl-tc@oasis-open.org"
        env["GIT_COMMITTER_NAME"] = "OASIS UBL TC"
        env["GIT_COMMITTER_EMAIL"] = "ubl-tc@oasis-open.org"
        return env

    def _set_git_env_global(self, release: dict) -> dict:
        """Set git author/date env vars on os.environ so subprocess inherits them.
        Returns the old values for restoration."""
        keys = ['GIT_AUTHOR_DATE', 'GIT_COMMITTER_DATE',
                'GIT_AUTHOR_NAME', 'GIT_AUTHOR_EMAIL',
                'GIT_COMMITTER_NAME', 'GIT_COMMITTER_EMAIL']
        old_vals = {k: os.environ.get(k) for k in keys}

        timestamp = release.get('timestamp')
        if timestamp:
            os.environ['GIT_AUTHOR_DATE'] = timestamp
            os.environ['GIT_COMMITTER_DATE'] = timestamp
        else:
            date = release['date']
            os.environ['GIT_AUTHOR_DATE'] = f'{date}T12:00:00+00:00'
            os.environ['GIT_COMMITTER_DATE'] = f'{date}T12:00:00+00:00'
        os.environ['GIT_AUTHOR_NAME'] = 'OASIS UBL TC'
        os.environ['GIT_AUTHOR_EMAIL'] = 'ubl-tc@oasis-open.org'
        os.environ['GIT_COMMITTER_NAME'] = 'OASIS UBL TC'
        os.environ['GIT_COMMITTER_EMAIL'] = 'ubl-tc@oasis-open.org'
        return old_vals

    def _format_stage(self, release: dict) -> str:
        """Format stage for commit messages.

        Intermediate releases use the full timestamp-based label
        (e.g., pre-csd02-2025-11-17-1042).
        Official releases use the uppercased stage name (e.g., CSD01).
        """
        if release.get("timestamp"):
            label = release["label"]
            suffix = f"-UBL-{release['version']}"
            if label.endswith(suffix):
                return label[:-len(suffix)]
            return label
        return release["stage"].upper()

    def _format_commit_body(self, release: dict) -> str:
        """Format extra commit body lines for source/description metadata."""
        lines = []
        if release.get("source"):
            lines.append(f"Source: {release['source']}")
        if release.get("description"):
            lines.append(f"Change: {release['description']}")
        timestamp = release.get("timestamp")
        if timestamp:
            lines.append(f"Timestamp: {timestamp}")
        return "\n".join(lines)

    def _diff_and_commit(self, old_file, new_file, target_name, old_rel, new_rel):
        """Override to include source/description in commit messages."""
        from gc_diff import GCDiff

        print(f"  Diffing {target_name}...")

        if self.dry_run:
            print(f"    [DRY-RUN] Would compute diff for {target_name}")
            self.commits_created += 1
            return

        differ = GCDiff(str(old_file), str(new_file))
        changes = differ.compute()

        if not changes:
            version = new_rel["version"]
            stage = self._format_stage(new_rel)
            print(f"    {target_name}: No changes from {self._format_stage(old_rel)} - skipping")
            return

        state = GCDiff.parse_file(str(old_file))
        env = self.set_git_env(new_rel)
        version = new_rel["version"]
        stage = self._format_stage(new_rel)
        extra = self._format_commit_body(new_rel)

        for i, change in enumerate(changes, 1):
            state = differ.apply_change(state, change)

            target_path = self.work_dir / target_name
            GCDiff.write_state(state, str(target_path))

            msg = (f"UBL {version} {stage}: {change.description}\n\n"
                   f"Release: {new_rel['label']}\nFile: {target_name}\n"
                   f"Date: {new_rel['date']}")
            if extra:
                msg += f"\n{extra}"
            self.git_add_and_commit(target_name, msg, new_rel, env)

        print(f"    Created {len(changes)} commits for {target_name}")

    def _add_small_file(self, new_file, target_name, release):
        """Override to include source/description in commit messages."""
        if self.dry_run:
            print(f"    [DRY-RUN] Copy {new_file.name} -> {target_name}")
            self.commits_created += 1
            return

        target_path = self.work_dir / target_name
        shutil.copy2(new_file, target_path)

        env = self.set_git_env(release)
        version = release["version"]
        stage = self._format_stage(release)
        extra = self._format_commit_body(release)
        msg = (f"UBL {version} {stage}: Add {target_name}\n\n"
               f"Release: {release['label']}\nDate: {release['date']}")
        if extra:
            msg += f"\n{extra}"
        self.git_add_and_commit(target_name, msg, release, env)

    def build(self, start_at: int = 0) -> None:
        """Build the entire history starting from a specific release index."""
        print("\n" + "=" * 70)
        print("UBL GENERICCODE WORK HISTORY BUILDER")
        print("=" * 70)

        print(f"Processing {len(RELEASES)} releases (35 official + 9 intermediate)...")
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


def main():
    parser = argparse.ArgumentParser(
        description="Build UBL work history from 44 releases (35 official + 9 intermediate)"
    )
    parser.add_argument(
        "--branch",
        default=DEFAULT_BRANCH,
        help=f"Target branch name (default: {DEFAULT_BRANCH})",
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
        "--push",
        action="store_true",
        help="Push the work-history branch to remote after building",
    )
    parser.add_argument(
        "--keep-work-dir",
        action="store_true",
        help="Keep temporary work directory for inspection",
    )

    args = parser.parse_args()

    # Validate that we're in the right place
    if not (REPO_ROOT / "history").exists():
        print(f"Error: Not in ubl-gc repository root")
        print(f"Expected history/ directory at {REPO_ROOT}")
        sys.exit(1)

    if not (REPO_ROOT / "work" / "work-history").exists():
        print(f"Error: Missing work/work-history/ directory")
        print(f"Expected intermediate files at {REPO_ROOT / 'work' / 'work-history'}")
        sys.exit(1)

    print(f"Target branch: {args.branch}")
    print(f"Manifest: work_release_manifest ({len(RELEASES)} releases)")

    work_dir = None
    try:
        work_dir = setup_work_dir(REPO_ROOT, args.branch)

        builder = WorkHistoryBuilder(REPO_ROOT, work_dir, dry_run=args.dry_run)
        builder.build(start_at=args.start_at)

        if not args.dry_run:
            push_results(work_dir, args.branch, do_push=args.push)

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
