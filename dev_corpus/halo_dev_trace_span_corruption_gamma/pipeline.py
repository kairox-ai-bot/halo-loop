from trace_middleware import TraceMiddleware

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
