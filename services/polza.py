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

    # ── Image Generation (Media API) ──────────────────────────

    async def generate_image(
        self,
        prompt: str,
        model: str = "nano-banana",
        image_b64: str | None = None,
    ) -> str:
        """Generate an image via Media API. Returns the result URL.

        Args:
            prompt: Text description of the desired image.
            model: Image model id (e.g. nano-banana, grok-image, etc.).
            image_b64: Optional base64-encoded source image for img2img.

        Returns:
            URL of the generated image.
        """
        url = f"{self.base_url}/media"
        input_obj: dict = {"prompt": prompt}
        if image_b64 is not None:
            input_obj["images"] = [{"type": "base64", "data": image_b64}]

        payload = {
            "model": model,
            "input": input_obj,
        }

        async with aiohttp.ClientSession() as session:
            # Create media generation task
            async with session.post(url, json=payload, headers=self.headers) as resp:
                if resp.status not in (200, 201):
                    text = await resp.text()
                    raise Exception(f"API error ({resp.status}): {text}")
                data = await resp.json()

            # If already completed (synchronous return)
            if data.get("status") == "completed":
                return self._extract_image_url(data)

            # Async mode — poll for result
            task_id = data.get("id")
            if not task_id:
                raise Exception(f"No task id in response: {data}")

            return await self._poll_media(session, task_id)

    async def _poll_media(
        self,
        session: aiohttp.ClientSession,
        task_id: str,
        interval: float = 4.0,
        max_wait: float = 300.0,
    ) -> str:
        """Poll GET /v1/media/{id} until completed or failed."""
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
                return self._extract_image_url(data)
            if status == "failed":
                error = data.get("error", "unknown error")
                raise Exception(f"Generation failed: {error}")
            # pending / processing — keep polling
            logger.debug("Media %s status: %s (%.0fs)", task_id, status, elapsed)

        raise TimeoutError(f"Image generation timed out after {max_wait}s")

    @staticmethod
    def _extract_image_url(data: dict) -> str:
        """Pull the image URL from a completed media response."""
        # Media API: data.data.url
        inner = data.get("data")
        if isinstance(inner, dict) and "url" in inner:
            return inner["url"]
        # Images API compat: data.data[0].url
        if isinstance(inner, list) and inner:
            return inner[0].get("url", "")
        raise Exception(f"Could not extract image URL from response: {data}")

    # ── Video (placeholder) ───────────────────────────────────

    async def generate_video(self, prompt: str) -> str:
        """Placeholder — video generation is not yet available."""
        return "🎬 Генерация видео скоро будет доступна! Следите за обновлениями."
