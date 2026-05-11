import asyncio
from async_tools import fetch_data

async def run():
    result = fetch_data("api")
    # forgot to await — result is a coroutine object
    if result:
        return {"ok": True, "data": result}
    return {"ok": False}

def main():
    return asyncio.run(run())
