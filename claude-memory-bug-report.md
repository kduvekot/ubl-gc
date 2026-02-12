# Claude Memory Tool - Bug Report

**Date:** 2026-02-12
**Repository:** kduvekot/ubl-gc
**Branch:** claude/git-history-exploration-bunUn
**Tool Version:** From https://raw.githubusercontent.com/sipico/swap/main/claude-memory.zip

---

## Summary

The `claude-memory` tool works for most commands but has issues with:
1. Output piping (BrokenPipeError)
2. JSON parsing when combining with stderr redirects

---

## Working Commands ✅

### 1. `topics` - Works perfectly
```bash
.claude/scripts/claude-memory topics
```
**Output:** Valid JSON array with 19 session files
**Status:** ✅ Success

### 2. `tokens` - Works perfectly
```bash
.claude/scripts/claude-memory tokens
```
**Output:** Valid JSON with usage statistics:
```json
{
  "api_calls": 11955,
  "models": ["claude-haiku-4-5-20251001", "claude-sonnet-4-5-20250929"],
  "tokens": {
    "input": 301994,
    "output": 26759,
    "cache_write_5m": 0,
    "cache_write_1h": 19064047,
    "cache_read": 625377650
  },
  "tokens_total": 644770450,
  "cost_usd": {
    "input": 0.302,
    "output": 0.1338,
    "cache_write_5m": 0.0,
    "cache_write_1h": 38.1281,
    "cache_read": 62.5378,
    "total": 101.1016
  }
}
```
**Status:** ✅ Success

### 3. `conversation --user-only --last 50` - Works
```bash
.claude/scripts/claude-memory conversation --user-only --last 50 > /tmp/user-messages.json
```
**Output:** Valid JSON array (1002 lines)
**Status:** ✅ Success

---

## Problematic Commands ❌

### Issue #1: BrokenPipeError with piped output

**Command:**
```bash
.claude/scripts/claude-memory search "Option K" | head -50
```

**Error:**
```
BrokenPipeError: [Errno 32] Broken pipe
```

**Full Traceback:**
```python
Traceback (most recent call last):
  File "/home/user/ubl-gc/.claude/scripts/claude-memory", line 418, in <module>
    main()
  File "/home/user/ubl-gc/.claude/scripts/claude-memory", line 410, in main
    cmd_search(" ".join(positional))
  File "/home/user/ubl-gc/.claude/scripts/claude-memory", line 200, in cmd_search
    _json_out({"query": query, "count": len(hits), "matches": hits})
  File "/home/user/ubl-gc/.claude/scripts/claude-memory", line 174, in _json_out
    print(json.dumps(data, indent=2))
BrokenPipeError: [Errno 32] Broken pipe
```

**Context:**
- The `search` command found 85 matches
- Started outputting JSON
- `head -50` closed the pipe after reading 50 lines
- Python script didn't handle the closed pipe gracefully

**Expected Behavior:**
- Should catch `BrokenPipeError` and exit cleanly (similar to how `grep` handles SIGPIPE)

**Workaround:**
```bash
# This works without error:
.claude/scripts/claude-memory search "Option K" > /tmp/results.json
head -50 /tmp/results.json
```

---

### Issue #2: JSON parsing fails with stderr redirect

**Command:**
```bash
.claude/scripts/claude-memory search "agreed" 2>/dev/null | python3 -c "import json, sys; d=json.load(sys.stdin); print(f\"Found {d['count']} matches\")"
```

**Error:**
```python
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Context:**
- When stderr is redirected, the tool seems to output nothing to stdout
- The JSON parser receives empty input

**Workaround:**
```bash
# This works:
.claude/scripts/claude-memory search "agreed" > /tmp/search.json 2>&1
cat /tmp/search.json | python3 -c "import json, sys; ..."
```

---

### Issue #3: No helpful output when tool fails silently

**Command:**
```bash
.claude/scripts/claude-memory search "agreed" 2>/dev/null
```

**Output:** (nothing - empty)

**Expected:** Either valid JSON or an error message

---

## Environment Details

```bash
Python Version: 3.11
OS: Linux 4.4.0
Shell: bash

# Session details
Project: /home/user/ubl-gc
Sessions Found: 19 .jsonl files
Total Tokens: 644,770,450
Estimated Cost: $101.10 USD
```

---

## Suggested Fixes

### Fix #1: Handle BrokenPipeError gracefully

```python
def _json_out(data) -> None:
    try:
        print(json.dumps(data, indent=2))
    except BrokenPipeError:
        # Pipe closed early (e.g., piped to head)
        # This is normal - exit cleanly
        import sys
        sys.exit(0)
```

### Fix #2: Always output to stdout, even with stderr redirects

Ensure the tool doesn't suppress stdout when stderr is redirected.

### Fix #3: Add error handling for empty results

```python
def cmd_search(query: str) -> None:
    query_lower = query.lower()
    hits = [e for e in parse_all(include_tool_results=True)
            if query_lower in e["text"].lower()]

    result = {"query": query, "count": len(hits), "matches": hits}

    if not hits:
        # Add a helpful message for empty results
        result["note"] = "No matches found"

    _json_out(result)
```

---

## Test Cases for Validation

### Test 1: Pipe to head (should not error)
```bash
.claude/scripts/claude-memory search "test" | head -10
# Expected: Clean exit, no BrokenPipeError
```

### Test 2: Stderr redirect (should output JSON)
```bash
.claude/scripts/claude-memory search "test" 2>/dev/null
# Expected: Valid JSON on stdout
```

### Test 3: Empty results (should be valid JSON)
```bash
.claude/scripts/claude-memory search "xyznonexistentquery"
# Expected: {"query": "xyznonexistentquery", "count": 0, "matches": [], "note": "No matches found"}
```

### Test 4: Large output with pipe (stress test)
```bash
.claude/scripts/claude-memory conversation | head -100
# Expected: Clean exit, no errors
```

---

## Overall Assessment

**Tool Quality:** 🌟🌟🌟🌟⭐ (4/5)

**Strengths:**
- ✅ Excellent JSON output structure
- ✅ Fast parsing of JSONL files
- ✅ Comprehensive data extraction
- ✅ Good filtering options (--last, --user-only, --truncate)
- ✅ Token cost tracking is very useful

**Weaknesses:**
- ❌ Doesn't handle pipe breakage gracefully
- ❌ Unclear behavior with stderr redirects
- ⚠️  No progress indicator for large searches

**Use Case Fit:**
This tool is **excellent** for recovering session context after compression. The issues are minor edge cases that don't affect core functionality.

---

## Additional Notes

### Successful Use Cases During Testing:

1. **Session Overview** - Worked perfectly
   ```bash
   .claude/scripts/claude-memory topics
   ```

2. **Cost Tracking** - Excellent visibility into API usage
   ```bash
   .claude/scripts/claude-memory tokens
   ```

3. **Targeted Search** - Found 85 matches for "Option K"
   ```bash
   .claude/scripts/claude-memory search "Option K" > results.json
   ```

4. **Recent Context** - Last 50 user messages retrieved successfully
   ```bash
   .claude/scripts/claude-memory conversation --user-only --last 50
   ```

### Integration with Claude Code

The tool integrates well with Claude Code workflows:
- Placed in `.claude/scripts/` directory
- Executable permissions set correctly
- Reads from `~/.claude/projects/` automatically
- No configuration needed

---

## Contact

**Tested by:** Claude (Sonnet 4.5)
**Session ID:** claude/git-history-exploration-bunUn
**Repository:** https://github.com/kduvekot/ubl-gc

**For tool author:** This is excellent work! The core functionality is solid. The pipe handling issue is a minor Python quirk that's easy to fix. Would love to see this tool become a standard part of Claude Code! 🙌
