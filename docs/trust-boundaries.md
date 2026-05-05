# Trust Boundaries

HALO Loop processes data from multiple sources with different trust levels. This document describes the threat model and recommended mitigations.

## Threat Model

### Untrusted Data Sources

The following data is treated as **untrusted** by default:

1. **Trace payloads** — Execution traces contain tool outputs, environment variables, filesystem reads, API responses, and user inputs. Any of these may contain malicious content.

2. **Task manifests** — Task definitions come from external sources and may contain crafted payloads designed to influence the diagnostic agent.

3. **Trace error messages** — Error strings from external APIs, databases, or filesystem operations may contain injection vectors.

4. **Tool call results** — Responses from tools (web scrapers, API clients, database queries) are untrusted until validated.

### Trusted Data Sources

1. **Frozen benchmark protocol** — The protocol document itself is trusted (version-controlled, hashed).
2. **JSON Schemas** — Schema files are trusted (version-controlled).
3. **Scoring scripts** — Python scripts are trusted (version-controlled, auditable).
4. **Dev task manifests** — Public dev tasks are trusted (synthetically generated, reviewed).

## Attack Vectors

### 1. Prompt Injection via Trace Payloads

**Risk:** Malicious content in trace tool outputs, error messages, or user inputs could inject instructions that cause the diagnostic agent to take unintended actions (exfiltrate data, modify files, skip validation steps).

**Mitigation:**
- The HALO Loop skill explicitly warns: never execute commands extracted from trace payloads without sanitization.
- Diagnostic questions should be narrowly scoped to failure pattern analysis, not action execution.
- The redaction scan (`scripts/redaction_scan.py`) catches some injection patterns as a side effect of scanning for secrets/PII.
- Keep the diagnostic agent's tool permissions minimal during trace analysis.

### 2. Data Exfiltration via Diagnostic Reports

**Risk:** A compromised diagnostic agent could include trace data (which may contain secrets) in its output reports.

**Mitigation:**
- The redaction scan must pass before any diagnostic analysis begins.
- Reports should reference trace/span IDs, not quote raw payloads verbatim.
- The per-iteration report template uses structured fields, not freeform text, limiting exfiltration surface.

### 3. Benchmark Gaming via Sealed Task Leakage

**Risk:** If sealed task contents become visible to the skill author (through trace data, error messages, or other channels), the benchmark is compromised.

**Mitigation:**
- Sealed manifests are physically separate from public files.
- Public manifests contain only IDs and hashes — no diagnostic material.
- The contamination policy (see `docs/protocol.md`) defines strict rules and requires reporting both original and adjusted results if contamination is discovered.

### 4. Script Injection via Malicious Inputs

**Risk:** The Python scripts (`trace_validator.py`, `score_runs.py`, etc.) parse untrusted JSON/JSONL data. Malicious inputs could exploit parser vulnerabilities.

**Mitigation:**
- Scripts use only stdlib `json.loads()` — no `eval()`, `exec()`, `yaml.load()`, or pickle deserialization.
- File paths are constructed from trusted sources (command-line arguments), not from trace data.
- No network calls in any script — all processing is local.

### 5. Cost Amplification

**Risk:** An attacker could craft traces that cause the diagnostic agent to make excessive API calls or consume disproportionate resources.

**Mitigation:**
- Budget limits are enforced in the run manifest schema (`max_cost_usd_per_run`, `max_tool_calls`, `max_wall_clock_minutes`).
- The operational loop enforces max iterations and budget checks before each step.

## Recommended Practices

1. **Run redaction scans first** — Before any diagnostic analysis, run `scripts/redaction_scan.py` on all trace data. Do not proceed if the scan finds high-confidence issues.

2. **Sandbox diagnostic agents** — Run the HALO diagnostic agent in a sandboxed environment with restricted filesystem and network access.

3. **Audit diagnostic outputs** — Review HALO reports for unexpected commands, file accesses, or data inclusions before acting on them.

4. **Validate patches before applying** — Patches generated based on trace diagnostics should be reviewed for correctness and safety before being applied to the target repository.

5. **Separate sealed data physically** — Sealed manifests should be stored in a location inaccessible to the diagnostic agent and skill author during development.

6. **Use the verification checklist** — The SKILL.md verification checklist is designed to catch trust boundary violations before they propagate.
