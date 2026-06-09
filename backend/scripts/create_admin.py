"""One-off: create (or reset) a FitStack admin account directly in the database.

Admins are stored as rows in the `admins` table, so an admin created this way
persists across redeploys — no `ADMIN_EMAIL`/`ADMIN_PASSWORD` app settings needed
(those exist only to bootstrap a fresh environment on first boot).

Usage — run from the `backend/` directory with DATABASE_URL pointing at the
target database (your dev-IP firewall rule must allow access to prod Postgres):

    # PowerShell — create (prompts for the password):
    $env:DATABASE_URL = 'postgresql+asyncpg://USER:PASS@HOST:5432/fitstack_db'
    python -m scripts.create_admin admin@example.com

    # Reset an existing admin's password:
    python -m scripts.create_admin admin@example.com --password 'NewStrongPass' --force

By default this is idempotent: if the admin already exists it reports and exits
without changing anything. Pass --force to update the existing admin's password.

PowerShell password gotchas (these bite on Windows):
  * Use SINGLE quotes for both DATABASE_URL and --password. Double quotes expand
    `$word` as a variable, so a `$` in either password is silently mangled.
  * DATABASE_URL is a URL: percent-encode reserved chars in the password
    (@ -> %40, : -> %3A, / -> %2F, # -> %23, % -> %25).
  * Easiest: copy the known-good string straight from Key Vault —
    $env:DATABASE_URL = az keyvault secret show --vault-name fitstack-kv `
        --name DATABASE-URL --query value -o tsv
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


async def _run(email: str, password: str, force: bool) -> None:
    await _ensure_tables()
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Admin).where(Admin.email == email))
        existing = result.scalar_one_or_none()

        if existing is not None:
            if not force:
                print(
                    f"Admin '{email}' already exists — nothing to do "
                    f"(pass --force to reset the password)."
                )
                return
            existing.hashed_password = pwd_context.hash(password)
            await db.commit()
            print(f"Reset password for admin '{email}'.")
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
    parser.add_argument(
        "--force",
        action="store_true",
        help="If the admin already exists, reset its password instead of skipping",
    )
    args = parser.parse_args()

    password = args.password or getpass.getpass("Admin password: ")
    if len(password) < 8:
        parser.error("password must be at least 8 characters")

    asyncio.run(_run(args.email, password, args.force))


if __name__ == "__main__":
    main()
