# Glossary

## Terms

**Agent harness**
The tool wrappers, eval harnesses, prompt orchestration, tracing layer, and infrastructure that sit between an LLM and its tasks. Includes retry logic, context construction, tool serialization, and evaluation pipelines.

**Baseline**
The eval score captured before any HALO-driven changes. Frozen at the start of each iteration.

**Bootstrap CI**
A confidence interval estimated by resampling paired observations with replacement. Used in `score_runs.py` to compute the 95% CI for the HALO-control delta.

**Comparator mode**
One of three experimental conditions: baseline (no framework), generic debugging (systematic debugging without HALO), or HALO candidate (full HALO Loop skill).

**Contamination**
Any exposure of sealed task content to the skill author before locked evaluation. Contaminated tasks cannot support a production pass.

**Dev partition**
Visible tasks used for developing and tuning the skill. Tasks may influence skill text.

**Failure class**
A category from the HALO failure taxonomy: `tool_schema_mismatch`, `tool_result_loss`, `retry_loop`, `timeout_retry_gap`, `context_bloat`, `missing_semantic_constraint`, `state_leakage`, `ordering_instability`, `evaluator_bug`, `trace_artifact`, `model_capability`, `external_dependency`, or `unknown`.

**HALO**
Hypothesis-Anchored Loop for Observation. The trace-diagnostic methodology implemented by this skill.

**Hypothesis**
A single, falsifiable claim about a harness failure mode, supported by trace evidence and predicting a specific eval movement. One hypothesis per iteration.

**Keep/revert decision**
A mechanical, binary decision made after each iteration: keep the patch if it produces the pre-stated metric improvement, or revert it if it doesn't. Not subjective.

**Locked partition**
Sealed tasks used for final evaluation. Not visible to the skill author until after the skill and scoring protocol are frozen. Includes synthetic and realistic sub-partitions.

**Primary endpoint**
Task success rate on locked realistic tasks. The main metric for production acceptance.

**Production-grade pass**
When the HALO candidate meets all seven statistical conditions on locked realistic tasks: sufficient power, ≥10pp improvement over stronger control, positive 95% CI, ≤5pp regression increase, ≤20% cost increase (or ≥15pp success gain), no contamination, no post-hoc exclusions.

**Redaction gate**
A mandatory scan using `scripts/redaction_scan.py` that checks for secrets, PII, and other sensitive data in trace corpora. Must pass before diagnostic analysis.

**Research partition**
Visible tasks used for learning HALO mechanics. Cannot directly influence skill text.

**Research-only result**
When the powered N threshold is not met but directional improvement is observed. Can justify further evaluation but cannot install a production skill.

**Sealed manifest**
A task manifest whose private form (containing task text, expected fixes) is hidden from the skill author. Public forms contain only IDs and hashes.

**Span**
A single observation in an execution trace, representing one unit of work (LLM call, tool invocation, agent action, etc.).

**Trace**
A collection of spans representing one complete agent execution. Stored as JSONL with one JSON object per span.

**Trace readiness**
The set of thresholds that trace data must meet before it can be used for HALO analysis. Validated by `scripts/trace_validator.py`.
