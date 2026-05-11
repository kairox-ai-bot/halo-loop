import threading

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
