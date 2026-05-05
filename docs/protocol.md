# HALO Loop Benchmark Protocol

This document specifies the benchmark protocol for evaluating the HALO Loop skill. The protocol is frozen — changes require a new version and invalidate prior locked-test exposure.

## 1. Frozen Claim

The HALO candidate skill may be accepted only if it improves:

> **Per-task success probability of an agent harness on realistic locked-test tasks, compared with the stronger of baseline and generic-debugging controls under identical budgets.**

Primary endpoint is task success on realistic locked tasks. Synthetic tasks, evidence quality, and report polish are secondary.

## 2. Dataset Partitions and Leakage Controls

| Partition | Purpose | Visibility | Can affect skill text? |
|-----------|---------|------------|----------------------|
| research | learn HALO mechanics/source behavior | visible now | no direct examples copied |
| dev/tuning | refine scripts and candidate draft | visible | yes |
| locked synthetic | final controlled failure test | sealed until skill + scoring frozen | no |
| locked realistic | primary endpoint | sealed until skill + scoring frozen | no |
| internal | rollout only | after benchmark pass | no benchmark role |

### Contamination Rules

A locked task is contaminated if any of these occur before locked execution:

- task text, expected fix, trace corpus, evaluator, or failure class is visible to skill author;
- task is generated from a prompt visible to skill author and not randomized by sealed script/person;
- task shares exact code/evaluator with a dev task except via intentionally versioned harness template;
- HALO/coding-agent transcript includes the answer before scoring;
- manual exclusion happens after seeing mode outcomes.

Contaminated locked tasks are replaced before freeze. If contamination is discovered after execution, report both original and contamination-adjusted results; contaminated tasks cannot support pass.

## 3. Benchmark Composition

- Synthetic dev: 30 tasks across ≥5 failure classes
- Synthetic locked: 50 tasks across ≥5 failure classes
- Realistic dev: 30 tasks across ≥3 harnesses
- Realistic locked: minimum 80 tasks, target 150+, across ≥3 harnesses

Sealed locked manifests contain only IDs/hashes in their public form. Private manifests contain task text/expected fixes and remain sealed until locked execution.

## 4. Comparator Modes

All modes receive the same repo snapshot, task, trace corpus, eval command, tools, context budget, wall-clock budget, retry budget, common run rules, and no-human-steering rule.

### Mode A — Baseline

Receives no debugging framework beyond "inspect traces and improve harness."

### Mode B — Generic Debugging

Receives systematic debugging discipline, but no HALO-specific trace workflow and no HALO-specific prompt library.

### Mode C — HALO Candidate

Receives the HALO candidate skill text plus the same constraints as other modes. The candidate skill file hash is recorded in every run manifest. A missing or mismatched hash invalidates the run.

## 5. Run Protocol

For each task/mode/seed:

1. Start from clean repo snapshot.
2. Run baseline eval; store `eval_before.json`.
3. Validate trace corpus with `scripts/trace_validator.py`; fail task if trace readiness fails.
4. Run the assigned mode under frozen budget.
5. Save transcript, diagnosis, patch, and run manifest.
6. Run targeted tests if mode changed code.
7. Run full eval; store `eval_after.json`.
8. Score mechanically with `scripts/score_runs.py`.
9. Build blind adjudication pack for secondary metrics only.
10. Keep/revert decision is determined by mechanical eval and threshold, not subjective review.

No human steering after mode start. Infra failures are handled by the exclusion policy before outcomes are inspected.

## 6. Trace Readiness Gate

Implemented by `scripts/trace_validator.py`. Task manifest and redaction report are mandatory for benchmark runs.

Required thresholds:

| Check | Threshold |
|-------|-----------|
| JSONL parse success | 100% |
| Required top-level span fields | 100% |
| `schema_version == 1` | 100% |
| `project_id` present | 100% |
| `observation_kind` valid | 100% |
| Parent link validity | ≥99% |
| Timestamp validity | ≥99.5% |
| Status code present | 100% |
| Task-trace join | ≥98% |
| Tool reconstruction | ≥95% |
| LLM span visibility | ≥95% |
| Error visibility | ≥95% |
| Token/cost visibility | ≥90% |
| Redaction findings | zero high-confidence |

## 7. Privacy/Security Protocol

Implemented by `scripts/redaction_scan.py`. Any high-confidence secret or personal data finding quarantines the corpus.

Prohibited:
- personal account data
- customer/user PII
- secrets/tokens/cookies/passwords
- production traces unless separately approved

No upload to third-party tracing backends without approval.

## 8. Statistical Decision Rule

### Production-Grade Pass

All must hold:

1. Locked realistic tasks have sufficient N for 80% power to detect 10pp absolute improvement at alpha 0.05 under paired/repeated design, or the project lead explicitly approves a reduced power claim labeled beta-only.
2. HALO candidate beats the stronger control by ≥10pp absolute success on locked realistic tasks.
3. 95% CI lower bound for HALO-control delta > 0.
4. Regression rate increase ≤5pp.
5. Median cost increase ≤20%, unless success gain ≥15pp.
6. No holdout contamination.
7. Gains are not driven by post-hoc exclusions.

### Research-Only Result

If powered N is not reached, HALO can only justify more evaluation if:

- directional improvement on realistic locked tasks;
- no regression/cost blowup;
- evidence discipline improves;
- no contamination.

Research-only evidence cannot install a production skill.

## 9. Blinded Adjudication

Implemented by `scripts/make_blind_adjudication_pack.py`.

Subjective metrics (evidence quality, diagnosis clarity, root-cause plausibility, patch appropriateness) are secondary only. Blinding requirements:

1. Strip mode labels from reports and patches.
2. Randomize IDs.
3. Reviewer cannot be skill author.
4. Reviewer sees task, trace excerpts, diagnosis, patch, eval outcome; not mode.
5. If blinding fails, subjective scores become qualitative notes only.
