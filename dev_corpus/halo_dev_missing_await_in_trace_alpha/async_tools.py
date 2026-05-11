import asyncio

async def fetch_data(source):
    await asyncio.sleep(0.01)  # simulate IO
    return {"source": source, "data": [1, 2, 3], "status": "complete"}
