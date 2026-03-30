from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_user, update_selected_model
from keyboards import models_keyboard, main_menu_keyboard


class UserMode(StatesGroup):
    chat = State()
    images = State()
    video = State()


router = Router()


@router.message(F.text == "💬 Чат с ИИ")
async def enter_chat_mode(message: Message, state: FSMContext) -> None:
    await state.set_state(UserMode.chat)
    await message.answer(
        "💬 Режим чата с ИИ активирован.\nОтправь мне сообщение, и я отвечу!",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "🖼️ Картинки")
async def enter_images_mode(message: Message, state: FSMContext) -> None:
    await state.set_state(UserMode.images)
    await message.answer(
        "🖼️ Режим генерации картинок.\nОпиши, что хочешь увидеть!",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "🎬 Видео")
async def enter_video_mode(message: Message, state: FSMContext) -> None:
    await state.set_state(UserMode.video)
    await message.answer(
        "🎬 Генерация видео скоро будет доступна! Следите за обновлениями.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "🤖 Выбрать модель")
async def choose_model(message: Message) -> None:
    user = await get_user(message.from_user.id)
    current_model = user["selected_model"] if user else "auto"
    await message.answer(
        "Выбери модель ИИ:", reply_markup=models_keyboard(current_model)
    )


@router.callback_query(F.data.startswith("select_model:"))
async def callback_select_model(callback: CallbackQuery) -> None:
    model = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    await update_selected_model(user_id, model)
    user = await get_user(user_id)
    current_model = user["selected_model"] if user else model
    await callback.message.edit_text(
        f"✅ Модель изменена на: <b>{model}</b>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message) -> None:
    user = await get_user(message.from_user.id)
    if user is None:
        await message.answer("Профиль не найден. Отправь /start для регистрации.")
        return
    username = f"@{user['username']}" if user["username"] else "не указан"
    created = user["created_at"][:10] if user["created_at"] else "неизвестно"
    text = (
        f"👤 <b>Профиль</b>\n\n"
        f"Имя: {user['full_name']}\n"
        f"Юзернейм: {username}\n"
        f"Модель: {user['selected_model']}\n"
        f"Дата регистрации: {created}"
    )
    await message.answer(text, parse_mode="HTML")
