from typing import AsyncIterator

from httpx import AsyncClient


async def stream_turn(backend_url: str, trigger: str, story_id: str | None = None) -> AsyncIterator[str]:
    async with AsyncClient(timeout=None) as client:
        payload = {"trigger": trigger}
        if story_id:
            payload["story_id"] = story_id
        async with client.stream(
            "POST",
            f"{backend_url}/turn/stream",
            json=payload,
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_text():
                if chunk:
                    yield chunk
