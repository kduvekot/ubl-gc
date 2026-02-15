#!/usr/bin/env python3
"""One command to run the next needed step.

Usage:
    export GOOGLE_ACCESS_TOKEN="ya29.a0..."
    python3 scripts/run.py
"""
import os, sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

def main():
    token = os.environ.get("GOOGLE_ACCESS_TOKEN", "")
    if not token:
        print("ERROR: Set GOOGLE_ACCESS_TOKEN first.")
        print("  1. Visit https://developers.google.com/oauthplayground/")
        print("  2. Authorize scope: https://www.googleapis.com/auth/drive.readonly")
        print("  3. export GOOGLE_ACCESS_TOKEN='ya29.a0...'")
        sys.exit(1)

    discovery = ROOT / ".claude" / "swap" / "drive-discovery.json.gz"
    exports_dir = ROOT / "revision-exports"
    manifest = exports_dir / "manifest.json"

    # Step 1: Discovery
    if not discovery.exists():
        print("=== Step 1: Discovering Google Drive contents ===")
        r = subprocess.run([sys.executable, "scripts/discover-drive-history.py"], cwd=ROOT)
        if r.returncode != 0:
            sys.exit(r.returncode)
        print("\nDone! Re-run this script to continue to Step 2.")
        return

    # Step 2: Download revision content
    # Check manifest has actual downloads (not just an empty/failed run)
    manifest_ok = False
    if manifest.exists():
        import json
        try:
            m = json.loads(manifest.read_text())
            manifest_ok = m.get("stats", {}).get("total_revisions_downloaded", 0) > 0
        except (json.JSONDecodeError, KeyError):
            pass
    if not manifest_ok:
        print("=== Step 2: Downloading revision content ===")
        print(f"  Discovery data: {discovery}")
        r = subprocess.run([sys.executable, "scripts/fetch-revision-content.py", "--resume"], cwd=ROOT)
        if r.returncode != 0:
            sys.exit(r.returncode)
        print("\nDone! The tar.gz and swap copy were created automatically.")
        print("Now commit and push:")
        print("  git add .claude/swap/revision-exports.tar.gz")
        print("  git commit -m 'Step 2: Google Sheets revision exports'")
        print("  git push -u origin claude/google-sheets-history-cQ6AV")
        return

    # Step 3: Test files.download endpoint (PoC for revision-specific content)
    poc_result = ROOT / ".claude" / "swap" / "poc-revision-download.txt"
    if not poc_result.exists():
        print("=== Step 3: PoC — testing files.download with revisionId ===")
        print("  Previous approach (files.export) returned identical data for all revisions.")
        print("  Testing files.download (POST) which officially supports revisionId for Sheets.")
        print()
        poc_result.parent.mkdir(parents=True, exist_ok=True)
        with open(poc_result, "w") as f:
            r = subprocess.run(
                [sys.executable, "scripts/test-revision-download.py"],
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            output = r.stdout
            f.write(output)
            print(output)
        print(f"\n  Output saved to: {poc_result}")
        print("\nDone! Upload results:")
        print(f"  git add {poc_result.relative_to(ROOT)}")
        print("  git commit -m 'Step 3: PoC revision download test results'")
        print("  git push -u origin claude/google-sheets-history-cQ6AV")
        return

    # Step 4: Download ODS for key revisions (using v2 exportLinks — proven by PoC)
    ods_manifest = ROOT / ".claude" / "swap" / "revision-ods" / "manifest.json"
    ods_tar = ROOT / ".claude" / "swap" / "revision-ods.tar.gz"
    ods_ok = False
    if ods_manifest.exists():
        import json as _json
        try:
            m = _json.loads(ods_manifest.read_text())
            ods_ok = m.get("stats", {}).get("total_ok", 0) > 0
        except (json.JSONDecodeError, KeyError):
            pass
    if not ods_ok:
        print("=== Step 4: Download ODS for key revisions ===")
        print("  Using Drive API v2 exportLinks (proven by PoC in Step 3).")
        print("  Downloads 10 ODS files: 4 library + 6 documents revisions.")
        print("  These map to the 10 workflow-generated GC versions (V1-V10).")
        print()
        r = subprocess.run(
            [sys.executable, "scripts/download-revision-ods.py"],
            cwd=ROOT
        )
        if r.returncode != 0:
            sys.exit(r.returncode)
        print()
        print("Done! Now commit and push the results:")
        print("  git add .claude/swap/revision-ods.tar.gz")
        print("  git commit -m 'Step 4: ODS exports for key revisions'")
        print("  git push -u origin claude/google-sheets-history-cQ6AV")
        return

    # All done
    print("=== All steps complete ===")
    print(f"  Step 1 - Discovery:    {discovery}")
    print(f"  Step 2 - Bulk exports: {exports_dir}")
    print(f"  Step 3 - PoC test:     {poc_result}")
    print(f"  Step 4 - ODS revisions:{ods_tar}")
    print()
    print("ODS files ready for Crane ODS→GC conversion.")

if __name__ == "__main__":
    main()
