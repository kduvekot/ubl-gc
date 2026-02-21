#!/usr/bin/env python3
"""
UBL GenericCode Git History Orchestrator

Processes all 35 UBL releases and creates git commits showing the complete
evolution of UBL GenericCode semantic models.

Strategy:
1. First release (UBL 2.0 PRD): Generate empty skeleton, then diff against
   full source to create ABIE-by-ABIE commits via the unified diff engine.
2. Subsequent releases: Use gc_diff to compute changes, create commits per change.
3. New files (Signature/Endorsed): Same skeleton+diff approach as first release.
4. File types: Track Entities, Signature-Entities, Endorsed-Entities separately.
5. Versioning: Files in history branch use versioned names matching OASIS originals:
   - UBL-Entities-{version}.gc
   - UBL-Signature-Entities-{version}.gc
   - UBL-Endorsed-Entities-{version}.gc
6. Version transitions use git mv to preserve file provenance.
"""

import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional
import argparse

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

from release_manifest import RELEASES, get_release_pairs
from gc_diff import GCDiff, GCFileState

DEFAULT_BRANCH = "history"


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
    def get_target_name(file_type: str, version: str) -> str:
        """Get the versioned target filename for a file type.

        Preserves the original OASIS naming convention with version numbers.
        At version transitions, git mv is used to rename the file.
        """
        if file_type == "entities":
            return f"UBL-Entities-{version}.gc"
        elif file_type == "signature":
            return f"UBL-Signature-Entities-{version}.gc"
        elif file_type == "endorsed":
            return f"UBL-Endorsed-Entities-{version}.gc"
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

        # Check if there's actually anything staged to commit
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=self.work_dir,
            capture_output=True,
        )
        if result.returncode == 0:
            # Nothing staged — skip this commit
            print(f"    Skipping no-op commit: {message.splitlines()[0]}")
            return

        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.work_dir,
            check=True,
            capture_output=True,
            env=env,
        )
        self.commits_created += 1


    def git_commit_staged(self, message: str, release: dict, env: dict) -> None:
        """Commit whatever is already staged (used after git rm)."""
        if self.dry_run:
            print(f"  [DRY-RUN] git commit: {message.splitlines()[0]}")
            return

        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.work_dir,
            check=True,
            capture_output=True,
            env=env,
        )
        self.commits_created += 1

    def git_mv_and_commit(
        self, old_name: str, new_name: str, release: dict, env: dict
    ) -> None:
        """Rename a file using git mv and commit the rename."""
        if self.dry_run:
            print(f"  [DRY-RUN] git mv {old_name} {new_name}")
            print(f"  [DRY-RUN] git commit: Rename {old_name} -> {new_name}")
            self.commits_created += 1
            return

        subprocess.run(
            ["git", "mv", old_name, new_name],
            cwd=self.work_dir,
            check=True,
            capture_output=True,
        )

        version = release["version"]
        stage = release["stage"].upper()
        msg = (f"UBL {version} {stage}: Rename {old_name} to {new_name}\n\n"
               f"Release: {release['label']}\nDate: {release['date']}")
        self.git_commit_staged(msg, release, env)

    def _generate_empty_skeleton(self, source_file: Path) -> Path:
        """Generate an empty .gc skeleton from a source file.

        Extracts the header (everything before first <Row>) and footer
        (everything after last </Row>), producing a valid .gc file with
        no data rows. If the source has no rows, the whole file is
        returned as the skeleton header.

        Returns:
            Path to the temporary skeleton file.
        """
        with open(source_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()

        # Find first <Row> and last </Row>
        first_row = None
        last_row_end = None
        for i, line in enumerate(all_lines):
            stripped = line.strip()
            if first_row is None and (stripped.startswith('<Row>') or stripped.startswith('<Row ')):
                first_row = i
            if stripped == '</Row>':
                last_row_end = i

        if first_row is None:
            # No rows — file is already "empty"
            header = all_lines
            footer = []
        else:
            header = all_lines[:first_row]
            footer = all_lines[last_row_end + 1:]

        # Write skeleton to a temp file
        skeleton_path = Path(tempfile.mktemp(suffix='.gc', prefix='skeleton-'))
        with open(skeleton_path, 'w', encoding='utf-8') as f:
            for line in header:
                f.write(line)
            for line in footer:
                f.write(line)

        return skeleton_path

    def _add_via_skeleton_diff(
        self, source_file: Path, target_name: str, release: dict
    ) -> None:
        """Add a new file by diffing an empty skeleton against the source.

        Creates a skeleton commit, then uses _diff_and_commit() to add
        all ABIEs one-by-one in dependency order — the same code path
        used for all transitions.
        """
        print(f"  Adding via skeleton diff: {target_name}")

        if self.dry_run:
            print(f"    [DRY-RUN] Would create skeleton + diff commits for {target_name}")
            self.commits_created += 100  # Rough estimate
            return

        # Generate empty skeleton
        skeleton_path = self._generate_empty_skeleton(source_file)
        try:
            # Write skeleton to work dir and commit it
            target_path = self.work_dir / target_name
            shutil.copy2(skeleton_path, target_path)

            env = self.set_git_env(release)
            version = release["version"]
            stage = release["stage"].upper()
            msg = (f"UBL {version} {stage}: Initialize {target_name}\n\n"
                   f"Empty file with header, column definitions, and "
                   f"empty SimpleCodeList.\n\n"
                   f"Release: {release['label']}\nDate: {release['date']}")
            self.git_add_and_commit(target_name, msg, release, env)

            # Now diff skeleton against full source — produces ABIE-by-ABIE commits
            self._diff_and_commit(
                skeleton_path, source_file, target_name, release, release
            )
        finally:
            skeleton_path.unlink(missing_ok=True)

    def process_first_release(self, release: dict) -> None:
        """Process the first release (UBL 2.0 PRD) via skeleton + diff.

        Creates an empty skeleton, then diffs against the full source
        file, producing one commit per ABIE in dependency order.
        """
        print(f"\nProcessing first release: {release['label']}")
        print("=" * 70)

        source_file = self.get_source_path(release, "entities")
        if source_file is None:
            raise ValueError(f"No entities file for {release['label']}")

        target_name = self.get_target_name("entities", release["version"])
        self._add_via_skeleton_diff(source_file, target_name, release)

    def process_transition(self, old_rel: dict, new_rel: dict) -> None:
        """Process a transition between two releases.

        For each file type (entities, signature, endorsed):
        - If file didn't exist before but exists now: add it
        - If file existed before and exists now: compute diff and create commits
        - If file existed before but doesn't exist now: remove it
        - If both are None: skip

        At version transitions (e.g. 2.0->2.1), uses git mv to rename the
        versioned file before applying content changes.
        """
        rel_label = f"{old_rel['label']} -> {new_rel['label']}"
        print(f"\nProcessing: {rel_label}")
        print("=" * 70)

        is_version_change = old_rel["version"] != new_rel["version"]

        for file_type in ["entities", "signature", "endorsed"]:
            old_file = self.get_source_path(old_rel, file_type)
            new_file = self.get_source_path(new_rel, file_type)
            old_target = self.get_target_name(file_type, old_rel["version"])
            new_target = self.get_target_name(file_type, new_rel["version"])

            if old_file is None and new_file is None:
                continue

            elif old_file is None and new_file is not None:
                self._add_new_file(new_file, new_target, new_rel)

            elif old_file is not None and new_file is None:
                self._remove_file(old_target, new_rel)

            else:
                # If version changed, rename file first to preserve provenance
                if is_version_change:
                    env = self.set_git_env(new_rel)
                    self.git_mv_and_commit(
                        old_target, new_target, new_rel, env
                    )

                self._diff_and_commit(
                    old_file, new_file, new_target, old_rel, new_rel
                )

    def _add_new_file(
        self, new_file: Path, target_name: str, release: dict
    ) -> None:
        """Add a new file via skeleton + diff (unified approach for all file sizes)."""
        print(f"  Adding new file: {target_name}")
        self._add_via_skeleton_diff(new_file, target_name, release)

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
            # No changes - skip commit (file is identical to previous release)
            version = new_rel["version"]
            stage = new_rel["stage"].upper()
            print(f"    {target_name}: No changes from {old_rel['stage'].upper()} - skipping")
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


def setup_work_dir(repo_root: Path, branch_name: str) -> Path:
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
        ["git", "checkout", "--orphan", branch_name],
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

    # Set remote URL to the source repo's origin (so push goes to the right place)
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            remote_url = result.stdout.strip()
            subprocess.run(
                ["git", "remote", "set-url", "origin", remote_url],
                cwd=work_dir,
                check=True,
                capture_output=True,
            )
            # Copy GitHub Actions auth config if present
            auth_result = subprocess.run(
                ["git", "config", "--get", "http.https://github.com/.extraheader"],
                cwd=repo_root,
                capture_output=True,
                text=True,
            )
            if auth_result.returncode == 0 and auth_result.stdout.strip():
                subprocess.run(
                    ["git", "config", "http.https://github.com/.extraheader",
                     auth_result.stdout.strip()],
                    cwd=work_dir,
                    check=True,
                    capture_output=True,
                )
    except subprocess.CalledProcessError:
        pass  # Non-critical, push instructions will still work

    print(f"Created orphan branch: {branch_name}")

    return work_dir


def push_results(work_dir: Path, branch_name: str, do_push: bool = False) -> None:
    """Push the history branch to remote (or print instructions)."""
    if do_push:
        print("\n" + "=" * 70)
        print("PUSHING TO REMOTE")
        print("=" * 70)
        for attempt in range(4):
            try:
                result = subprocess.run(
                    ["git", "push", "-u", "origin", branch_name, "--force"],
                    cwd=work_dir,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                print(f"Successfully pushed to {branch_name}")
                return
            except subprocess.CalledProcessError as e:
                if attempt < 3:
                    delay = 2 ** (attempt + 1)
                    print(f"Push failed, retrying in {delay}s... ({e.stderr.strip()})")
                    import time
                    time.sleep(delay)
                else:
                    print(f"Push failed after 4 attempts: {e.stderr.strip()}")
                    raise
    else:
        print("\n" + "=" * 70)
        print("PUSH INSTRUCTIONS")
        print("=" * 70)
        print(f"\nTo push the history branch, run:")
        print(f"  git -C {work_dir} push -u origin {branch_name} --force")
        print(f"\nOr manually:")
        print(f"  cd {work_dir}")
        print(f"  git push -u origin {branch_name} --force")


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
        help="Push the history branch to remote after building",
    )
    parser.add_argument(
        "--keep-work-dir",
        action="store_true",
        help="Keep temporary work directory for inspection",
    )

    args = parser.parse_args()

    # Find repo root: go up from scripts/ to repository root
    script_file = Path(__file__).resolve()
    repo_root = script_file.parent.parent

    # Validate that we're in the right place
    if not (repo_root / "history").exists():
        print(f"Error: Not in ubl-gc repository root")
        print(f"Expected history/ directory at {repo_root}")
        print(f"Script location: {script_file}")
        sys.exit(1)

    print(f"Target branch: {args.branch}")

    work_dir = None
    try:
        work_dir = setup_work_dir(repo_root, args.branch)

        builder = HistoryBuilder(repo_root, work_dir, dry_run=args.dry_run)
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
