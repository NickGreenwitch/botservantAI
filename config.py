import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
POLZA_API_KEY: str = os.getenv("POLZA_API_KEY", "")
CHANNEL_ID: str = os.getenv("CHANNEL_ID", "@yandertakerai")

POLZA_BASE_URL = "https://polza.ai/api/v1"

AVAILABLE_MODELS: dict[str, str] = {
    "auto": "✅ Авто (по умолчанию)",
    "gemini-3-flash": "⚡ Gemini 3 Flash",
    "gpt-5-mini": "🚀 GPT-5 Mini",
    "grok-4.1-fast": "🤖 Grok 4.1 Fast",
    "deepseek-v3.2": "🤖 DeepSeek v3.2",
    "claude-sonnet-4.6": "✨ Claude Sonnet 4.6",
}
