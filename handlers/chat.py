import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from handlers.menu import UserMode
from database import get_user, update_last_active
from keyboards import main_menu_keyboard
from services.polza import PolzaClient

logger = logging.getLogger(__name__)
router = Router()
polza = PolzaClient()

MENU_BUTTONS = {"💬 Чат с ИИ", "🖼️ Картинки", "🎬 Видео", "🤖 Выбрать модель", "👤 Профиль"}


@router.message(UserMode.chat)
async def handle_chat_message(message: Message, state: FSMContext) -> None:
    if not message.text or message.text in MENU_BUTTONS:
        return

    user = await get_user(message.from_user.id)
    model = user["selected_model"] if user else "auto"

    thinking_msg = await message.answer("🤖 Думаю...")
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    messages = [{"role": "user", "content": message.text}]

    try:
        response = await polza.chat(model=model, messages=messages)
    except Exception as e:
        logger.error("Polza chat error: %s", e)
        await thinking_msg.edit_text("❌ Ошибка при обращении к ИИ. Попробуй ещё раз.")
        return

    await update_last_active(message.from_user.id)
    await thinking_msg.edit_text(response)
