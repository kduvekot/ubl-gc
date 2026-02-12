#!/usr/bin/env python3
"""
PoC: Ultra-Granular Git History Builder

Creates a proof-of-concept branch showing UBL 2.0 prd built incrementally
with 232+ commits (one per element addition).
"""

import subprocess
import sys
import os
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

from gc_analyzer import GCAnalyzer
from gc_builder import GCBuilder
from gc_commit_builder import GCCommitBuilder


def run_command(cmd, cwd='.', check=True):
    """Run a shell command"""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True
    )
    if check and result.returncode != 0:
        print(f"Command failed: {cmd}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def main():
    print("="*70)
    print("PoC: Ultra-Granular Git History Builder")
    print("="*70)
    print()

    # Configuration
    POC_BRANCH = "claude/poc-granular-history-bunUn"
    SOURCE_FILE = "history/generated/prd-UBL-2.0/mod/UBL-Entities-2.0.gc"
    TARGET_FILE = "UBL-Entities.gc"

    # Get current branch
    current_branch = run_command("git branch --show-current")
    print(f"Current branch: {current_branch}")

    # Check if PoC branch exists and delete it
    branch_exists = run_command(f"git rev-parse --verify {POC_BRANCH}", check=False)
    if branch_exists:
        print(f"\n⚠️  Branch {POC_BRANCH} already exists - deleting...")
        run_command(f"git branch -D {POC_BRANCH}", check=False)
        run_command(f"git push origin --delete {POC_BRANCH}", check=False)

    # Create new branch from current HEAD
    print(f"\nCreating new branch: {POC_BRANCH}")
    run_command(f"git checkout -b {POC_BRANCH}")

    # Create README
    print("\nCreating README...")
    readme_content = """# UBL GenericCode Evolution - Proof of Concept

This branch demonstrates **ultra-granular git history** for UBL semantic model evolution.

## What is this?

A proof-of-concept showing UBL 2.0 PRD built incrementally:
- **232 commits** for one release
- Each commit adds one element (ABIE, BBIE, or ASBIE)
- File is valid XML at every commit
- No forward references

## Build Strategy

**Phase 1: Leaf ABIEs (34 commits)**
- Add ABIEs with no dependencies
- Complete with all BBIEs and ASBIEs

**Phase 2: Non-leaf ABIEs + BBIEs (99 commits)**
- Add ABIEs with dependencies
- Include BBIEs only (defer ASBIEs)

**Phase 3: ASBIEs (99 commits)**
- Add deferred ASBIEs
- All references now valid

## Viewing the History

```bash
# See all commits
git log --oneline --graph

# See a specific commit
git show <commit-hash>

# See diff between commits
git diff <commit1> <commit2>
```

## Total Evolution

If applied to all 35 UBL releases: **~8,120 commits** showing complete evolution from UBL 2.0 (2006) to UBL 2.5 (2025).

---

Built with: https://claude.ai/code/session_01J8Cq8ZxE5GAVoSg2e5LFvK
"""

    Path("README-POC.md").write_text(readme_content)
    run_command("git add README-POC.md")
    run_command('git commit -m "📋 Initialize PoC: Ultra-granular UBL history\n\nThis branch demonstrates building UBL GenericCode files\nincrementally with one commit per element addition.\n\nhttps://claude.ai/code/session_01J8Cq8ZxE5GAVoSg2e5LFvK"')

    # Push initial commit
    print("\nPushing initial commit...")
    run_command(f"git push -u origin {POC_BRANCH}")

    # Analyze source file
    print("\n" + "="*70)
    print("ANALYZING SOURCE FILE")
    print("="*70)

    analyzer = GCAnalyzer(SOURCE_FILE)
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

    commit_builder = GCCommitBuilder(SOURCE_FILE, TARGET_FILE, '.')

    # Create initial empty file
    print("\nCreating initial empty GenericCode file...")
    commit_builder.create_empty_gc_file()
    commit_builder._git_add_and_commit("📋 Initialize empty GenericCode file structure")

    # Build incrementally
    commit_builder.build_incremental(steps)

    # Push all commits
    print("\n" + "="*70)
    print("PUSHING TO REMOTE")
    print("="*70)

    for retry in range(4):
        try:
            run_command(f"git push origin {POC_BRANCH}")
            print("\n✓ Push successful!")
            break
        except:
            if retry < 3:
                delay = 2 ** retry
                print(f"\nPush failed, retrying in {delay}s...")
                import time
                time.sleep(delay)
            else:
                print("\n❌ Push failed after 4 attempts")
                return

    # Summary
    print("\n" + "="*70)
    print("✓ PoC BUILD COMPLETE!")
    print("="*70)
    print(f"\nBranch: {POC_BRANCH}")
    print(f"\nView commits:")
    print(f"  git log --oneline --graph {POC_BRANCH}")
    print(f"\nReturn to original branch:")
    print(f"  git checkout {current_branch}")


if __name__ == '__main__':
    main()
