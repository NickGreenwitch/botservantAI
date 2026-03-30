import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
POLZA_API_KEY: str = os.getenv("POLZA_API_KEY", "")
CHANNEL_ID: str = os.getenv("CHANNEL_ID", "@yandertakerai")

AVAILABLE_MODELS: list[str] = [
    "auto",
    "gpt-4o",
    "gpt-4o-mini",
    "claude-3.5-sonnet",
    "gemini-2.0-flash",
]
