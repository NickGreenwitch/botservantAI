import aiosqlite
from datetime import datetime

DB_PATH = "servant_ai.db"


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                is_subscribed BOOLEAN DEFAULT FALSE,
                selected_model TEXT DEFAULT 'auto',
                created_at DATETIME,
                last_active DATETIME
            )
            """
        )
        await db.commit()


async def add_user(user_id: int, username: str | None, full_name: str) -> None:
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO users (user_id, username, full_name, is_subscribed, selected_model, created_at, last_active)
            VALUES (?, ?, ?, FALSE, 'auto', ?, ?)
            """,
            (user_id, username, full_name, now, now),
        )
        await db.commit()


async def get_user(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)


async def update_subscription(user_id: int, is_subscribed: bool) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_subscribed = ? WHERE user_id = ?",
            (is_subscribed, user_id),
        )
        await db.commit()


async def update_selected_model(user_id: int, model: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET selected_model = ? WHERE user_id = ?",
            (model, user_id),
        )
        await db.commit()


async def update_last_active(user_id: int) -> None:
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET last_active = ? WHERE user_id = ?",
            (now, user_id),
        )
        await db.commit()
