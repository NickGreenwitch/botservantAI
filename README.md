# 🤖 ServantAI — Telegram ИИ-бот

Telegram-бот с доступом к нейросетям для текстового чата, генерации изображений и видео через [Polza AI API](https://polza.ai).

## Возможности

- **💬 Чат с ИИ** — диалог с нейросетями (GPT-5 Mini, Claude Sonnet 4.6, Gemini 3 Flash, Grok 4.1 Fast, DeepSeek v3.2)
- **🖼️ Генерация изображений** — Text-to-Image и Image-to-Image (Nano Banana, Grok Image, Seedream 5.0 Lite)
- **🎬 Генерация видео** — Text-to-Video и Image-to-Video (Veo 3.1 Fast, Sora 2, Kling 3.0)
- **🤖 Выбор модели** — переключение между текстовыми моделями ИИ
- **👤 Профиль** — информация о пользователе и настройках
- **Проверка подписки** — доступ только для подписчиков канала

## Стек

- Python 3.11+
- [aiogram 3](https://docs.aiogram.dev/) — Telegram Bot API
- [aiosqlite](https://github.com/omnilib/aiosqlite) — асинхронный SQLite
- [aiohttp](https://docs.aiohttp.org/) — HTTP-клиент для Polza AI API
- [python-dotenv](https://github.com/theskumar/python-dotenv) — переменные окружения

## Установка

```bash
git clone https://github.com/NickGreenwitch/botservantAI.git
cd botservantAI
pip install -r requirements.txt
```

## Настройка

Скопируй `.env.example` в `.env` и заполни:

```bash
cp .env.example .env
```

```env
BOT_TOKEN=токен_бота_из_BotFather
POLZA_API_KEY=ключ_api_из_polza.ai/dashboard
CHANNEL_ID=@yandertakerai
```

### Где взять токены

| Параметр | Источник |
|----------|----------|
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) → /newbot |
| `POLZA_API_KEY` | [polza.ai/dashboard/api-keys](https://polza.ai/dashboard/api-keys) |
| `CHANNEL_ID` | Username канала с `@` (например `@yandertakerai`) |

## Запуск

```bash
python bot.py
```

Бот запустится и начнёт принимать сообщения. Логи выводятся в stdout.

## Структура проекта

```
servant_ai/
├── bot.py              # Точка входа, middleware, lifecycle
├── config.py           # Переменные окружения и списки моделей
├── database.py         # SQLite: таблица users
├── keyboards.py        # Все клавиатуры (inline + reply)
├── handlers/
│   ├── start.py        # /start, /help, проверка подписки
│   ├── menu.py         # Главное меню, выбор модели, профиль
│   ├── chat.py         # Текстовый чат с LLM
│   ├── images.py       # Генерация изображений (t2i + i2i)
│   └── video.py        # Генерация видео (t2v + i2v)
├── services/
│   └── polza.py        # Клиент Polza AI API
├── .env.example
├── requirements.txt
└── README.md
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Запуск бота, проверка подписки |
| `/help` | Справка о возможностях |

## Лицензия

MIT
