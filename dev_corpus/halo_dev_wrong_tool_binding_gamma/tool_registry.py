class ToolRegistry:
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
