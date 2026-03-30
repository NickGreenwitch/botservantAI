from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from config import AVAILABLE_MODELS, CHANNEL_ID


def subscription_keyboard() -> InlineKeyboardMarkup:
    channel = CHANNEL_ID.lstrip("@")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Подписаться на канал",
                    url=f"https://t.me/{channel}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Проверить подписку",
                    callback_data="check_subscription",
                )
            ],
        ]
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 Чат с ИИ")],
            [KeyboardButton(text="🖼️ Картинки"), KeyboardButton(text="🎬 Видео")],
            [KeyboardButton(text="🤖 Выбрать модель"), KeyboardButton(text="👤 Профиль")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def models_keyboard(current_model: str) -> InlineKeyboardMarkup:
    buttons = []
    for model in AVAILABLE_MODELS:
        label = f"✅ {model}" if model == current_model else model
        buttons.append(
            [InlineKeyboardButton(text=label, callback_data=f"select_model:{model}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)
