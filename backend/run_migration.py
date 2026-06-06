"""
One-off migration script: adds new columns and tables for the FitStack
profile / body-metrics / medical-safety system.

All statements use IF NOT EXISTS / IF NOT EXISTS guards so the script is
safe to re-run.

Usage (from repo root or backend/):
    # Activate the backend venv first, then:
    DATABASE_URL="postgresql+asyncpg://user:pass@host/db?sslmode=require" python run_migration.py

The script accepts either the SQLAlchemy-style URL (postgresql+asyncpg://)
or the raw asyncpg URL (postgresql://); it normalises automatically.
"""

import asyncio
import os
import re
import sys


def _to_asyncpg_dsn(url: str) -> str:
    """Strip the '+asyncpg' driver qualifier so raw asyncpg can parse the DSN."""
    return re.sub(r"^postgresql\+asyncpg://", "postgresql://", url, count=1)


# ---------------------------------------------------------------------------
# Migration steps — each is a (label, SQL) pair executed as a single statement
# ---------------------------------------------------------------------------

STEPS: list[tuple[str, str]] = [
    # ── Extend users table ──────────────────────────────────────────────────
    (
        "users: add sex column",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS sex VARCHAR(10);",
    ),
    (
        "users: add date_of_birth column",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS date_of_birth DATE;",
    ),
    (
        "users: add consent_accepted_at column",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_accepted_at TIMESTAMPTZ;",
    ),
    (
        "users: add consent_version column",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_version VARCHAR(20);",
    ),
    # ── profiles table ──────────────────────────────────────────────────────
    (
        "create profiles table",
        """
        CREATE TABLE IF NOT EXISTS profiles (
            id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id               UUID        NOT NULL
                                              REFERENCES users(id) ON DELETE CASCADE,
            height_cm             FLOAT,
            primary_goal          VARCHAR(30),
            secondary_constraint  VARCHAR(255),
            experience_level      VARCHAR(20),
            lift_competency       JSON,
            activity_level        VARCHAR(20),
            training_days_per_week INTEGER    DEFAULT 3,
            equipment             VARCHAR(30) DEFAULT 'full_gym',
            injuries_notes        TEXT,
            goal_targets          JSON,
            goal_timeline_weeks   INTEGER,
            created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT profiles_user_id_key UNIQUE (user_id)
        );
        """,
    ),
    # ── medical_flags table ─────────────────────────────────────────────────
    (
        "create medical_flags table",
        """
        CREATE TABLE IF NOT EXISTS medical_flags (
            id                  UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id             UUID    NOT NULL
                                        REFERENCES users(id) ON DELETE CASCADE,
            heart_condition     BOOLEAN NOT NULL DEFAULT FALSE,
            diabetes            BOOLEAN NOT NULL DEFAULT FALSE,
            asthma              BOOLEAN NOT NULL DEFAULT FALSE,
            joint_or_back_issues BOOLEAN NOT NULL DEFAULT FALSE,
            pregnant            BOOLEAN NOT NULL DEFAULT FALSE,
            other               BOOLEAN NOT NULL DEFAULT FALSE,
            other_notes         TEXT,
            none                BOOLEAN NOT NULL DEFAULT FALSE,
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT medical_flags_user_id_key UNIQUE (user_id)
        );
        """,
    ),
    # ── body_metrics table ──────────────────────────────────────────────────
    (
        "create body_metrics table",
        """
        CREATE TABLE IF NOT EXISTS body_metrics (
            id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id      UUID        NOT NULL
                                     REFERENCES users(id) ON DELETE CASCADE,
            weight_kg    FLOAT,
            body_fat_pct FLOAT,
            waist_cm     FLOAT,
            hip_cm       FLOAT,
            recorded_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
    ),
    # ── index on body_metrics ───────────────────────────────────────────────
    (
        "create index ix_body_metrics_user_recorded",
        """
        CREATE INDEX IF NOT EXISTS ix_body_metrics_user_recorded
            ON body_metrics (user_id, recorded_at);
        """,
    ),
]


async def run_migration() -> None:
    try:
        import asyncpg
    except ImportError:
        print("ERROR: asyncpg is not installed.  Run: pip install asyncpg", file=sys.stderr)
        sys.exit(1)

    raw_url = os.getenv("DATABASE_URL", "")
    if not raw_url:
        print(
            "ERROR: DATABASE_URL environment variable is not set.\n"
            "  Example:\n"
            "    DATABASE_URL='postgresql+asyncpg://user:pass@host/db?sslmode=require'"
            " python run_migration.py",
            file=sys.stderr,
        )
        sys.exit(1)

    dsn = _to_asyncpg_dsn(raw_url)

    print(f"Connecting to database …")
    try:
        conn = await asyncpg.connect(dsn=dsn)
    except Exception as exc:
        print(f"ERROR: could not connect — {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Connected.\n{'─' * 60}")

    try:
        for label, sql in STEPS:
            try:
                await conn.execute(sql)
                print(f"  ✓  {label}")
            except Exception as exc:
                print(f"  ✗  {label}\n     {exc}", file=sys.stderr)
                sys.exit(1)

        print(f"{'─' * 60}")
        print("All migration steps complete.\n")

        # ── Verify: list public tables ──────────────────────────────────────
        rows = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"
        )
        print("Tables in public schema:")
        for row in rows:
            print(f"  • {row['tablename']}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
