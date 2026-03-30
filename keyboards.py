from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from config import AVAILABLE_MODELS, IMAGE_MODELS, VIDEO_MODELS, CHANNEL_ID


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


# ── Image keyboards ──────────────────────────────────────────

def image_models_keyboard() -> InlineKeyboardMarkup:
    rows = []
    items = list(IMAGE_MODELS.items())
    for i in range(0, len(items), 2):
        row = []
        for model_id, label in items[i : i + 2]:
            row.append(
                InlineKeyboardButton(text=label, callback_data=f"img_model:{model_id}")
            )
        rows.append(row)
    rows.append(
        [InlineKeyboardButton(text="🖼️ Моя галерея — в разработке", callback_data="img_gallery")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def image_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Text to Image", callback_data="img_mode:t2i"),
                InlineKeyboardButton(text="🖼️ Image to Image", callback_data="img_mode:i2i"),
            ]
        ]
    )


# ── Video keyboards ──────────────────────────────────────────

def video_models_keyboard() -> InlineKeyboardMarkup:
    rows = []
    items = list(VIDEO_MODELS.items())
    for i in range(0, len(items), 2):
        row = []
        for model_id, label in items[i : i + 2]:
            row.append(
                InlineKeyboardButton(text=label, callback_data=f"vid_model:{model_id}")
            )
        rows.append(row)
    rows.append(
        [InlineKeyboardButton(text="☁️ Мои видео — в разработке", callback_data="vid_gallery")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def video_mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Text to Video", callback_data="vid_mode:t2v"),
                InlineKeyboardButton(text="🖼️ Image to Video", callback_data="vid_mode:i2v"),
            ]
        ]
    )


# ── Text model keyboard ──────────────────────────────────────

def models_keyboard(current_model: str) -> InlineKeyboardMarkup:
    buttons = []
    for model_id, label in AVAILABLE_MODELS.items():
        display = f"👉 {label}" if model_id == current_model else label
        buttons.append(
            [InlineKeyboardButton(text=display, callback_data=f"select_model:{model_id}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)
