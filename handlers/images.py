from aiogram import Router
from aiogram.types import Message, URLInputFile
from aiogram.fsm.context import FSMContext

from handlers.menu import UserMode
from database import update_last_active
from services.polza import PolzaClient

router = Router()
polza = PolzaClient()


@router.message(UserMode.images)
async def handle_image_message(message: Message, state: FSMContext) -> None:
    if not message.text:
        return

    # Check if user pressed a menu button — don't process as image generation
    menu_buttons = {"💬 Чат с ИИ", "🖼️ Картинки", "🎬 Видео", "🤖 Выбрать модель", "👤 Профиль"}
    if message.text in menu_buttons:
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")

    result = await polza.generate_image(prompt=message.text)

    await update_last_active(message.from_user.id)

    if result.startswith("⚠️"):
        await message.answer(result)
    else:
        try:
            photo = URLInputFile(result)
            await message.answer_photo(photo=photo, caption=f"🖼️ {message.text}")
        except Exception as e:
            await message.answer(f"⚠️ Не удалось отправить изображение: {e}")
