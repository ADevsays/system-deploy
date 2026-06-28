import aiosqlite
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS elevenlabs_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    character_limit INTEGER NOT NULL DEFAULT 10000,
    characters_used INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(settings.ELEVENLABS_DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    logger.info(f"Initializing ElevenLabs database at {settings.ELEVENLABS_DB_PATH}")
    async with aiosqlite.connect(settings.ELEVENLABS_DB_PATH) as db:
        await db.execute(CREATE_TABLE_SQL)
        await db.commit()
    logger.info("ElevenLabs database initialized successfully")
