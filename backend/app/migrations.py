"""Lightweight, idempotent schema migrations.

The app has no Alembic; `Base.metadata.create_all` creates missing *tables* but
will not add new *columns* to a table that already exists in a deployed database.
This module applies additive column migrations using Postgres
`ADD COLUMN IF NOT EXISTS`, which is safe to run on every startup.

Add new `ALTER TABLE` statements here as the schema grows.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

# Each statement must be idempotent (safe to run repeatedly).
_MIGRATIONS: list[str] = [
    "ALTER TABLE workouts ADD COLUMN IF NOT EXISTS source VARCHAR(20) NOT NULL DEFAULT 'manual'",
    "ALTER TABLE workouts ADD COLUMN IF NOT EXISTS plan JSONB",
    "ALTER TABLE workouts ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ",
    "ALTER TABLE workouts ADD COLUMN IF NOT EXISTS difficulty VARCHAR(20)",
]


async def run_light_migrations(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        for statement in _MIGRATIONS:
            await conn.execute(text(statement))
