"""RED: Failing tests for corpus generator."""
import pytest
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_generator_produces_correct_count(tmp_path):
    """Generator must produce n_per_class × n_classes task directories."""
    from generator import generate_corpus
    from scenarios import get_scenarios
    scenarios = get_scenarios()
    tasks = generate_corpus(scenarios, n_per_class=3, output_dir=tmp_path)
    assert len(tasks) == 30
    for t in tasks:
        assert t.is_dir()


def test_each_task_has_required_files(tmp_path):
    """Each task dir must have harness.py, trace.json, TASK.md, eval_test.py."""
    from generator import generate_corpus
    from scenarios import get_scenarios
    tasks = generate_corpus(get_scenarios(), n_per_class=1, output_dir=tmp_path)
    for task_dir in tasks:
        assert (task_dir / "harness.py").exists(), f"Missing harness.py in {task_dir.name}"
        assert (task_dir / "trace.json").exists(), f"Missing trace.json in {task_dir.name}"
        assert (task_dir / "TASK.md").exists(), f"Missing TASK.md in {task_dir.name}"
        assert (task_dir / "eval_test.py").exists(), f"Missing eval_test.py in {task_dir.name}"


def test_trace_json_is_valid(tmp_path):
    """trace.json must be valid JSON with spans."""
    from generator import generate_corpus
    from scenarios import get_scenarios
    tasks = generate_corpus(get_scenarios(), n_per_class=1, output_dir=tmp_path)
    for task_dir in tasks:
        trace = json.loads((task_dir / "trace.json").read_text())
        assert "spans" in trace
        assert len(trace["spans"]) >= 3


def test_task_md_mentions_trace(tmp_path):
    """TASK.md must reference trace analysis (not just code reading)."""
    from generator import generate_corpus
    from scenarios import get_scenarios
    tasks = generate_corpus(get_scenarios(), n_per_class=1, output_dir=tmp_path)
    for task_dir in tasks:
        content = (task_dir / "TASK.md").read_text().lower()
        assert "trace" in content or "span" in content, (
            f"{task_dir.name}: TASK.md doesn't reference trace analysis"
        )


def test_evals_fail_at_baseline(tmp_path):
    """All eval tests must FAIL before any fixes (RED phase)."""
    from generator import generate_corpus
    from scenarios import get_scenarios
    tasks = generate_corpus(get_scenarios(), n_per_class=1, output_dir=tmp_path)
    failures = 0
    for task_dir in tasks:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(task_dir / "eval_test.py"), "-v"],
            capture_output=True, text=True, timeout=10,
            cwd=str(task_dir),
        )
        if result.returncode != 0:
            failures += 1
        else:
            print(f"UNEXPECTED PASS: {task_dir.name}")
            print(result.stdout[-200:])
    assert failures == len(tasks), (
        f"Only {failures}/{len(tasks)} failed — some tasks pass at baseline"
    )


def test_supporting_files_included(tmp_path):
    """Multi-file scenarios must have their supporting files in the task dir."""
    from generator import generate_corpus
    from scenarios import get_scenarios
    tasks = generate_corpus(get_scenarios(), n_per_class=1, output_dir=tmp_path)
    for task_dir in tasks:
        py_files = list(task_dir.glob("*.py"))
        # At minimum: harness.py + eval_test.py + at least one supporting file
        assert len(py_files) >= 3, (
            f"{task_dir.name}: only {len(py_files)} .py files, expected >= 3"
        )
