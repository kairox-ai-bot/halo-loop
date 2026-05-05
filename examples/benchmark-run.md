# Example: Running a Full Benchmark

This example shows how to run a complete HALO Loop benchmark evaluation using the three comparator modes.

## Prerequisites

- A target agent harness repository (e.g., `my-agent/`)
- Execution traces for each task in the manifests
- The HALO Loop scripts and manifests cloned locally

## Directory Layout

```
benchmark/
├── halo-loop/           # This repo (cloned)
│   ├── scripts/
│   ├── schemas/
│   └── manifests/
├── my-agent/            # Target harness repo
├── traces/              # Trace corpora
│   ├── task_001.jsonl
│   ├── task_002.jsonl
│   └── ...
└── results/             # Output directory
```

## Step 1: Prepare Dev Task Traces

For each task in the dev manifest, ensure you have a trace file:

```bash
# Verify trace readiness for all dev tasks
while IFS= read -r line; do
  task_id=$(echo "$line" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['task_id'])")
  python halo-loop/scripts/trace_validator.py "traces/${task_id}.jsonl" \
    --task-manifest halo-loop/manifests/tasks.dev.jsonl \
    --corpus-id "$task_id" \
    --requires-tools --requires-llm \
    --output "results/readiness_${task_id}.json"
done < halo-loop/manifests/tasks.dev.jsonl
```

## Step 2: Run Redaction Scan on All Traces

```bash
python halo-loop/scripts/redaction_scan.py traces/ \
  --output results/corpus_redaction.json
# Must show: decision: "pass"
```

## Step 3: Capture Baseline

Run your eval command without any HALO modifications:

```bash
cd my-agent
pytest tests/ -v --json results/baseline_eval.json
cd ..
```

Record the baseline score (e.g., 34/60 pass).

## Step 4: Run Three Comparator Modes

For each task, run three modes under identical conditions:

### Mode A: Baseline (no framework)

```bash
# The agent receives no debugging instructions beyond "inspect and improve"
# Run using your agent's default behavior
python run_agent.py \
  --mode baseline \
  --task-manifest halo-loop/manifests/tasks.dev.jsonl \
  --traces traces/ \
  --output-dir results/mode_a/
```

### Mode B: Generic Debugging

```bash
# The agent receives systematic debugging instructions (not HALO-specific)
python run_agent.py \
  --mode generic_debugging \
  --task-manifest halo-loop/manifests/tasks.dev.jsonl \
  --traces traces/ \
  --output-dir results/mode_b/
```

### Mode C: HALO Candidate

```bash
# The agent receives the full HALO Loop skill
python run_agent.py \
  --mode halo_candidate \
  --skill halo-loop/SKILL.md \
  --task-manifest halo-loop/manifests/tasks.dev.jsonl \
  --traces traces/ \
  --output-dir results/mode_c/
```

**Important:** All modes must receive:
- Same repo snapshot (same git SHA)
- Same tasks and traces
- Same eval command
- Same budget (time, cost, tool calls)
- No human steering after mode start

## Step 5: Score Results

```bash
python halo-loop/scripts/score_runs.py \
  'results/*/result_*.json' \
  --task-manifest halo-loop/manifests/tasks.dev.jsonl \
  --primary-partition dev \
  --output results/aggregate_scores.json
```

The scorer outputs:
- Per-mode success rate, regression rate, median cost
- HALO vs stronger control delta
- Bootstrap 95% CI
- Production pass / research-only / fail decision

## Step 6: Review Results

```bash
cat results/aggregate_scores.json | python3 -m json.tool
```

Key fields to check:
- `summary.halo_candidate.success_rate` — HALO's success rate
- `stronger_control` — Which control mode was stronger
- `halo_vs_stronger_delta` — Absolute improvement
- `production_pass` — Whether the statistical rule passed
- `bootstrap_95_ci` — Whether the CI excludes zero

## Step 7: Blinded Adjudication (Secondary Metrics)

For subjective quality metrics, create a blinded pack:

```bash
python halo-loop/scripts/make_blind_adjudication_pack.py \
  results/ \
  --output-dir results/adjudication_pack/ \
  --mapping-output results/PRIVATE_adjudication_mapping.json
```

**Important:** `PRIVATE_adjudication_mapping.json` contains the de-anonymization key. It must NOT be visible to reviewers.

## Key Constraints

- **Budget:** Set explicit limits per run (e.g., 30 min wall clock, $0.12 max cost)
- **No steering:** Once a mode starts, no human intervention until it completes
- **Reproducibility:** Record repo SHA, model version, and seed policy in every run manifest
- **Contamination:** Never open sealed manifests during dev runs. Only open them for the final locked evaluation after skill and scoring are frozen
