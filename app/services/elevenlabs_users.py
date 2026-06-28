import logging
from app.core.database import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)


async def create_user(email: str, character_limit: int | None = None) -> dict:
    limit = character_limit if character_limit is not None else settings.ELEVENLABS_DEFAULT_CHARACTER_LIMIT
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO elevenlabs_users (email, character_limit) VALUES (?, ?)",
            (email, limit),
        )
        await db.commit()
        return await get_user_by_email(email)
    finally:
        await db.close()


async def get_user_by_email(email: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM elevenlabs_users WHERE email = ?", (email,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_dict(row)
    finally:
        await db.close()


async def list_users() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM elevenlabs_users ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [_row_to_dict(row) for row in rows]
    finally:
        await db.close()


async def update_user_limit(email: str, new_limit: int) -> dict | None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE elevenlabs_users SET character_limit = ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?",
            (new_limit, email),
        )
        await db.commit()
        return await get_user_by_email(email)
    finally:
        await db.close()


async def update_user_status(email: str, is_active: bool) -> dict | None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE elevenlabs_users SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?",
            (1 if is_active else 0, email),
        )
        await db.commit()
        return await get_user_by_email(email)
    finally:
        await db.close()


async def consume_characters(email: str, count: int) -> dict:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT characters_used, character_limit, is_active FROM elevenlabs_users WHERE email = ?",
            (email,),
        )
        row = await cursor.fetchone()

        if row is None:
            raise ValueError(f"User {email} not found")

        if not row["is_active"]:
            raise PermissionError(f"User {email} is deactivated")

        remaining = row["character_limit"] - row["characters_used"]
        if count > remaining:
            raise ValueError(
                f"Quota exceeded: {count} characters requested, {remaining} remaining"
            )

        await db.execute(
            "UPDATE elevenlabs_users SET characters_used = characters_used + ?, updated_at = CURRENT_TIMESTAMP WHERE email = ?",
            (count, email),
        )
        await db.commit()
        return await get_user_by_email(email)
    finally:
        await db.close()


async def reset_usage(email: str) -> dict | None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE elevenlabs_users SET characters_used = 0, updated_at = CURRENT_TIMESTAMP WHERE email = ?",
            (email,),
        )
        await db.commit()
        return await get_user_by_email(email)
    finally:
        await db.close()


async def delete_user(email: str) -> bool:
    db = await get_db()
    try:
        cursor = await db.execute(
            "DELETE FROM elevenlabs_users WHERE email = ?", (email,)
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


def _row_to_dict(row) -> dict:
    d = dict(row)
    d["is_active"] = bool(d["is_active"])
    d["characters_remaining"] = d["character_limit"] - d["characters_used"]
    return d
