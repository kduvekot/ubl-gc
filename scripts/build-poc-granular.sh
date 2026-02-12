#!/bin/bash
set -e

# PoC: Build ultra-granular git history for UBL 2.0 prd
# Creates 232+ commits showing element-by-element evolution

echo "=========================================================================="
echo "PoC: Ultra-Granular Git History Builder"
echo "=========================================================================="
echo ""
echo "This script will:"
echo "  1. Create a new branch: claude/poc-granular-history-bunUn"
echo "  2. Build UBL 2.0 prd incrementally (232+ commits)"
echo "  3. Push to remote for inspection"
echo ""

# Configuration
POC_BRANCH="claude/poc-granular-history-bunUn"
SOURCE_FILE="history/generated/prd-UBL-2.0/mod/UBL-Entities-2.0.gc"
TARGET_FILE="UBL-Entities.gc"

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Check if PoC branch exists
if git rev-parse --verify "$POC_BRANCH" >/dev/null 2>&1; then
    echo ""
    echo "⚠️  Branch $POC_BRANCH already exists!"
    echo "Deleting it to start fresh..."
    git branch -D "$POC_BRANCH" || true
    git push origin --delete "$POC_BRANCH" 2>/dev/null || true
fi

# Create new orphan branch (no history)
echo ""
echo "Creating new orphan branch: $POC_BRANCH"
git checkout --orphan "$POC_BRANCH"

# Remove all files from staging
git rm -rf --cached . 2>/dev/null || true

# Copy essential files
echo ""
echo "Setting up branch structure..."
mkdir -p scripts/lib

# Copy Python scripts
cp scripts/lib/gc_analyzer.py scripts/lib/
cp scripts/lib/gc_builder.py scripts/lib/
cp scripts/lib/gc_commit_builder.py scripts/lib/

# Copy source files we need
cp -r history .

# Create initial README
cat > README.md << 'EOF'
# UBL GenericCode Evolution - Proof of Concept

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

## Total Evolution

If applied to all 35 UBL releases: **~8,120 commits** showing complete evolution from UBL 2.0 (2006) to UBL 2.5 (2025).

---

Built with: https://claude.ai/code/session_01J8Cq8ZxE5GAVoSg2e5LFvK
EOF

# Initial commit
echo ""
echo "Creating initial commit..."
git add README.md scripts/ history/
git commit -m "📋 Initialize PoC: Ultra-granular UBL history

This branch demonstrates building UBL GenericCode files
incrementally with one commit per element addition.

For UBL 2.0 prd: 232 commits showing element-by-element evolution.

https://claude.ai/code/session_01J8Cq8ZxE5GAVoSg2e5LFvK"

# Push initial structure
echo ""
echo "Pushing initial structure..."
git push -u origin "$POC_BRANCH"

# Run the incremental builder
echo ""
echo "=========================================================================="
echo "Building incremental commits..."
echo "=========================================================================="
echo ""

python3 scripts/lib/gc_commit_builder.py "$SOURCE_FILE" "$TARGET_FILE" .

# Push all commits
echo ""
echo "=========================================================================="
echo "Pushing all commits to remote..."
echo "=========================================================================="
echo ""

# Push with retry logic
MAX_RETRIES=4
RETRY_DELAY=2

for i in $(seq 1 $MAX_RETRIES); do
    if git push origin "$POC_BRANCH"; then
        echo "✓ Push successful!"
        break
    else
        if [ $i -lt $MAX_RETRIES ]; then
            echo "Push failed, retrying in ${RETRY_DELAY}s..."
            sleep $RETRY_DELAY
            RETRY_DELAY=$((RETRY_DELAY * 2))
        else
            echo "❌ Push failed after $MAX_RETRIES attempts"
            exit 1
        fi
    fi
done

# Show summary
echo ""
echo "=========================================================================="
echo "✓ PoC BUILD COMPLETE!"
echo "=========================================================================="
echo ""
echo "Branch: $POC_BRANCH"
echo ""
echo "View the history:"
echo "  git log --oneline --graph"
echo ""
echo "View on GitHub:"
echo "  gh browse --branch $POC_BRANCH"
echo ""
echo "Return to original branch:"
echo "  git checkout $CURRENT_BRANCH"
echo ""
