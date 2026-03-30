import logging

from aiogram import Router
from aiogram.types import Message, URLInputFile
from aiogram.fsm.context import FSMContext

from handlers.menu import UserMode
from database import update_last_active
from keyboards import main_menu_keyboard
from services.polza import PolzaClient

logger = logging.getLogger(__name__)
router = Router()
polza = PolzaClient()

MENU_BUTTONS = {"💬 Чат с ИИ", "🖼️ Картинки", "🎬 Видео", "🤖 Выбрать модель", "👤 Профиль"}


@router.message(UserMode.images)
async def handle_image_message(message: Message, state: FSMContext) -> None:
    if not message.text or message.text in MENU_BUTTONS:
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")

    try:
        image_url = await polza.generate_image(prompt=message.text)
    except Exception as e:
        logger.error("Polza image error: %s", e)
        await message.answer("❌ Ошибка при генерации изображения. Попробуй ещё раз.")
        return

    await update_last_active(message.from_user.id)

    try:
        photo = URLInputFile(image_url)
        await message.answer_photo(photo=photo, caption=f"🖼️ {message.text}")
    except Exception as e:
        logger.error("Failed to send image: %s", e)
        await message.answer(f"⚠️ Не удалось отправить изображение: {e}")
