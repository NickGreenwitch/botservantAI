import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject, BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from typing import Any, Awaitable, Callable

from config import BOT_TOKEN, CHANNEL_ID
from database import init_db
from keyboards import subscription_keyboard

from handlers import start, menu, chat, images, video

logger = logging.getLogger(__name__)


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Allow /start and /help commands through
        if isinstance(event, Message) and event.text:
            if event.text.startswith("/start") or event.text.startswith("/help"):
                return await handler(event, data)

        # Allow subscription check callback through
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            return await handler(event, data)

        # Determine the user
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        if user is None:
            return await handler(event, data)

        # Check subscription
        bot: Bot = data["bot"]
        try:
            member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user.id)
            is_subscribed = member.status in ("member", "administrator", "creator")
        except Exception:
            is_subscribed = False

        if is_subscribed:
            return await handler(event, data)

        # Not subscribed — show subscription prompt
        logger.info("Blocked unsubscribed user %d", user.id)
        text = (
            "❌ Для использования бота необходима подписка на канал @yandertakerai.\n\n"
            "Подпишись и нажми «Проверить подписку»."
        )
        if isinstance(event, Message):
            await event.answer(text, reply_markup=subscription_keyboard())
        elif isinstance(event, CallbackQuery):
            await event.answer(
                "❌ Ты ещё не подписан. Подпишись и нажми снова.",
                show_alert=True,
            )
        return None


async def on_startup(bot: Bot) -> None:
    """Set bot commands menu and log startup."""
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Справка о возможностях"),
    ])
    logger.info("Bot commands registered, startup complete.")


async def on_shutdown(bot: Bot) -> None:
    """Graceful shutdown: close bot session."""
    logger.info("Shutting down ServantAI...")
    await bot.session.close()
    logger.info("Bot session closed.")


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    logger.info("Initializing database...")
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Lifecycle hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Register middleware on both message and callback_query
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    # Include routers — order matters:
    # start first, then images & video (own FSM + menu buttons), then menu, then chat
    dp.include_router(start.router)
    dp.include_router(images.router)
    dp.include_router(video.router)
    dp.include_router(menu.router)
    dp.include_router(chat.router)

    logger.info("Starting ServantAI bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
