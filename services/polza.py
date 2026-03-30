import aiohttp
from config import POLZA_API_KEY, POLZA_BASE_URL


class PolzaClient:
    def __init__(self, api_key: str = POLZA_API_KEY, base_url: str = POLZA_BASE_URL) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

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

    async def generate_image(self, prompt: str, model: str = "dall-e-3") -> str:
        """Generate an image and return its URL."""
        url = f"{self.base_url}/images/generations"
        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self.headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"API error ({resp.status}): {text}")
                data = await resp.json()
                return data["data"][0]["url"]

    async def generate_video(self, prompt: str) -> str:
        """Placeholder — video generation is not yet available."""
        return "🎬 Генерация видео скоро будет доступна! Следите за обновлениями."
