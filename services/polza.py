import asyncio
import logging

import aiohttp
from config import POLZA_API_KEY, POLZA_BASE_URL

logger = logging.getLogger(__name__)

# Timeouts: 60s for text chat, 30s for media task creation, no limit on polling
CHAT_TIMEOUT = aiohttp.ClientTimeout(total=60)
MEDIA_TIMEOUT = aiohttp.ClientTimeout(total=30)


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
        payload = {"model": model, "messages": messages}
        logger.info("Chat request: model=%s, message_count=%d", model, len(messages))
        async with aiohttp.ClientSession(timeout=CHAT_TIMEOUT) as session:
            async with session.post(url, json=payload, headers=self.headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error("Chat API error %d: %s", resp.status, text[:300])
                    raise Exception(f"API error ({resp.status}): {text}")
                data = await resp.json()
                content = data["choices"][0]["message"]["content"]
                logger.info("Chat response received: %d chars", len(content))
                return content

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
        logger.info("Media task: model=%s", model)
        async with session.post(url, json=payload, headers=self.headers) as resp:
            if resp.status not in (200, 201):
                text = await resp.text()
                logger.error("Media create error %d: %s", resp.status, text[:300])
                raise Exception(f"API error ({resp.status}): {text}")
            data = await resp.json()
            logger.info("Media task created: id=%s status=%s", data.get("id"), data.get("status"))
            return data

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
                    logger.error("Poll error %d for %s: %s", resp.status, task_id, text[:200])
                    raise Exception(f"Poll error ({resp.status}): {text}")
                data = await resp.json()

            status = data.get("status")
            if status == "completed":
                logger.info("Media %s completed after %.0fs", task_id, elapsed)
                return data
            if status == "failed":
                error = data.get("error", "unknown error")
                logger.error("Media %s failed: %s", task_id, error)
                raise Exception(f"Generation failed: {error}")
            logger.debug("Media %s status: %s (%.0fs)", task_id, status, elapsed)

        logger.warning("Media %s timed out after %.0fs", task_id, max_wait)
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
        logger.info("Image generation: model=%s, has_source=%s", model, image_b64 is not None)

        async with aiohttp.ClientSession(timeout=MEDIA_TIMEOUT) as session:
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
        """Generate a video via Media API. Returns the result URL."""
        input_obj: dict = {"prompt": prompt}
        if image_b64 is not None:
            input_obj["images"] = [{"type": "base64", "data": image_b64}]
        logger.info("Video generation: model=%s, has_source=%s", model, image_b64 is not None)

        async with aiohttp.ClientSession(timeout=MEDIA_TIMEOUT) as session:
            data = await self._create_media_task(session, model, input_obj)

            if data.get("status") == "completed":
                return self._extract_media_url(data)

            task_id = data.get("id")
            if not task_id:
                raise Exception(f"No task id in response: {data}")

            result = await self._poll_media(session, task_id, interval=5.0, max_wait=300.0)
            return self._extract_media_url(result)
