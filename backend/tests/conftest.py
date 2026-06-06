import os
import uuid
from collections.abc import AsyncGenerator, Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

os.environ["SKIP_DB_INIT"] = "1"

from app.database import get_db  # noqa: E402
from app.dependencies import get_current_user  # noqa: E402
from app.main import app  # noqa: E402
from app.models.db_models import Exercise as ExerciseORM  # noqa: E402
from app.models.db_models import User  # noqa: E402


@pytest.fixture
def db_session() -> AsyncMock:
    session = AsyncMock()
    session.execute = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )
    )
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def auth_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        name="Test User",
        training_years=2,
        goal="strength",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def client(db_session: AsyncMock) -> Iterator[TestClient]:
    async def override_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client: TestClient, auth_user: User) -> Iterator[TestClient]:
    async def override_get_current_user() -> User:
        return auth_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)
