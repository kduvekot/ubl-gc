# UBL GenericCode Evolution - Proof of Concept (ABIE-Level)

This branch demonstrates **ABIE-level git history** for UBL semantic model evolution.

## What is this?

A proof-of-concept showing UBL 2.0 PRD built incrementally:
- **~131 commits** for one release (1 skeleton + 130 ABIE groups)
- Each commit adds one complete ABIE (with all its BBIEs and ASBIEs)
- File is valid GenericCode XML at every commit
- No forward references (topologically sorted using Tarjan's SCC algorithm)
- One cycle group (4 mutually dependent ABIEs committed together)

## Build Strategy

ABIEs are added in **dependency order** (leaves first, documents last):

1. **Skeleton** - Empty GenericCode file with header and column definitions
2. **Leaf ABIEs** - ABIEs with no external dependencies (Address Line, Country, etc.)
3. **Dependent ABIEs** - ABIEs that reference others (topologically sorted)
4. **Cycle group** - Mutually dependent ABIEs committed together (Despatch Line + Receipt Line + Shipment + Transport Handling Unit)
5. **Document ABIEs** - Top-level documents (Invoice, Order, etc.)

## Statistics

| Metric | Count |
|--------|-------|
| Total commits | ~131 |
| Total rows | 1,604 |
| ABIEs | 133 |
| BBIEs | 848 |
| ASBIEs | 623 |
| Cycle groups | 1 (4 ABIEs) |
| Self-referencing ABIEs | 5 |

## Commit Message Format

```
UBL 2.0 PRD [42/130]: Add "Party"

ABIE: Party
Components: 3 BBIEs, 9 ASBIEs
Total rows: 13
```

---

Built with GitHub Actions
