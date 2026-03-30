from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from handlers.menu import UserMode
from database import get_user, update_last_active
from services.polza import PolzaClient

router = Router()
polza = PolzaClient()


@router.message(UserMode.chat)
async def handle_chat_message(message: Message, state: FSMContext) -> None:
    if not message.text:
        return

    # Check if user pressed a menu button — don't process as chat
    menu_buttons = {"💬 Чат с ИИ", "🖼️ Картинки", "🎬 Видео", "🤖 Выбрать модель", "👤 Профиль"}
    if message.text in menu_buttons:
        return

    user = await get_user(message.from_user.id)
    model = user["selected_model"] if user else "auto"

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    messages = [{"role": "user", "content": message.text}]
    response = await polza.chat(model=model, messages=messages)

    await update_last_active(message.from_user.id)
    await message.answer(response)
