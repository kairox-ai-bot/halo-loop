# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 1.0.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in HALO Loop, please report it responsibly:

- **Email:** philip@kairoxai.live
- **Response time:** We aim to acknowledge reports within 48 hours and provide an initial assessment within 5 business days.

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigations

### Scope

Security issues specifically in:
- Trace data handling and sanitization
- Redaction scan bypasses
- Sealed manifest leakage vectors
- Script injection via trace payloads

### Out of scope

- Issues in dependencies (report to upstream)
- Theoretical attacks without concrete reproduction
- Issues in tools or frameworks that HALO Loop integrates with but does not control

## Trust Boundaries

HALO Loop processes untrusted data (execution traces, task payloads). See [`docs/trust-boundaries.md`](docs/trust-boundaries.md) for the full threat model and recommended mitigations.
