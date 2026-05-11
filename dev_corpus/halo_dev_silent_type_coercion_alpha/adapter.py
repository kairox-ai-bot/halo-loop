from api_client import fetch_record

class ToolAdapter:
    def call(self, tool_name, **kwargs):
        if tool_name == "fetch_record":
            return fetch_record(**kwargs)
        return {"error": f"Unknown tool: {tool_name}"}
