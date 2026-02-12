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

## Viewing the History

```bash
# Clone the repository and checkout this branch
git clone https://github.com/kduvekot/ubl-gc.git
cd ubl-gc
git checkout claude/poc-granular-history-bunUn

# See all commits
git log --oneline --graph

# See first 20 commits
git log --oneline -20

# See a specific commit
git show <commit-hash>

# See the file at a specific point
git show <commit-hash>:UBL-Entities.gc

# See what changed in each commit
git log --patch UBL-Entities.gc
```

## Example Commits

The history shows the incremental build process:

```
🌱 Step 1/232: Add leaf ABIE: Address Line. Details
🌱 Step 2/232: Add leaf ABIE: Classification Category. Details
...
🏗️ Step 35/232: Add ABIE+BBIEs: Application Response. Details
...
🔗 Step 134/232: Add ASBIEs: Application Response. Details
```

## Statistics

- **Total commits**: 233 (1 initial + 232 build steps)
- **Total rows added**: 1,604
- **ABIEs**: 133
- **Leaf ABIEs**: 34
- **Non-leaf ABIEs**: 99

## Evolution Potential

If applied to all 35 UBL releases with transitions:
- **~8,120 commits** showing complete evolution
- From UBL 2.0 (2006) to UBL 2.5 (2025)
- Every element addition visible as a commit

---

Built with GitHub Actions
Workflow run: https://github.com/kduvekot/ubl-gc/actions/runs/21961087606
