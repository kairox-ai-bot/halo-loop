class ContextManager:
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
