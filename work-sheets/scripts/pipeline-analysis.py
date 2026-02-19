#!/usr/bin/env python3
"""Pipeline: download and diff ODS revisions concurrently.

Downloads revision ODS files from Google Drive while simultaneously
running semantic diffs on already-downloaded pairs. Overlaps I/O-bound
downloads with CPU-bound diffs, and splits diffs into parallel chunks.

Architecture:
  1. Download starts (10 thread workers) → writes manifest.txt immediately
  2. Diff workers start as soon as manifest exists
  3. Each diff worker processes its chunk sequentially (with parse caching)
  4. Diff workers poll for files with --wait (2s interval, 10 min timeout)
  5. Pair JSON files written to shared output dir (no filename collisions)
  6. After all workers finish, merge per-chunk summaries into one

Usage:
    python3 pipeline-analysis.py library
    python3 pipeline-analysis.py documents --diff-workers 4
    python3 pipeline-analysis.py library --download-dir /tmp/ods --diff-dir /tmp/diffs
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Pipelined download + parallel diff of ODS revisions"
    )
    parser.add_argument(
        "sheet", choices=["library", "documents"],
        help="Which sheet to process"
    )
    parser.add_argument(
        "--diff-workers", type=int, default=2,
        help="Number of parallel diff chunk processes (default: 2)"
    )
    parser.add_argument(
        "--download-dir", type=str, default=None,
        help="Where to store downloaded ODS files (default: /tmp/ubl-revisions/{sheet})"
    )
    parser.add_argument(
        "--diff-dir", type=str, default=None,
        help="Where to write diff JSON results (default: /tmp/diff-results/{sheet})"
    )
    parser.add_argument(
        "--text-only", action="store_true", default=True,
        help="Ignore formulas in diff (default: true)"
    )
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    dl_dir = Path(args.download_dir) if args.download_dir else Path(f"/tmp/ubl-revisions/{args.sheet}")
    diff_dir = Path(args.diff_dir) if args.diff_dir else Path(f"/tmp/diff-results/{args.sheet}")
    dl_dir.mkdir(parents=True, exist_ok=True)
    diff_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"Pipeline Analysis: {args.sheet}")
    print("=" * 70)
    print(f"  Download dir:  {dl_dir}")
    print(f"  Diff output:   {diff_dir}")
    print(f"  Diff workers:  {args.diff_workers}")
    print(f"  Text-only:     {args.text_only}")
    print()

    t_start = time.time()

    # ── Phase 1: Start download in background ─────────────────────────
    download_cmd = [
        sys.executable, str(script_dir / "download-drive-revisions.py"),
        "--sheet", args.sheet, "--all", "--output", str(dl_dir),
    ]
    print(f"[pipeline] Starting download...")
    dl_proc = subprocess.Popen(
        download_cmd,
        stdout=sys.stdout, stderr=sys.stderr,
    )

    # Wait for manifest (written by download script after folder listing)
    manifest = dl_dir / "manifest.txt"
    print(f"[pipeline] Waiting for manifest...", end="", flush=True)
    t0 = time.time()
    while not manifest.exists():
        if time.time() - t0 > 120:
            print(" TIMEOUT (120s)")
            dl_proc.kill()
            sys.exit(1)
        time.sleep(0.5)

    revs = sorted(
        int(line.strip())
        for line in manifest.read_text().splitlines()
        if line.strip()
    )
    print(f" {len(revs)} revisions in {time.time() - t0:.1f}s")

    # ── Phase 2: Start diff workers in parallel chunks ────────────────
    n_workers = min(args.diff_workers, max(1, len(revs) - 1))
    chunk_size = len(revs) // n_workers

    diff_procs = []
    for i in range(n_workers):
        start_idx = i * chunk_size
        if i == n_workers - 1:
            # Last chunk gets everything remaining
            chunk_revs = revs[start_idx:]
        else:
            # +1 overlap: include last rev as start of next pair
            chunk_revs = revs[start_idx : (i + 1) * chunk_size + 1]

        if len(chunk_revs) < 2:
            continue

        range_str = f"{chunk_revs[0]}-{chunk_revs[-1]}"

        diff_cmd = [
            sys.executable, str(script_dir / "diff-ods-revisions.py"),
            str(dl_dir),
            "--streaming",
            "--manifest", str(manifest),
            "--range", range_str,
            "--wait",
            "--output-dir", str(diff_dir),
        ]
        if args.text_only:
            diff_cmd.append("--text-only")

        print(f"[pipeline] Diff chunk {i}: range {range_str} "
              f"({len(chunk_revs)} revs, {len(chunk_revs) - 1} pairs)")
        diff_procs.append(subprocess.Popen(
            diff_cmd,
            stdout=sys.stdout, stderr=sys.stderr,
        ))

    # ── Phase 3: Wait for everything to finish ────────────────────────
    dl_exit = dl_proc.wait()
    t_dl = time.time() - t_start
    print(f"\n[pipeline] Download finished in {t_dl:.0f}s (exit {dl_exit})")

    diff_exits = []
    for i, p in enumerate(diff_procs):
        rc = p.wait()
        diff_exits.append(rc)
        print(f"[pipeline] Diff chunk {i} finished (exit {rc})")

    t_total = time.time() - t_start

    # ── Phase 4: Merge per-chunk summaries ────────────────────────────
    # Each chunk writes its own summary.json with overlapping names, but we
    # actually don't need to merge — the pair-*.json files have unique names
    # and the streaming function writes a summary.json that each chunk
    # overwrites. Let's rebuild the summary from all pair files.
    pair_files = sorted(diff_dir.glob("pair-*.json"))
    print(f"\n[pipeline] Total pair files: {len(pair_files)}")

    # Build merged summary
    total_transitions = 0
    identical_count = 0
    style_only_count = 0
    changed_count = 0
    total_cell_changes = 0
    total_user_edits = 0
    col_events = []
    row_events = []
    errors = []

    for pf in pair_files:
        try:
            with open(pf) as f:
                p = json.load(f)
            total_transitions += 1
            n = p.get("num_changes", 0)
            soc = p.get("style_only_count", 0)
            hcs = p.get("has_col_structure", False)
            hrs = p.get("has_row_structure", False)

            if n == 0 and soc == 0 and not hcs and not hrs:
                identical_count += 1
            elif n == 0 and soc > 0 and not hcs and not hrs:
                style_only_count += 1
            else:
                changed_count += 1
                total_cell_changes += n
                total_user_edits += p.get("summary", {}).get(
                    "by_category", {}).get("user_edit", 0)
                if hcs:
                    cc = p.get("column_changes", {})
                    col_events.append({
                        "from": p["from_rev"], "to": p["to_rev"],
                        "added": cc.get("added", []),
                        "removed": cc.get("removed", []),
                        "unnamed_added": cc.get("unnamed_added", 0),
                        "unnamed_removed": cc.get("unnamed_removed", 0),
                    })
                if hrs:
                    rc = p.get("row_changes", {})
                    row_events.append({
                        "from": p["from_rev"], "to": p["to_rev"],
                        "added": rc.get("added_count", 0),
                        "removed": rc.get("removed_count", 0),
                    })
        except Exception as e:
            errors.append({"file": pf.name, "error": str(e)})

    summary = {
        "input_dir": str(dl_dir),
        "mode": "pipeline",
        "text_only": args.text_only,
        "diff_workers": n_workers,
        "revision_range": [revs[0], revs[-1]] if revs else [],
        "total_revisions": len(revs),
        "total_transitions": total_transitions,
        "identical_transitions": identical_count,
        "style_only_transitions": style_only_count,
        "changed_transitions": changed_count,
        "total_cell_changes": total_cell_changes,
        "total_user_edits": total_user_edits,
        "col_structure_events": col_events,
        "row_structure_events": row_events,
        "errors": errors,
        "timing": {
            "download_seconds": round(t_dl, 1),
            "total_seconds": round(t_total, 1),
        },
    }

    summary_path = diff_dir / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # ── Final report ──────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)
    print(f"  Revisions:      {len(revs)}")
    print(f"  Transitions:    {total_transitions}")
    print(f"  Identical:      {identical_count}")
    print(f"  Style-only:     {style_only_count}")
    print(f"  Changed:        {changed_count}")
    print(f"  Cell changes:   {total_cell_changes}")
    print(f"  User edits:     {total_user_edits}")
    print(f"  Errors:         {len(errors)}")
    print(f"  Download time:  {t_dl:.0f}s")
    print(f"  Total time:     {t_total:.0f}s")
    print(f"  Pair files:     {len(pair_files)}")
    print(f"  Summary:        {summary_path}")
    print("=" * 70)

    # Exit with error if any subprocess failed
    if dl_exit != 0 or any(rc != 0 for rc in diff_exits):
        print(f"\nWARNING: Some processes had non-zero exit codes")
        print(f"  Download: {dl_exit}")
        for i, rc in enumerate(diff_exits):
            print(f"  Diff {i}: {rc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
