#!/bin/bash
set -e

# PoC: Build ABIE-level git history for UBL 2.0 PRD
# Creates ~131 commits showing ABIE-by-ABIE evolution
#
# Each commit adds one complete ABIE group (ABIE + BBIEs + ASBIEs)
# in topological dependency order (Tarjan's SCC algorithm).
#
# This script is for local testing. The workflow version runs in CI.

echo "=========================================================================="
echo "PoC: ABIE-Level Git History Builder"
echo "=========================================================================="
echo ""
echo "This script will:"
echo "  1. Create a new orphan branch: claude/poc-abie-history-wsfi6"
echo "  2. Build UBL 2.0 PRD incrementally (~131 commits)"
echo "  3. Push to remote for inspection"
echo ""

# Configuration
POC_BRANCH="claude/poc-abie-history-wsfi6"
SOURCE_FILE="history/generated/prd-UBL-2.0/mod/UBL-Entities-2.0.gc"
TARGET_FILE="UBL-Entities.gc"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Verify source file exists
if [ ! -f "$REPO_ROOT/$SOURCE_FILE" ]; then
    echo "ERROR: Source file not found: $SOURCE_FILE"
    exit 1
fi

# Save current branch
CURRENT_BRANCH=$(git -C "$REPO_ROOT" branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Check if PoC branch exists
if git -C "$REPO_ROOT" rev-parse --verify "$POC_BRANCH" >/dev/null 2>&1; then
    echo ""
    echo "Branch $POC_BRANCH already exists! Deleting to start fresh..."
    git -C "$REPO_ROOT" branch -D "$POC_BRANCH" || true
fi

# Create orphan branch
echo ""
echo "Creating new orphan branch: $POC_BRANCH"
cd "$REPO_ROOT"
git checkout --orphan "$POC_BRANCH"
git rm -rf --cached . 2>/dev/null || true

# Configure git for this session
git config user.name "OASIS UBL TC"
git config user.email "ubl-tc@oasis-open.org"

# Restore source files from the previous branch
echo "Restoring source files..."
git checkout "$CURRENT_BRANCH" -- "$SOURCE_FILE"
git checkout "$CURRENT_BRANCH" -- scripts/lib/gc_analyzer.py
git checkout "$CURRENT_BRANCH" -- scripts/lib/gc_builder.py
git checkout "$CURRENT_BRANCH" -- scripts/lib/gc_commit_builder.py

# Create README
cat > README.md << 'EOF'
# UBL GenericCode Evolution - Proof of Concept (ABIE-Level)

This branch demonstrates **ABIE-level git history** for UBL semantic model evolution.

Each commit adds one complete ABIE (with all its BBIEs and ASBIEs)
in dependency order, ensuring the file is valid at every step.

Built with: https://claude.ai/code/session_01B5kfoVeuncQaSCz9nX4H1j
EOF

git add README.md
git commit -m "Initialize PoC: ABIE-level UBL history

https://claude.ai/code/session_01B5kfoVeuncQaSCz9nX4H1j"

# Run the ABIE-level builder
echo ""
echo "=========================================================================="
echo "Building ABIE-level commits..."
echo "=========================================================================="
echo ""

PYTHONPATH="$REPO_ROOT/scripts/lib" python3 "$REPO_ROOT/scripts/lib/gc_commit_builder.py" \
    "$SOURCE_FILE" "$TARGET_FILE" .

# Push with retry
echo ""
echo "=========================================================================="
echo "Pushing commits to remote..."
echo "=========================================================================="
echo ""

MAX_RETRIES=4
RETRY_DELAY=2

for i in $(seq 1 $MAX_RETRIES); do
    if git push -u origin "$POC_BRANCH" --force; then
        echo "Push successful!"
        break
    else
        if [ $i -lt $MAX_RETRIES ]; then
            echo "Push failed, retrying in ${RETRY_DELAY}s..."
            sleep $RETRY_DELAY
            RETRY_DELAY=$((RETRY_DELAY * 2))
        else
            echo "Push failed after $MAX_RETRIES attempts"
            # Return to original branch before exiting
            git checkout "$CURRENT_BRANCH" 2>/dev/null || true
            exit 1
        fi
    fi
done

# Summary
COMMIT_COUNT=$(git rev-list --count HEAD)
echo ""
echo "=========================================================================="
echo "PoC BUILD COMPLETE!"
echo "=========================================================================="
echo ""
echo "Branch:  $POC_BRANCH"
echo "Commits: $COMMIT_COUNT"
echo ""
echo "View the history:"
echo "  git log --oneline --graph"
echo ""
echo "Return to original branch:"
echo "  git checkout $CURRENT_BRANCH"
echo ""
