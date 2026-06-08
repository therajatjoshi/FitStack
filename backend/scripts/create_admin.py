"""One-off: create a FitStack admin account directly in the database.

Admins are stored as rows in the `admins` table, so an admin created this way
persists across redeploys — no `ADMIN_EMAIL`/`ADMIN_PASSWORD` app settings needed
(those exist only to bootstrap a fresh environment on first boot).

Usage — run from the `backend/` directory with DATABASE_URL pointing at the
target database (your dev-IP firewall rule must allow access to prod Postgres):

    # PowerShell
    $env:DATABASE_URL = "postgresql+asyncpg://USER:PASS@HOST:5432/fitstack_db"
    python -m scripts.create_admin joshi.rajat@gmail.com
    # (prompts for a password; or pass --password "...")

Idempotent: if an admin with that email already exists it reports and exits
without changing anything.
"""

from __future__ import annotations

import argparse
import asyncio
import getpass

from passlib.context import CryptContext
from sqlalchemy import select

from app.database import Base, AsyncSessionLocal, engine
from app.models.db_models import Admin

# Same scheme as app.services.auth_service, so the hash verifies at /admin/login.
# (Hashing only — avoids that module's import-time JWT_SECRET guard.)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def _ensure_tables() -> None:
    # Safe + idempotent — creates the admins table if a fresh DB hasn't yet.
    import app.models.db_models  # noqa: F401  (register models on Base)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _run(email: str, password: str) -> None:
    await _ensure_tables()
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(Admin).where(Admin.email == email))
        if existing.scalar_one_or_none() is not None:
            print(f"Admin '{email}' already exists — nothing to do.")
            return
        db.add(Admin(email=email, hashed_password=pwd_context.hash(password)))
        await db.commit()
        print(f"Created admin '{email}'. Log in at /admin/login.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a FitStack admin account.")
    parser.add_argument("email", help="Admin email (the /admin/login username)")
    parser.add_argument(
        "--password",
        help="Admin password (prompted securely if omitted)",
    )
    args = parser.parse_args()

    password = args.password or getpass.getpass("Admin password: ")
    if len(password) < 8:
        parser.error("password must be at least 8 characters")

    asyncio.run(_run(args.email, password))


if __name__ == "__main__":
    main()
