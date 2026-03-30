from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from handlers.menu import UserMode
from services.polza import PolzaClient

router = Router()
polza = PolzaClient()

MENU_BUTTONS = {"💬 Чат с ИИ", "🖼️ Картинки", "🎬 Видео", "🤖 Выбрать модель", "👤 Профиль"}


@router.message(UserMode.video)
async def handle_video_message(message: Message, state: FSMContext) -> None:
    if not message.text or message.text in MENU_BUTTONS:
        return

    result = await polza.generate_video(prompt=message.text)
    await message.answer(result)
