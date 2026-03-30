import asyncio
import logging

import aiohttp
from config import POLZA_API_KEY, POLZA_BASE_URL

logger = logging.getLogger(__name__)


class PolzaClient:
    def __init__(self, api_key: str = POLZA_API_KEY, base_url: str = POLZA_BASE_URL) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ── Text Chat ──────────────────────────────────────────────

    async def chat(self, model: str, messages: list[dict[str, str]]) -> str:
        """Send a chat completion request and return the assistant's reply."""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self.headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"API error ({resp.status}): {text}")
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    # ── Media helpers (shared by image & video) ───────────────

    async def _create_media_task(
        self,
        session: aiohttp.ClientSession,
        model: str,
        input_obj: dict,
    ) -> dict:
        """POST /v1/media and return the raw JSON response."""
        url = f"{self.base_url}/media"
        payload = {"model": model, "input": input_obj}
        async with session.post(url, json=payload, headers=self.headers) as resp:
            if resp.status not in (200, 201):
                text = await resp.text()
                raise Exception(f"API error ({resp.status}): {text}")
            return await resp.json()

    async def _poll_media(
        self,
        session: aiohttp.ClientSession,
        task_id: str,
        interval: float = 4.0,
        max_wait: float = 300.0,
    ) -> dict:
        """Poll GET /v1/media/{id} until completed or failed. Returns full response."""
        url = f"{self.base_url}/media/{task_id}"
        elapsed = 0.0
        while elapsed < max_wait:
            await asyncio.sleep(interval)
            elapsed += interval
            async with session.get(url, headers=self.headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Poll error ({resp.status}): {text}")
                data = await resp.json()

            status = data.get("status")
            if status == "completed":
                return data
            if status == "failed":
                error = data.get("error", "unknown error")
                raise Exception(f"Generation failed: {error}")
            logger.debug("Media %s status: %s (%.0fs)", task_id, status, elapsed)

        raise TimeoutError(f"Generation timed out after {max_wait}s")

    @staticmethod
    def _extract_media_url(data: dict) -> str:
        """Pull the result URL from a completed media response."""
        inner = data.get("data")
        if isinstance(inner, dict) and "url" in inner:
            return inner["url"]
        if isinstance(inner, list) and inner:
            return inner[0].get("url", "")
        raise Exception(f"Could not extract media URL from response: {data}")

    # ── Image Generation (Media API) ──────────────────────────

    async def generate_image(
        self,
        prompt: str,
        model: str = "nano-banana",
        image_b64: str | None = None,
    ) -> str:
        """Generate an image via Media API. Returns the result URL."""
        input_obj: dict = {"prompt": prompt}
        if image_b64 is not None:
            input_obj["images"] = [{"type": "base64", "data": image_b64}]

        async with aiohttp.ClientSession() as session:
            data = await self._create_media_task(session, model, input_obj)

            if data.get("status") == "completed":
                return self._extract_media_url(data)

            task_id = data.get("id")
            if not task_id:
                raise Exception(f"No task id in response: {data}")

            result = await self._poll_media(session, task_id, interval=4.0, max_wait=300.0)
            return self._extract_media_url(result)

    # ── Video Generation (Media API) ──────────────────────────

    async def generate_video(
        self,
        prompt: str,
        model: str = "veo-3.1-fast",
        image_b64: str | None = None,
    ) -> str:
        """Generate a video via Media API. Returns the result URL.

        Video generation is always async — we poll until completion.
        """
        input_obj: dict = {"prompt": prompt}
        if image_b64 is not None:
            input_obj["images"] = [{"type": "base64", "data": image_b64}]

        async with aiohttp.ClientSession() as session:
            data = await self._create_media_task(session, model, input_obj)

            if data.get("status") == "completed":
                return self._extract_media_url(data)

            task_id = data.get("id")
            if not task_id:
                raise Exception(f"No task id in response: {data}")

            # Video takes longer — poll every 5s, up to 5 min
            result = await self._poll_media(session, task_id, interval=5.0, max_wait=300.0)
            return self._extract_media_url(result)
