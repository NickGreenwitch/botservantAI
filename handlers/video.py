from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from handlers.menu import UserMode
from services.polza import PolzaClient

router = Router()
polza = PolzaClient()


@router.message(UserMode.video)
async def handle_video_message(message: Message, state: FSMContext) -> None:
    if not message.text:
        return

    # Check if user pressed a menu button — don't process as video
    menu_buttons = {"💬 Чат с ИИ", "🖼️ Картинки", "🎬 Видео", "🤖 Выбрать модель", "👤 Профиль"}
    if message.text in menu_buttons:
        return

    result = await polza.generate_video(prompt=message.text)
    await message.answer(result)
