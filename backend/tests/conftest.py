import os
from collections.abc import AsyncGenerator, Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

os.environ["SKIP_DB_INIT"] = "1"

from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.db_models import Exercise as ExerciseORM  # noqa: E402


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
def client(db_session: AsyncMock) -> Iterator[TestClient]:
    async def override_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
