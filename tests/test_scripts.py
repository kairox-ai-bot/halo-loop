#!/usr/bin/env python3
"""Smoke tests for HALO Loop scripts.

Run with: python -m pytest tests/ -v

No external dependencies — uses only stdlib.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
MANIFESTS_DIR = Path(__file__).resolve().parent.parent / "manifests"
SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


def run_script(script_name, args, cwd=None):
    """Run a script and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script_name)] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.stdout, result.stderr, result.returncode


class TestRedactionScan(unittest.TestCase):
    """Test scripts/redaction_scan.py"""

    def test_clean_file_passes(self):
        """A file with no sensitive data should pass."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello world\nThis is fine\n")
            f.flush()
            try:
                stdout, stderr, rc = run_script("redaction_scan.py", [f.name, "--output", os.devnull])
                self.assertEqual(rc, 0, f"Expected pass but got rc={rc}\nstdout={stdout}\nstderr={stderr}")
            finally:
                os.unlink(f.name)

    def test_secret_quarantines(self):
        """A file with an API key should quarantine."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write('api_key = "sk-abc123def456ghi789jkl012mno345"\n')
            f.flush()
            try:
                stdout, stderr, rc = run_script("redaction_scan.py", [f.name, "--output", os.devnull])
                self.assertNotEqual(rc, 0, "Expected non-zero rc for quarantined file")
            finally:
                os.unlink(f.name)

    def test_medium_only_passes_with_flag(self):
        """Medium-severity findings pass with --allow-medium."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Contact: user@example.com\n")
            f.flush()
            try:
                # Without flag: should quarantine (medium)
                stdout, stderr, rc = run_script("redaction_scan.py", [f.name, "--output", os.devnull])
                self.assertNotEqual(rc, 0, "Expected quarantine for medium finding without flag")
                # With flag: should pass
                stdout, stderr, rc = run_script("redaction_scan.py", [f.name, "--allow-medium", "--output", os.devnull])
                self.assertEqual(rc, 0, f"Expected pass with --allow-medium but got rc={rc}")
            finally:
                os.unlink(f.name)

    def test_output_json_valid(self):
        """Output should be valid JSON with required fields."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("clean content\n")
            out_path = f.name + ".scan.json"
            f.flush()
            try:
                run_script("redaction_scan.py", [f.name, "--output", out_path])
                with open(out_path) as result:
                    data = json.load(result)
                self.assertIn("decision", data)
                self.assertIn("findings", data)
                self.assertIn("files_scanned", data)
                self.assertEqual(data["decision"], "pass")
            finally:
                os.unlink(f.name)
                if os.path.exists(out_path):
                    os.unlink(out_path)


class TestTraceValidator(unittest.TestCase):
    """Test scripts/trace_validator.py"""

    def _make_trace(self, spans):
        """Write spans as JSONL to a temp file, return path."""
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        for span in spans:
            f.write(json.dumps(span) + "\n")
        f.close()
        return f.name

    def _valid_span(self, **overrides):
        """Create a minimal valid trace span."""
        span = {
            "trace_id": "tr001",
            "span_id": "sp001",
            "parent_span_id": "",
            "trace_state": "ok",
            "name": "test_span",
            "kind": "SPAN",
            "start_time": "2026-01-01T00:00:00Z",
            "end_time": "2026-01-01T00:00:01Z",
            "status": {"code": "OK"},
            "resource": {},
            "scope": {},
            "attributes": {
                "inference.export.schema_version": 1,
                "inference.project_id": "test_project",
                "inference.observation_kind": "SPAN",
            },
        }
        span.update(overrides)
        return span

    def test_valid_traces_pass(self):
        """Valid traces with required fields and a task manifest should pass."""
        trace_path = self._make_trace([
            self._valid_span(
                attributes={
                    "inference.export.schema_version": 1,
                    "inference.project_id": "test_project",
                    "inference.observation_kind": "SPAN",
                    "task.id": "test_task_001",
                }
            )
        ])
        # Create a matching task manifest so task_trace_join can succeed
        manifest_path = trace_path + ".manifest.jsonl"
        with open(manifest_path, "w") as f:
            f.write(json.dumps({
                "task_id": "test_task_001",
                "partition": "dev",
                "source": "test",
                "harness": "test_harness",
                "known_to_skill_author": True,
                "eval_command": "echo ok",
                "trace_corpus_id": "test_corpus",
                "content_sha256": "abc",
                "evaluator_sha256": "def",
                "contamination_notes": "",
            }) + "\n")
        out_path = trace_path + ".readiness.json"
        try:
            stdout, stderr, rc = run_script("trace_validator.py", [
                trace_path,
                "--task-manifest", manifest_path,
                "--dev-allow-missing-gates",
                "--output", out_path,
            ])
            self.assertEqual(rc, 0, f"Expected pass but got rc={rc}\nstdout={stdout}\nstderr={stderr}")
            with open(out_path) as f:
                data = json.load(f)
            self.assertEqual(data["decision"], "pass")
        finally:
            os.unlink(trace_path)
            os.unlink(manifest_path)
            if os.path.exists(out_path):
                os.unlink(out_path)

    def test_invalid_json_fails(self):
        """Traces with invalid JSON should fail."""
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        f.write("not json\n")
        f.close()
        out_path = f.name + ".readiness.json"
        try:
            stdout, stderr, rc = run_script("trace_validator.py", [
                f.name,
                "--dev-allow-missing-gates",
                "--output", out_path,
            ])
            self.assertEqual(rc, 2, "Expected fail for invalid JSON")
        finally:
            os.unlink(f.name)
            if os.path.exists(out_path):
                os.unlink(out_path)

    def test_missing_gates_fails_without_dev_flag(self):
        """Without --dev-allow-missing-gates, missing task manifest should fail."""
        trace_path = self._make_trace([self._valid_span()])
        try:
            stdout, stderr, rc = run_script("trace_validator.py", [trace_path])
            self.assertEqual(rc, 2, "Expected fail without dev flag")
            self.assertIn("missing_task_manifest", stdout)
        finally:
            os.unlink(trace_path)


class TestScoreRuns(unittest.TestCase):
    """Test scripts/score_runs.py"""

    def _make_manifest(self, tasks):
        """Write tasks as JSONL manifest."""
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        for t in tasks:
            f.write(json.dumps(t) + "\n")
        f.close()
        return f.name

    def test_no_results_fails(self):
        """No result files should cause graceful failure."""
        manifest_path = self._make_manifest([
            {"task_id": "t1", "partition": "locked_realistic", "source": "test",
             "harness": "h1", "known_to_skill_author": False, "eval_command": "echo",
             "trace_corpus_id": "c1", "content_sha256": "abc", "evaluator_sha256": "def",
             "contamination_notes": ""}
        ])
        try:
            stdout, stderr, rc = run_script("score_runs.py", [
                "/nonexistent/path/*.json",
                "--task-manifest", manifest_path,
            ])
            # Should fail (no results)
            self.assertNotEqual(rc, 0, "Expected non-zero rc with no results")
        finally:
            os.unlink(manifest_path)


class TestMakeBlindAdjudicationPack(unittest.TestCase):
    """Test scripts/make_blind_adjudication_pack.py"""

    def test_empty_dir_produces_empty_pack(self):
        """An empty runs directory should produce an empty adjudication pack."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runs_dir = os.path.join(tmpdir, "runs")
            os.makedirs(runs_dir)
            out_dir = os.path.join(tmpdir, "pack")
            mapping_path = os.path.join(tmpdir, "mapping.json")
            stdout, stderr, rc = run_script("make_blind_adjudication_pack.py", [
                runs_dir,
                "--output-dir", out_dir,
                "--mapping-output", mapping_path,
            ])
            self.assertEqual(rc, 0, f"Expected success but got rc={rc}\nstderr={stderr}")
            with open(mapping_path) as f:
                data = json.load(f)
            self.assertEqual(len(data), 0, "Expected empty mapping for empty dir")


class TestSchemasExist(unittest.TestCase):
    """Verify all expected schemas exist and are valid JSON."""

    def test_run_manifest_schema(self):
        path = SCHEMAS_DIR / "run_manifest.schema.json"
        self.assertTrue(path.exists(), f"Missing schema: {path}")
        data = json.loads(path.read_text())
        self.assertEqual(data["type"], "object")

    def test_task_manifest_schema(self):
        path = SCHEMAS_DIR / "task_manifest.schema.json"
        self.assertTrue(path.exists(), f"Missing schema: {path}")
        data = json.loads(path.read_text())
        self.assertEqual(data["type"], "object")


class TestManifestsValid(unittest.TestCase):
    """Verify manifest files are valid JSONL."""

    def test_dev_manifest(self):
        path = MANIFESTS_DIR / "tasks.dev.jsonl"
        self.assertTrue(path.exists(), "Missing dev manifest")
        lines = [l for l in path.read_text().splitlines() if l.strip()]
        self.assertGreater(len(lines), 0, "Dev manifest is empty")
        for i, line in enumerate(lines):
            data = json.loads(line)
            self.assertIn("task_id", data, f"Line {i+1}: missing task_id")

    def test_research_manifest(self):
        path = MANIFESTS_DIR / "tasks.research.jsonl"
        self.assertTrue(path.exists(), "Missing research manifest")
        lines = [l for l in path.read_text().splitlines() if l.strip()]
        self.assertGreater(len(lines), 0, "Research manifest is empty")
        for i, line in enumerate(lines):
            data = json.loads(line)
            self.assertIn("task_id", data, f"Line {i+1}: missing task_id")


if __name__ == "__main__":
    unittest.main()
