import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
POLZA_API_KEY: str = os.getenv("POLZA_API_KEY", "")
CHANNEL_ID: str = os.getenv("CHANNEL_ID", "@yandertakerai")

POLZA_BASE_URL = "https://polza.ai/api/v1"

AVAILABLE_MODELS: dict[str, str] = {
    "auto": "✅ Авто (по умолчанию)",
    "google/gemini-3-flash-preview": "⚡ Gemini 3 Flash",
    "openai/gpt-5-mini": "🚀 GPT-5 Mini",
    "x-ai/grok-4.1-fast": "🤖 Grok 4.1 Fast",
    "deepseek/deepseek-v3.2": "🤖 DeepSeek v3.2",
    "anthropic/claude-sonnet-4.6": "✨ Claude Sonnet 4.6",
}

IMAGE_MODELS: dict[str, str] = {
    "google/gemini-2.5-flash-image": "🍌 Nano Banana",
    "google/gemini-3.1-flash-image-preview": "🍌 Nano Banana V2",
    "x-ai/grok-imagine-image": "🤖 Grok Image",
    "bytedance/seedream-5-lite": "🌱 Seedream 5.0 Lite",
}

VIDEO_MODELS: dict[str, str] = {
    "google/veo3_fast": "🎬 Veo 3.1 Fast",
    "openai/sora-2": "🎥 Sora 2",
    "kling/v3": "🎞️ Kling 3.0",
}
