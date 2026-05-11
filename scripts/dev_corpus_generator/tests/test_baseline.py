"""
RED phase validation: confirm the tasks actually require trace analysis.
A naive approach (grep for obvious patterns) should fail on most tasks.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_naive_code_reading_fails_most_tasks(tmp_path):
    """
    Simulate a naive code-reading approach: grep for 'return False',
    'return {ok: False}', 'raise', etc. If the bug is visible from
    these patterns, the task is too easy.
    """
    from generator import generate_corpus
    from scenarios import get_scenarios
    
    tasks = generate_corpus(get_scenarios(), n_per_class=1, output_dir=tmp_path)
    
    naive_solvable = 0
    for task_dir in tasks:
        # Collect all Python source code
        all_code = ""
        for py in task_dir.glob("*.py"):
            if py.name != "eval_test.py":
                all_code += py.read_text() + "\n"
        
        # Naive patterns that would reveal the bug
        naive_patterns = [
            "return False",
            "return {\"ok\": False}",
            "return {'ok': False}",
            "# BUG",
            "# FIXME",
            "# HACK",
            "# XXX",
        ]
        
        found_naive = False
        for pattern in naive_patterns:
            if pattern in all_code:
                found_naive = True
                break
        
        if found_naive:
            naive_solvable += 1
    
    total = len(tasks)
    assert naive_solvable < total * 0.3, (
        f"{naive_solvable}/{total} tasks solvable by naive grep — "
        f"max allowed is {int(total * 0.3)}. Tasks too easy."
    )


def test_trace_contains_diagnostic_signal_not_in_code(tmp_path):
    """
    For each task, verify that the trace.json contains information
    that is NOT present in any source file. This is the key differentiator.
    """
    from generator import generate_corpus
    from scenarios import get_scenarios
    
    tasks = generate_corpus(get_scenarios(), n_per_class=1, output_dir=tmp_path)
    
    for task_dir in tasks:
        trace = json.loads((task_dir / "trace.json").read_text())
        
        # Collect all source code content
        source_text = ""
        for py in task_dir.glob("*.py"):
            if py.name != "eval_test.py":
                source_text += py.read_text().lower() + "\n"
        
        # Each trace should have at least one span with runtime info
        # not derivable from source alone
        has_hidden_info = False
        for span in trace["spans"]:
            for key in ["tool_output", "actual_return", "actual_tool", "actual_system_prompt",
                        "coerced_value", "is_coroutine", "max_after_reassignment",
                        "field_mismatch", "error_detail", "actual_parent_id", "actual_value"]:
                if key in span:
                    val = str(span[key]).lower()
                    if val and val not in source_text:
                        has_hidden_info = True
                        break
            if has_hidden_info:
                break
        
        assert has_hidden_info, (
            f"{task_dir.name}: trace has no information hidden from source files"
        )


def test_all_evals_fail_at_baseline(tmp_path):
    """All 10 tasks (1 per class) must fail at baseline."""
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
    
    assert failures == len(tasks), f"Only {failures}/{len(tasks)} fail at baseline"
