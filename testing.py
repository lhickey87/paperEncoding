

import asyncio

#one way we can think of async functions is that we MUST call await on a coroutine


async def main():
    tasks = []
    with httpx.AsyncClient() as client:
        new = client.get(URL)
        tasks.append(new)
    #
        
    response = await asyncio.gather(*tasks)