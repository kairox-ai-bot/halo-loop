# Gate D v2 hard dev corpus report

Date: 2026-05-11
Partition: dev (visible tuning only; not production evidence)
Corpus: `dev_corpus/` — 30 tasks, 10 failure classes × 3 variants
Trace corpus ID: `halo_dev_corpus_v2_hard`

## Validation

- Generator tests: 15/15 passed.
- Baseline validation: 30/30 tasks fail before fixes.
- Trace-required pressure tests: passed — each task has runtime diagnostic signal in `trace.json` not present in source files.
- Locked/private manifests: not opened.

## Gate D v2 result

Aggregate report: `/tmp/halo-loop-eval/gate_d_v2_hard_report.json`

- Baseline: 0/30 = 0%
- Generic debugging: 30/30 = 100%
- HALO candidate: 30/30 = 100%
- Stronger control: generic debugging
- HALO delta vs stronger control: 0pp
- Bootstrap 95% CI: [0pp, 0pp]
- Regression delta: 0pp
- Decision: fail / inconclusive for skill value

## Conclusion

The rebuilt corpus is materially better than v1: multi-file tasks, explicit trace artifacts, baseline fails, and pressure tests pass. But it still does not differentiate the HALO candidate from a strong generic debugging agent. Generic debugging can inspect `TASK.md` and `trace.json` and solve every task.

This is not a production or promotion pass. It is a useful negative result: the benchmark needs a different comparator design or harder tasks where generic debugging cannot simply read the same diagnostic trace and patch directly.

## Recommended next step

Gate D v3 should test HALO-specific value by changing the task format, not merely making bugs multi-file:

1. Hide direct fix hints from `TASK.md` more aggressively.
2. Give generic debugging source + failing eval only; give HALO candidate the validated trace corpus as the treatment, or define a trace-free generic control separately.
3. Add distractor traces and near-miss hypotheses so trace discipline matters.
4. Require diagnosis report quality only as secondary; primary remains mechanical eval success.
5. Re-run with the same 30-task size after freezing comparator access rules.
