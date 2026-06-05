import os
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

JWT_SECRET = os.getenv("JWT_SECRET", "fitstack-dev-jwt-secret-change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(
        self,
        subject: str,
        expires_delta: timedelta | None = None,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        expire = datetime.now(UTC) + (
            expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        payload: dict[str, Any] = {"sub": subject, "exp": expire}
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def decode_access_token(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

    def get_user_id_from_token(self, token: str) -> UUID:
        try:
            payload = self.decode_access_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise JWTError("Missing subject")
            return UUID(user_id)
        except (JWTError, ValueError) as exc:
            raise JWTError("Invalid token") from exc
