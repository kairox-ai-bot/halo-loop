from agent import Agent

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
