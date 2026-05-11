"""
Scenario definitions for HALO Loop dev corpus.
Each scenario represents a realistic agent harness failure that requires
trace-level diagnosis — the bug is invisible from reading any single file.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class SourceFile:
    path: str
    content: str


@dataclass
class Scenario:
    failure_class: str
    bug_description: str
    files: List[SourceFile]
    trace_spans: List[Dict[str, Any]]
    fix_description: str


def get_scenarios() -> List[Scenario]:
    return [
        Scenario(
            failure_class="wrong_tool_binding",
            bug_description=(
                "The agent's tool registry maps the model's 'search_database' call to "
                "a 'query_cache' function instead. The harness code correctly registers "
                "both tools, but the binding order in the adapter causes the wrong function "
                "to execute. The model's output is correct, the tool exists, but the trace "
                "shows a different tool's return value than what was requested."
            ),
            files=[
                SourceFile(
                    path="tool_registry.py",
                    content="""class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name, func):
        self._tools[name] = func

    def get(self, name):
        return self._tools.get(name)

    def execute(self, name, **kwargs):
        tool = self.get(name)
        if tool is None:
            return {"error": f"Tool {name} not found"}
        return tool(**kwargs)
""",
                ),
                SourceFile(
                    path="adapter.py",
                    content="""from tool_registry import ToolRegistry

def search_database(query, filters=None):
    results = [{"id": 1, "name": "Product A", "price": 29.99}]
    if filters:
        results = [r for r in results if all(r.get(k) == v for k, v in filters.items())]
    return {"results": results, "count": len(results)}

def query_cache(query):
    return {"cached": True, "data": [], "source": "cache"}

class AgentAdapter:
    def __init__(self):
        self.registry = ToolRegistry()
        self.registry.register("query_cache", query_cache)
        self.registry.register("search_database", query_cache)

    def dispatch(self, model_output):
        tool_name = model_output["tool_calls"][0]["function"]["name"]
        arguments = model_output["tool_calls"][0]["function"]["arguments"]
        return self.registry.execute(tool_name, **arguments)
""",
                ),
                SourceFile(
                    path="harness.py",
                    content="""from adapter import AgentAdapter

def run_query(user_query):
    adapter = AgentAdapter()
    model_output = {
        "tool_calls": [{
            "function": {
                "name": "search_database",
                "arguments": {"query": user_query}
            }
        }]
    }
    result = adapter.dispatch(model_output)
    return result
""",
                ),
            ],
            trace_spans=[
                {"span_id": "s1", "type": "model_call", "model_output": {"tool_calls": [{"function": {"name": "search_database", "arguments": {"query": "laptop"}}}]}},
                {"span_id": "s2", "type": "tool_dispatch", "requested_tool": "search_database", "actual_tool": "query_cache", "tool_output": {"cached": True, "data": [], "source": "cache"}},
                {"span_id": "s3", "type": "result", "returned_to_model": {"cached": True, "data": [], "source": "cache"}},
            ],
            fix_description="Fix the binding order in adapter.py so search_database maps to the search_database function, not query_cache.",
        ),

        Scenario(
            failure_class="prompt_schema_mismatch",
            bug_description=(
                "The prompt builder constructs messages using 'content' as the field for "
                "tool results, but the schema validator expects 'output'. The harness "
                "passes validation because the validator only checks top-level structure, "
                "not the tool-result field naming convention. The model receives a malformed "
                "tool result and produces an empty response."
            ),
            files=[
                SourceFile(
                    path="prompt_builder.py",
                    content="""def build_tool_result(tool_call_id, result):
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": str(result)
    }

def build_messages(user_query, tool_results=None):
    messages = [{"role": "user", "content": user_query}]
    if tool_results:
        for tr in tool_results:
            messages.append(tr)
    return messages
""",
                ),
                SourceFile(
                    path="schema_validator.py",
                    content="""def validate_tool_result(msg):
    required = ["role", "tool_call_id", "output"]
    for field in required:
        if field not in msg:
            return {"valid": False, "error": f"Missing field: {field}"}
    return {"valid": True}

def validate_messages(messages):
    for msg in messages:
        if msg.get("role") == "tool":
            result = validate_tool_result(msg)
            if not result["valid"]:
                return result
    return {"valid": True}
""",
                ),
                SourceFile(
                    path="harness.py",
                    content="""from prompt_builder import build_tool_result, build_messages
from schema_validator import validate_messages

def run(user_query, tool_call_id="tc_1", tool_result_data="search results here"):
    tool_result = build_tool_result(tool_call_id, tool_result_data)
    validation = validate_messages([tool_result])
    if not validation["valid"]:
        return {"ok": False, "error": validation["error"]}
    messages = build_messages(user_query, [tool_result])
    return {"ok": True, "messages": messages}
""",
                ),
            ],
            trace_spans=[
                {"span_id": "s1", "type": "tool_result_build", "fields_used": ["role", "tool_call_id", "content"], "actual_output": {"role": "tool", "tool_call_id": "tc_1", "content": "search results here"}},
                {"span_id": "s2", "type": "validation", "schema_required": ["role", "tool_call_id", "output"], "actual_fields_present": ["role", "tool_call_id", "content"], "passed": True, "field_mismatch": "expected 'output', got 'content'"},
                {"span_id": "s3", "type": "model_response", "response": "", "finish_reason": "error", "error_detail": "tool message missing 'output' field per API contract"},
            ],
            fix_description="Change prompt_builder.py to use 'output' instead of 'content' for the tool result field, matching the schema.",
        ),

        Scenario(
            failure_class="trace_span_corruption",
            bug_description=(
                "A trace middleware assigns parent_id to spans using a stale reference. "
                "Span 3 should be a child of span 2, but instead references span 1's ID. "
                "This causes the trace analysis to conclude the tool call happened before "
                "the model decision, producing an incorrect causal ordering."
            ),
            files=[
                SourceFile(
                    path="trace_middleware.py",
                    content="""import uuid

class TraceMiddleware:
    def __init__(self):
        self.spans = []
        self._last_id = None
        self._root_id = None

    def start_span(self, span_type, data=None):
        span_id = str(uuid.uuid4())[:8]
        span = {"span_id": span_id, "type": span_type, "parent_id": self._last_id}
        if data:
            span.update(data)
        self.spans.append(span)
        if self._root_id is None:
            self._root_id = span_id
        self._last_id = span_id
        return span

    def finish_span(self, span_id, result=None):
        for span in self.spans:
            if span["span_id"] == span_id:
                if result:
                    span["result"] = result
                self._last_id = self._root_id
                break
""",
                ),
                SourceFile(
                    path="pipeline.py",
                    content="""from trace_middleware import TraceMiddleware

class Pipeline:
    def __init__(self):
        self.tracer = TraceMiddleware()

    def run(self, query):
        s1 = self.tracer.start_span("model_call", {"query": query})
        model_result = {"action": "search", "params": {"q": query}}
        self.tracer.finish_span(s1["span_id"], model_result)

        s2 = self.tracer.start_span("tool_call", {"tool": "search", "params": model_result["params"]})
        tool_result = {"found": True, "items": ["item1", "item2"]}
        self.tracer.finish_span(s2["span_id"], tool_result)

        s3 = self.tracer.start_span("model_response", {"tool_result": tool_result})
        response = "Here are the results: item1, item2"
        self.tracer.finish_span(s3["span_id"], response)

        return {"response": response, "trace": self.tracer.spans}
""",
                ),
                SourceFile(
                    path="harness.py",
                    content="""from pipeline import Pipeline

def run(query):
    p = Pipeline()
    result = p.run(query)
    trace = result["trace"]
    # Verify causal ordering: each span should be child of previous
    for i in range(1, len(trace)):
        if trace[i]["parent_id"] != trace[i-1]["span_id"]:
            return {"ok": False, "error": "trace ordering broken"}
    return {"ok": True, "response": result["response"]}
""",
                ),
            ],
            trace_spans=[
                {"span_id": "abc1", "type": "model_call", "parent_id": None, "result": {"action": "search", "params": {"q": "test"}}},
                {"span_id": "def2", "type": "tool_call", "parent_id": "abc1", "result": {"found": True, "items": ["item1", "item2"]}},
                {"span_id": "ghi3", "type": "model_response", "parent_id": "abc1", "actual_parent_id": "def2", "result": "Here are the results: item1, item2"},
            ],
            fix_description="Fix the trace middleware so s3's parent_id is def2 (the tool call), not abc1 (the model call). The _last_id reference gets overwritten before s3 starts.",
        ),

        Scenario(
            failure_class="stale_context_injection",
            bug_description=(
                "A context manager caches the system prompt from the first request and "
                "reuses it for subsequent requests, even when the user's query requires "
                "a different system prompt version. The first request used a 'concise' mode "
                "prompt, but the second request needs 'detailed' mode. The cache returns "
                "the old 'concise' prompt, causing the model to produce an abbreviated response."
            ),
            files=[
                SourceFile(
                    path="context_manager.py",
                    content="""class ContextManager:
    def __init__(self):
        self._cache = {}

    def get_system_prompt(self, mode="detailed"):
        if "system" in self._cache:
            return self._cache["system"]
        prompt = f"You are a helpful assistant. Respond in {mode} mode."
        self._cache["system"] = prompt
        return prompt

    def clear_cache(self):
        self._cache = {}
""",
                ),
                SourceFile(
                    path="agent.py",
                    content="""from context_manager import ContextManager

class Agent:
    def __init__(self):
        self.ctx = ContextManager()

    def query(self, user_input, mode="detailed"):
        system = self.ctx.get_system_prompt(mode)
        # Simulate model call
        if "concise" in system:
            response = user_input[:20] + "..."
        else:
            response = f"Detailed analysis of: {user_input}"
        return {"system_prompt": system, "response": response}
""",
                ),
                SourceFile(
                    path="harness.py",
                    content="""from agent import Agent

def run():
    agent = Agent()
    # First call uses concise mode
    r1 = agent.query("Tell me about machine learning", mode="concise")
    # Second call should use detailed mode
    r2 = agent.query("Tell me about machine learning", mode="detailed")
    # Second response should be detailed
    if r2["response"].startswith("Detailed"):
        return {"ok": True, "response": r2["response"]}
    return {"ok": False, "got": r2["response"], "system_used": r2["system_prompt"]}
""",
                ),
            ],
            trace_spans=[
                {"span_id": "s1", "type": "query", "mode": "concise", "system_prompt": "You are a helpful assistant. Respond in concise mode.", "response": "Tell me about machine le..."},
                {"span_id": "s2", "type": "query", "requested_mode": "detailed", "actual_system_prompt": "You are a helpful assistant. Respond in concise mode.", "response": "Tell me about machine le..."},
                {"span_id": "s3", "type": "cache_check", "cache_hit": True, "cached_mode": "concise", "requested_mode": "detailed"},
            ],
            fix_description="Fix get_system_prompt to check if cached prompt matches the requested mode before returning the cache.",
        ),

        Scenario(
            failure_class="error_swallow",
            bug_description=(
                "A tool wrapper catches all exceptions and converts them to a dict with "
                "status='error', but the harness's result handler only checks for the "
                "presence of a dict (truthy), not the status field. Every tool result — "
                "success or failure — is treated as a successful operation."
            ),
            files=[
                SourceFile(
                    path="tool_wrapper.py",
                    content="""def safe_execute(func, **kwargs):
    try:
        result = func(**kwargs)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
""",
                ),
                SourceFile(
                    path="harness.py",
                    content="""from tool_wrapper import safe_execute

def lookup_user(user_id):
    # This will raise if user_id is not an integer
    if not isinstance(user_id, int):
        raise ValueError(f"user_id must be int, got {type(user_id).__name__}")
    return {"id": user_id, "name": f"User {user_id}"}

def run(user_input):
    result = safe_execute(lookup_user, user_id=user_input)
    if result:
        return {"ok": True, "user": result.get("data", result)}
    return {"ok": False}
""",
                ),
            ],
            trace_spans=[
                {"span_id": "s1", "type": "tool_input", "function": "lookup_user", "args": {"user_id": "abc123"}, "note": "string passed, not int"},
                {"span_id": "s2", "type": "exception", "exception_type": "ValueError", "message": "user_id must be int, got str", "caught": True},
                {"span_id": "s3", "type": "tool_return", "returned": {"status": "error", "message": "user_id must be int, got str"}},
                {"span_id": "s4", "type": "harness_check", "checked": "if result", "result_truthy": True, "treated_as": "success", "actual_return": {"ok": True, "user": {"status": "error", "message": "user_id must be int, got str"}}},
            ],
            fix_description="Fix the harness to check result['status'] == 'ok' instead of just truthiness of the result dict.",
        ),

        Scenario(
            failure_class="off_by_one_in_loop",
            bug_description=(
                "A retry mechanism iterates using range(max_retries) which produces "
                "0,1,2 for max_retries=3 — giving only 3 iterations total. But the "
                "first attempt happens before the retry loop, so the total attempts "
                "are max_retries, not max_retries+1. The harness expects max_retries+1 "
                "total attempts (1 initial + max_retries retries)."
            ),
            files=[
                SourceFile(
                    path="retry.py",
                    content="""import time

def retry_with_backoff(func, max_retries=3, base_delay=0.1):
    last_error = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_error = e
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
    raise last_error
""",
                ),
                SourceFile(
                    path="harness.py",
                    content="""from retry import retry_with_backoff

call_count = 0

def flaky_operation():
    global call_count
    call_count += 1
    if call_count < 4:
        raise ConnectionError("timeout")
    return "success"

def run():
    global call_count
    call_count = 0
    try:
        result = retry_with_backoff(flaky_operation, max_retries=3)
        return {"ok": True, "result": result, "attempts": call_count}
    except ConnectionError:
        return {"ok": False, "attempts": call_count, "error": "all retries exhausted"}
""",
                ),
            ],
            trace_spans=[
                {"span_id": "s1", "type": "attempt", "attempt": 0, "result": "ConnectionError: timeout"},
                {"span_id": "s2", "type": "attempt", "attempt": 1, "result": "ConnectionError: timeout"},
                {"span_id": "s3", "type": "attempt", "attempt": 2, "result": "ConnectionError: timeout"},
                {"span_id": "s4", "type": "retry_exhausted", "total_attempts": 3, "max_retries": 3, "actual_return": {"ok": False, "attempts": 3, "error": "all retries exhausted"}, "note": "expected 4 attempts (1 initial + 3 retries), only got 3"},
            ],
            fix_description="Change range(max_retries) to range(max_retries + 1) or restructure to include the initial attempt in the count.",
        ),

        Scenario(
            failure_class="silent_type_coercion",
            bug_description=(
                "A tool expects a string parameter but receives an integer from the model. "
                "The adapter passes kwargs through without type checking. The downstream "
                "API call silently converts the int to a string via str(), but the resulting "
                "query matches nothing because the original data uses string-formatted IDs "
                "like '001' while str(1) produces '1'."
            ),
            files=[
                SourceFile(
                    path="api_client.py",
                    content="""def fetch_record(record_id):
    # API expects string IDs like "001", "002"
    # str() coercion happens implicitly in the URL path
    url = f"/api/records/{record_id}"
    return {"url_called": url, "found": url.endswith("001")}
""",
                ),
                SourceFile(
                    path="adapter.py",
                    content="""from api_client import fetch_record

class ToolAdapter:
    def call(self, tool_name, **kwargs):
        if tool_name == "fetch_record":
            return fetch_record(**kwargs)
        return {"error": f"Unknown tool: {tool_name}"}
""",
                ),
                SourceFile(
                    path="harness.py",
                    content="""from adapter import ToolAdapter

def run(model_output):
    adapter = ToolAdapter()
    # Model returns integer 1 instead of string "001"
    result = adapter.call("fetch_record", record_id=1)
    if result.get("found"):
        return {"ok": True, "record": result}
    return {"ok": False, "url_called": result.get("url_called"), "note": "record not found"}
""",
                ),
            ],
            trace_spans=[
                {"span_id": "s1", "type": "model_output", "tool": "fetch_record", "arguments": {"record_id": 1}, "argument_types": {"record_id": "int"}},
                {"span_id": "s2", "type": "api_call", "url": "/api/records/1", "expected_url": "/api/records/001", "coerced_value": "runtime_coercion_observed::int_1_became_unpadded_str_1", "original_value": 1},
                {"span_id": "s3", "type": "result", "found": False, "note": "ID '1' does not match any record; database uses zero-padded '001' format"},
            ],
            fix_description="Add type coercion in adapter.py to zero-pad integer record_ids to 3-digit strings, or validate the type before calling fetch_record.",
        ),

        Scenario(
            failure_class="missing_await_in_trace",
            bug_description=(
                "An async tool is called but the harness doesn't await it. The trace "
                "shows an immediate return of a coroutine object rather than the actual "
                "result. The harness treats the coroutine as a successful result because "
                "it's truthy, but no actual work was done."
            ),
            files=[
                SourceFile(
                    path="async_tools.py",
                    content="""import asyncio

async def fetch_data(source):
    await asyncio.sleep(0.01)  # simulate IO
    return {"source": source, "data": [1, 2, 3], "status": "complete"}
""",
                ),
                SourceFile(
                    path="harness.py",
                    content="""import asyncio
from async_tools import fetch_data

async def run():
    result = fetch_data("api")
    # forgot to await — result is a coroutine object
    if result:
        return {"ok": True, "data": result}
    return {"ok": False}

def main():
    return asyncio.run(run())
""",
                ),
            ],
            trace_spans=[
                {"span_id": "s1", "type": "tool_call", "tool": "fetch_data", "args": {"source": "api"}, "awaited": False},
                {"span_id": "s2", "type": "return_value", "value_repr": "<coroutine object fetch_data at 0x7f...>", "is_coroutine": "runtime_async_leak::fetch_data_returned_coroutine_object_unawaited", "truthy": True},
                {"span_id": "s3", "type": "harness_check", "checked": "if result", "result_type": "coroutine", "treated_as": "success", "actual_data": None},
            ],
            fix_description="Add `await` before the fetch_data call in harness.py.",
        ),

        Scenario(
            failure_class="overlapping_tool_dispatch",
            bug_description=(
                "Two tools are dispatched concurrently but their results are written to "
                "the same shared dict. Due to a race condition, tool B's result overwrites "
                "tool A's result in the dict. The harness reads the result for tool A and "
                "gets tool B's data, producing an incorrect summary."
            ),
            files=[
                SourceFile(
                    path="dispatcher.py",
                    content="""import threading

class ConcurrentDispatcher:
    def __init__(self):
        self.results = {}
        self._order = 0

    def dispatch(self, calls):
        threads = []
        for call in calls:
            t = threading.Thread(target=self._run, args=(call["name"], call["func"], call.get("args", {})))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        return self.results

    def _run(self, key, func, args):
        result = func(**args)
        existing = list(self.results.keys())
        if existing:
            self.results[existing[0]] = result
        self.results[key] = result
""",
                ),
                SourceFile(
                    path="harness.py",
                    content="""from dispatcher import ConcurrentDispatcher
import threading

def get_weather(city):
    return {"temp": "72F", "condition": "sunny", "city": city}

def get_news(topic):
    return {"headline": "Breaking: tech update", "category": topic}

def run():
    # Use sequential execution to make bug deterministic
    dispatcher = ConcurrentDispatcher()
    # First dispatch weather
    t1 = threading.Thread(target=dispatcher._run, args=("weather_result", get_weather, {"city": "NYC"}))
    t1.start()
    t1.join()
    # Then dispatch news — this triggers the bug: overwrites weather_result with news
    t2 = threading.Thread(target=dispatcher._run, args=("news_result", get_news, {"topic": "tech"}))
    t2.start()
    t2.join()

    results = dispatcher.results
    weather = results.get("weather_result", {})
    if isinstance(weather, dict) and "temp" in weather and "condition" in weather:
        return {"ok": True, "weather": weather}
    return {"ok": False, "got_weather": weather, "all_results": results}
""",
                ),
            ],
            trace_spans=[
                {"span_id": "s1", "type": "dispatch_start", "tools": ["weather_result", "news_result"], "concurrent": True},
                {"span_id": "s2", "type": "tool_complete", "tool": "weather_result", "result": {"temp": "72F", "condition": "sunny", "city": "NYC"}},
                {"span_id": "s3", "type": "tool_complete", "tool": "news_result", "result": {"headline": "Breaking: tech update", "category": "tech"}},
                {"span_id": "s4", "type": "result_read", "key_read": "weather_result", "actual_value": {"headline": "Breaking: tech update", "category": "tech"}, "expected_type": "weather_data"},
            ],
            fix_description="The race is in the harness reading results dict before both writes complete, or key collision. Fix the dispatcher to use unique keys per call or return results in a structured way.",
        ),

        Scenario(
            failure_class="harness_eval_false_positive",
            bug_description=(
                "The harness's eval function claims to verify the model output matches "
                "expectations, but the assertion always passes because it compares against "
                "a variable that's reassigned before the check. The eval returns 'pass' "
                "even for completely wrong outputs."
            ),
            files=[
                SourceFile(
                    path="evaluator.py",
                    content="""def evaluate_response(model_output, expected_keys):
    score = 0
    max_score = len(expected_keys)

    for key in expected_keys:
        if key in model_output:
            score += 1

    # Check partial match threshold
    if score >= 1:
        max_score = score

    passed = score >= max_score
    return {"passed": passed, "score": score, "max_score": max_score}
""",
                ),
                SourceFile(
                    path="harness.py",
                    content="""from evaluator import evaluate_response

def run():
    # Model output only has 1 of 3 required keys
    model_output = {"title": "Some title"}
    expected_keys = ["title", "body", "tags"]
    result = evaluate_response(model_output, expected_keys)
    # Should return passed=False (1/3 keys), but bug makes it pass
    return {"ok": result["passed"], "score": result["score"]}
""",
                ),
            ],
            trace_spans=[
                {"span_id": "s1", "type": "eval_input", "model_output": {"summary": "wrong content", "length": 5}, "expected_keys": ["title", "body", "tags", "author"]},
                {"span_id": "s2", "type": "scoring", "keys_matched": 0, "expected_total": 4, "score": 0},
                {"span_id": "s3", "type": "threshold_check", "score": 0, "original_max": 4, "max_after_reassignment": "runtime_eval_bug::threshold_mutated_from_4_to_score_0", "passed": True, "note": "max_score reassigned to score (0), so 0 >= 0 is True"},
            ],
            fix_description="Remove the `max_score = score` reassignment in evaluator.py. The variable should remain as the threshold.",
        ),
    ]
