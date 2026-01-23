from typing import AsyncIterator

from httpx import AsyncClient


async def stream_turn(backend_url: str, trigger: str) -> AsyncIterator[str]:
    async with AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            f"{backend_url}/turn/stream",
            json={"trigger": trigger},
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_text():
                if chunk:
                    yield chunk
