import logging

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import CHANNEL_ID
from database import add_user, update_subscription
from keyboards import subscription_keyboard, main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()


async def check_user_subscribed(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    # Reset any active FSM state
    await state.clear()

    user = message.from_user
    if user is None:
        return
    await add_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
    )
    logger.info("User /start: id=%d username=%s", user.id, user.username)
    name = user.first_name or user.full_name
    text = (
        f"👋 Привет, {name}! Я — ServantAI, твой ИИ-помощник.\n\n"
        "Чтобы начать, подпишись на канал @yandertakerai "
        "и нажми кнопку «Проверить подписку»."
    )
    await message.answer(text, reply_markup=subscription_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    logger.info("User /help: id=%d", message.from_user.id)
    text = (
        "🤖 <b>ServantAI — ИИ-помощник</b>\n\n"
        "Вот что я умею:\n\n"
        "💬 <b>Чат с ИИ</b> — задай любой вопрос, и я отвечу с помощью "
        "нейросети. Можно выбрать модель: GPT-5 Mini, Claude Sonnet 4.6, "
        "Gemini 3 Flash, Grok 4.1 Fast, DeepSeek v3.2.\n\n"
        "🖼️ <b>Картинки</b> — генерация изображений по описанию (Text to Image) "
        "или на основе фото (Image to Image). Модели: Nano Banana, Grok Image, "
        "Seedream 5.0 Lite.\n\n"
        "🎬 <b>Видео</b> — создание видео по описанию (Text to Video) "
        "или из фото (Image to Video). Модели: Veo 3.1 Fast, Sora 2, Kling 3.0.\n\n"
        "🤖 <b>Выбрать модель</b> — смена текстовой модели ИИ.\n\n"
        "👤 <b>Профиль</b> — твоя информация и настройки.\n\n"
        "Команды:\n"
        "/start — перезапуск бота\n"
        "/help — эта справка"
    )
    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "check_subscription")
async def callback_check_subscription(callback: CallbackQuery, bot: Bot) -> None:
    user = callback.from_user
    if user is None:
        return
    is_subscribed = await check_user_subscribed(bot, user.id)
    if is_subscribed:
        await update_subscription(user.id, True)
        logger.info("Subscription confirmed: user_id=%d", user.id)
        await callback.message.edit_text("✅ Подписка подтверждена! Добро пожаловать!")
        await callback.message.answer(
            "Выбери действие из меню 👇", reply_markup=main_menu_keyboard()
        )
    else:
        logger.info("Subscription check failed: user_id=%d", user.id)
        await callback.answer("❌ Ты ещё не подписан. Подпишись и нажми снова.", show_alert=True)
