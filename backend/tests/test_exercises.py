from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_exercises_returns_200() -> None:
    response = client.get("/exercises")
    assert response.status_code == 200


def test_list_exercises_returns_expected_shape() -> None:
    response = client.get("/exercises")
    exercises = response.json()

    assert isinstance(exercises, list)
    assert len(exercises) == 3
    for exercise in exercises:
        assert exercise.keys() == {"id", "name", "muscle_group", "equipment"}
        assert all(isinstance(value, str) and value for value in exercise.values())
