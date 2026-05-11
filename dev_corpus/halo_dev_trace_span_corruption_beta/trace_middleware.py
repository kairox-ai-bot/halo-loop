import uuid

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
