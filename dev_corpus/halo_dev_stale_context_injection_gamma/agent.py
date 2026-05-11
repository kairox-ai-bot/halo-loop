from context_manager import ContextManager

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
