import base64
import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, URLInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import IMAGE_MODELS
from database import update_last_active
from keyboards import image_models_keyboard, image_mode_keyboard, main_menu_keyboard
from services.polza import PolzaClient

logger = logging.getLogger(__name__)
router = Router()
polza = PolzaClient()

MENU_BUTTONS = {"💬 Чат с ИИ", "🖼️ Картинки", "🎬 Видео", "🤖 Выбрать модель", "👤 Профиль"}


class ImageMode(StatesGroup):
    waiting_t2i_prompt = State()
    waiting_i2i_photo = State()
    waiting_i2i_prompt = State()


# ── Entry: "🖼️ Картинки" button ──────────────────────────────

@router.message(F.text == "🖼️ Картинки")
async def enter_images(message: Message, state: FSMContext) -> None:
    await state.clear()
    logger.info("User %d entered image menu", message.from_user.id)
    await message.answer(
        "🖼️ Выбери модель для генерации изображений:",
        reply_markup=image_models_keyboard(),
    )


# ── Step 1: Pick image model ─────────────────────────────────

@router.callback_query(F.data.startswith("img_model:"))
async def pick_image_model(callback: CallbackQuery, state: FSMContext) -> None:
    model_id = callback.data.split(":", 1)[1]
    label = IMAGE_MODELS.get(model_id, model_id)
    await state.update_data(img_model=model_id, img_model_label=label)
    logger.info("User %d picked image model: %s", callback.from_user.id, model_id)
    await callback.message.edit_text(
        f"Модель: <b>{label}</b>\n\nВыбери режим:",
        parse_mode="HTML",
        reply_markup=image_mode_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "img_gallery")
async def gallery_placeholder(callback: CallbackQuery) -> None:
    await callback.answer("🖼️ Галерея пока в разработке!", show_alert=True)


# ── Step 2: Pick mode (t2i / i2i) ────────────────────────────

@router.callback_query(F.data == "img_mode:t2i")
async def mode_text_to_image(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ImageMode.waiting_t2i_prompt)
    logger.info("User %d chose Text-to-Image", callback.from_user.id)
    await callback.message.edit_text("✏️ Опиши, что хочешь увидеть:")
    await callback.answer()


@router.callback_query(F.data == "img_mode:i2i")
async def mode_image_to_image(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ImageMode.waiting_i2i_photo)
    logger.info("User %d chose Image-to-Image", callback.from_user.id)
    await callback.message.edit_text("🖼️ Пришли исходное фото:")
    await callback.answer()


# ── Text-to-Image: receive prompt ────────────────────────────

@router.message(ImageMode.waiting_t2i_prompt)
async def handle_t2i_prompt(message: Message, state: FSMContext) -> None:
    if not message.text or message.text in MENU_BUTTONS:
        await state.clear()
        return

    data = await state.get_data()
    model_id = data.get("img_model", "nano-banana")
    model_label = data.get("img_model_label", model_id)
    logger.info("T2I from user %d: model=%s prompt=%s", message.from_user.id, model_id, message.text[:80])

    status_msg = await message.answer("🎨 Генерирую изображение...")
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")

    try:
        image_url = await polza.generate_image(prompt=message.text, model=model_id)
    except TimeoutError:
        logger.warning("T2I timeout for user %d", message.from_user.id)
        await status_msg.edit_text("⏳ Генерация заняла слишком долго. Попробуй позже.")
        await state.clear()
        return
    except Exception as e:
        logger.error("T2I error for user %d: %s", message.from_user.id, e)
        await status_msg.edit_text("❌ Ошибка генерации. Попробуй другой промпт или модель.")
        await state.clear()
        return

    await update_last_active(message.from_user.id)
    await status_msg.delete()

    try:
        photo = URLInputFile(image_url)
        await message.answer_photo(
            photo=photo,
            caption=f"✅ Готово! Модель: {model_label}",
            reply_markup=main_menu_keyboard(),
        )
        logger.info("T2I result sent to user %d", message.from_user.id)
    except Exception as e:
        logger.error("Failed to send image to user %d: %s", message.from_user.id, e)
        await message.answer(
            "⚠️ Не удалось отправить изображение. Попробуй ещё раз.",
            reply_markup=main_menu_keyboard(),
        )

    await state.clear()


# ── Image-to-Image: receive photo ────────────────────────────

@router.message(ImageMode.waiting_i2i_photo, F.photo)
async def handle_i2i_photo(message: Message, state: FSMContext, bot: Bot) -> None:
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    bio = await bot.download_file(file.file_path)
    image_b64 = base64.b64encode(bio.read()).decode()

    await state.update_data(source_image_b64=image_b64)
    await state.set_state(ImageMode.waiting_i2i_prompt)
    logger.info("I2I photo received from user %d (%d bytes)", message.from_user.id, len(image_b64))
    await message.answer("✏️ Теперь опиши, что хочешь изменить или получить:")


@router.message(ImageMode.waiting_i2i_photo, F.document)
async def handle_i2i_document(message: Message, state: FSMContext) -> None:
    await message.answer(
        "⚠️ Пожалуйста, отправь как <b>фото</b>, а не как файл.\n"
        "Нажми скрепку → выбери фото → отправь без галочки «Файл».",
        parse_mode="HTML",
    )


@router.message(ImageMode.waiting_i2i_photo)
async def handle_i2i_photo_invalid(message: Message, state: FSMContext) -> None:
    if message.text and message.text in MENU_BUTTONS:
        await state.clear()
        return
    await message.answer("🖼️ Пожалуйста, пришли фото (не файл и не текст).")


# ── Image-to-Image: receive prompt ───────────────────────────

@router.message(ImageMode.waiting_i2i_prompt)
async def handle_i2i_prompt(message: Message, state: FSMContext) -> None:
    if not message.text or message.text in MENU_BUTTONS:
        await state.clear()
        return

    data = await state.get_data()
    model_id = data.get("img_model", "nano-banana")
    model_label = data.get("img_model_label", model_id)
    source_b64 = data.get("source_image_b64")
    logger.info("I2I from user %d: model=%s prompt=%s", message.from_user.id, model_id, message.text[:80])

    status_msg = await message.answer("🎨 Генерирую...")
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")

    try:
        image_url = await polza.generate_image(
            prompt=message.text, model=model_id, image_b64=source_b64,
        )
    except TimeoutError:
        logger.warning("I2I timeout for user %d", message.from_user.id)
        await status_msg.edit_text("⏳ Генерация заняла слишком долго. Попробуй позже.")
        await state.clear()
        return
    except Exception as e:
        logger.error("I2I error for user %d: %s", message.from_user.id, e)
        await status_msg.edit_text("❌ Ошибка генерации. Попробуй другой промпт или модель.")
        await state.clear()
        return

    await update_last_active(message.from_user.id)
    await status_msg.delete()

    try:
        photo = URLInputFile(image_url)
        await message.answer_photo(
            photo=photo,
            caption=f"✅ Готово! Модель: {model_label}",
            reply_markup=main_menu_keyboard(),
        )
        logger.info("I2I result sent to user %d", message.from_user.id)
    except Exception as e:
        logger.error("Failed to send image to user %d: %s", message.from_user.id, e)
        await message.answer(
            "⚠️ Не удалось отправить изображение. Попробуй ещё раз.",
            reply_markup=main_menu_keyboard(),
        )

    await state.clear()
