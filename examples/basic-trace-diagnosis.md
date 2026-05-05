# Example: Basic Trace Diagnosis

This walkthrough shows a single HALO Loop iteration diagnosing a harness failure.

## Setup

You have an agent harness with:
- A failing eval: `pytest tests/ -v` (34/60 pass, 26 fail)
- Execution traces stored in `traces/run_001.jsonl`
- A dev task manifest at `manifests/tasks.dev.jsonl`

## Step 1: Capture Baseline

```bash
pytest tests/ -v > eval_before.json 2>&1
# Record: 34/60 pass, 26 fail
# Save repo hash: git rev-parse HEAD → abc1234
```

## Step 2: Validate Traces

```bash
# Run redaction scan
python scripts/redaction_scan.py traces/run_001.jsonl --output redaction_scan.json
# → pass, 0 findings

# Run trace readiness
python scripts/trace_validator.py traces/run_001.jsonl \
  --task-manifest manifests/tasks.dev.jsonl \
  --redaction-report redaction_scan.json \
  --requires-tools --requires-llm \
  --output trace_readiness.json
# → pass, all thresholds met
```

## Step 3: Diagnose

Ask HALO one narrow question:

```
Across the 26 failed tasks in the trace corpus, identify recurring harness-level
failure modes. For each, cite trace_ids, span names, exact status/error strings,
earliest divergent span versus successes, and whether the likely class is
harness/tool/evaluator/instrumentation/model/external/unknown. Return only
hypotheses supported by trace evidence; mark low-confidence or
insufficient-evidence explicitly.
```

## Step 4: Convert to Hypothesis

HALO returns: "In 18/26 failures, tool calls return empty results despite the
tool reporting success. Affected spans show `status.code: OK` but
`output.value: ""`. Pattern is consistent across file_read and web_search tools.
Likely class: `tool_result_loss`."

Convert to a hypothesis record:

```yaml
hypothesis_id: H1
failure_class: tool_result_loss
claim: Tool result propagation drops non-empty outputs when response exceeds buffer size
evidence:
  - trace_id: tr_042
    span: file_read
    observed: 'status.code: OK, output.value: ""'
  - trace_id: tr_118
    span: web_search
    observed: 'status.code: OK, output.value: ""'
repo_surfaces_to_check:
  - src/harness/tool_result_buffer.py
  - src/harness/serialization.py
confidence: high
counterevidence: 8/26 failures show different patterns (timeout, auth)
proposed_minimal_change: Increase tool result buffer from 4KB to 64KB
expected_eval_effect: 18 previously-failing tasks should now receive tool content and succeed
abort_if: Buffer size is already 64KB or the issue is in the tool itself, not propagation
```

## Step 5: Verify Against Repo

```bash
# Check the actual code
cat src/harness/tool_result_buffer.py
# Confirmed: MAX_BUFFER_SIZE = 4096 (4KB)
# Tool outputs >4KB are silently truncated to empty string
```

Classification: **direct patch candidate** (harness failure confirmed).

## Step 6: Patch

```python
# src/harness/tool_result_buffer.py
# Before:
MAX_BUFFER_SIZE = 4096

# After:
MAX_BUFFER_SIZE = 65536
```

## Step 7: Evaluate

```bash
pytest tests/ -v > eval_after.json 2>&1
# Result: 52/60 pass, 8 fail
# Improvement: +18 tasks passing
# Regressions: 0
```

## Step 8: Decide

- Expected: ~18 previously-failing tasks should pass
- Actual: +18 tasks passing, 0 regressions
- **Decision: KEEP**

## Step 9: Next

8 tasks still failing with different patterns (timeout, auth). Formulate H2 with new evidence from those specific traces.

## Per-Iteration Report

```markdown
## HALO iteration 1

Run IDs: run_001
Repo snapshot: abc1234
Partition: dev
Trace readiness: pass (sha256: f7a3b2...)
Redaction scan: pass (sha256: cc373e...)
Baseline: 34/60 pass
HALO prompt: "Across the 26 failed tasks..."
Hypothesis: H1, tool_result_loss, high confidence
Evidence:
- tr_042 / file_read / status OK but empty output
- tr_118 / web_search / status OK but empty output
Repo verification: tool_result_buffer.py line 12, MAX_BUFFER_SIZE=4096
Patch objective: Increase tool result buffer from 4KB to 64KB
Files changed: src/harness/tool_result_buffer.py (1 LOC)
Eval after: 52/60 pass
Regressions: 0
Decision: keep
Reason: +18 tasks passing matches expected effect, 0 regressions
Stop/next: continue with H2 targeting remaining 8 failures (timeout/auth patterns)
```
```
