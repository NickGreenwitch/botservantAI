from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from config import CHANNEL_ID
from database import add_user, update_subscription
from keyboards import subscription_keyboard, main_menu_keyboard

router = Router()


async def check_user_subscribed(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    if user is None:
        return
    await add_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
    )
    name = user.first_name or user.full_name
    text = (
        f"👋 Привет, {name}! Я — ServantAI, твой ИИ-помощник.\n\n"
        "Чтобы начать, подпишись на канал @yandertakerai "
        "и нажми кнопку «Проверить подписку»."
    )
    await message.answer(text, reply_markup=subscription_keyboard())


@router.callback_query(F.data == "check_subscription")
async def callback_check_subscription(callback: CallbackQuery, bot: Bot) -> None:
    user = callback.from_user
    if user is None:
        return
    is_subscribed = await check_user_subscribed(bot, user.id)
    if is_subscribed:
        await update_subscription(user.id, True)
        await callback.message.edit_text("✅ Подписка подтверждена! Добро пожаловать!")
        await callback.message.answer(
            "Выбери действие из меню 👇", reply_markup=main_menu_keyboard()
        )
    else:
        await callback.answer("❌ Ты ещё не подписан. Подпишись и нажми снова.", show_alert=True)
