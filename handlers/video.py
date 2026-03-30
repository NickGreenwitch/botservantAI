import base64
import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, URLInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import VIDEO_MODELS
from database import update_last_active
from keyboards import video_models_keyboard, video_mode_keyboard, main_menu_keyboard
from services.polza import PolzaClient

logger = logging.getLogger(__name__)
router = Router()
polza = PolzaClient()

MENU_BUTTONS = {"💬 Чат с ИИ", "🖼️ Картинки", "🎬 Видео", "🤖 Выбрать модель", "👤 Профиль"}


class VideoMode(StatesGroup):
    waiting_t2v_prompt = State()
    waiting_i2v_photo = State()
    waiting_i2v_prompt = State()


# ── Entry: "🎬 Видео" button ─────────────────────────────────

@router.message(F.text == "🎬 Видео")
async def enter_video(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "🎬 Выбери модель для генерации видео:",
        reply_markup=video_models_keyboard(),
    )


# ── Step 1: Pick video model ─────────────────────────────────

@router.callback_query(F.data.startswith("vid_model:"))
async def pick_video_model(callback: CallbackQuery, state: FSMContext) -> None:
    model_id = callback.data.split(":", 1)[1]
    label = VIDEO_MODELS.get(model_id, model_id)
    await state.update_data(vid_model=model_id, vid_model_label=label)
    await callback.message.edit_text(
        f"Модель: <b>{label}</b>\n\nВыбери режим:",
        parse_mode="HTML",
        reply_markup=video_mode_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "vid_gallery")
async def gallery_placeholder(callback: CallbackQuery) -> None:
    await callback.answer("☁️ Галерея видео пока в разработке!", show_alert=True)


# ── Step 2: Pick mode (t2v / i2v) ────────────────────────────

@router.callback_query(F.data == "vid_mode:t2v")
async def mode_text_to_video(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(VideoMode.waiting_t2v_prompt)
    await callback.message.edit_text("📝 Опиши видео, которое хочешь получить:")
    await callback.answer()


@router.callback_query(F.data == "vid_mode:i2v")
async def mode_image_to_video(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(VideoMode.waiting_i2v_photo)
    await callback.message.edit_text("🖼️ Пришли исходное фото для видео:")
    await callback.answer()


# ── Text-to-Video: receive prompt ────────────────────────────

@router.message(VideoMode.waiting_t2v_prompt)
async def handle_t2v_prompt(message: Message, state: FSMContext) -> None:
    if not message.text or message.text in MENU_BUTTONS:
        await state.clear()
        return

    data = await state.get_data()
    model_id = data.get("vid_model", "veo-3.1-fast")
    model_label = data.get("vid_model_label", model_id)

    status_msg = await message.answer("🤖 Создаю видео, это займёт до 2-3 минут...")
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_video")

    try:
        video_url = await polza.generate_video(prompt=message.text, model=model_id)
    except TimeoutError:
        await status_msg.edit_text(
            "⏳ Генерация заняла слишком долго. Попробуй позже.",
        )
        await state.clear()
        return
    except Exception as e:
        logger.error("Video generation error: %s", e)
        await status_msg.edit_text("❌ Ошибка генерации видео.")
        await state.clear()
        return

    await update_last_active(message.from_user.id)
    await status_msg.delete()

    try:
        video_file = URLInputFile(video_url)
        await message.answer_video(
            video=video_file,
            caption=f"✅ Видео готово! Модель: {model_label}",
            reply_markup=main_menu_keyboard(),
        )
    except Exception as e:
        logger.error("Failed to send video: %s", e)
        await message.answer(
            f"⚠️ Не удалось отправить видео: {e}",
            reply_markup=main_menu_keyboard(),
        )

    await state.clear()


# ── Image-to-Video: receive photo ────────────────────────────

@router.message(VideoMode.waiting_i2v_photo, F.photo)
async def handle_i2v_photo(message: Message, state: FSMContext, bot: Bot) -> None:
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    bio = await bot.download_file(file.file_path)
    image_b64 = base64.b64encode(bio.read()).decode()

    await state.update_data(source_image_b64=image_b64)
    await state.set_state(VideoMode.waiting_i2v_prompt)
    await message.answer("📝 Теперь опиши, какое видео хочешь получить:")


@router.message(VideoMode.waiting_i2v_photo)
async def handle_i2v_photo_invalid(message: Message, state: FSMContext) -> None:
    if message.text and message.text in MENU_BUTTONS:
        await state.clear()
        return
    await message.answer("🖼️ Пожалуйста, пришли фото (не файл и не текст).")


# ── Image-to-Video: receive prompt ───────────────────────────

@router.message(VideoMode.waiting_i2v_prompt)
async def handle_i2v_prompt(message: Message, state: FSMContext) -> None:
    if not message.text or message.text in MENU_BUTTONS:
        await state.clear()
        return

    data = await state.get_data()
    model_id = data.get("vid_model", "veo-3.1-fast")
    model_label = data.get("vid_model_label", model_id)
    source_b64 = data.get("source_image_b64")

    status_msg = await message.answer("🤖 Создаю видео, это займёт до 2-3 минут...")
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_video")

    try:
        video_url = await polza.generate_video(
            prompt=message.text, model=model_id, image_b64=source_b64,
        )
    except TimeoutError:
        await status_msg.edit_text(
            "⏳ Генерация заняла слишком долго. Попробуй позже.",
        )
        await state.clear()
        return
    except Exception as e:
        logger.error("Video generation error (i2v): %s", e)
        await status_msg.edit_text("❌ Ошибка генерации видео.")
        await state.clear()
        return

    await update_last_active(message.from_user.id)
    await status_msg.delete()

    try:
        video_file = URLInputFile(video_url)
        await message.answer_video(
            video=video_file,
            caption=f"✅ Видео готово! Модель: {model_label}",
            reply_markup=main_menu_keyboard(),
        )
    except Exception as e:
        logger.error("Failed to send video: %s", e)
        await message.answer(
            f"⚠️ Не удалось отправить видео: {e}",
            reply_markup=main_menu_keyboard(),
        )

    await state.clear()
