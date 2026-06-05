import uuid
from unittest.mock import MagicMock

from app.models.db_models import Exercise as ExerciseORM


def test_list_exercises_returns_200(client) -> None:
    response = client.get("/exercises")
    assert response.status_code == 200


def test_list_exercises_returns_expected_shape(client, db_session) -> None:
    exercise = ExerciseORM(
        id=uuid.uuid4(),
        name="Barbell Back Squat",
        muscle_group="legs",
        equipment="barbell",
        difficulty="intermediate",
    )
    db_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[exercise])))
    )

    response = client.get("/exercises")
    exercises = response.json()

    assert isinstance(exercises, list)
    assert len(exercises) == 1
    assert exercises[0].keys() == {"id", "name", "muscle_group", "equipment"}
    assert all(isinstance(value, str) and value for value in exercises[0].values())


def test_create_exercise_returns_201(client, db_session) -> None:
    exercise_id = uuid.uuid4()

    async def refresh_side_effect(obj: ExerciseORM) -> None:
        obj.id = exercise_id

    db_session.refresh.side_effect = refresh_side_effect

    response = client.post(
        "/exercises",
        json={
            "name": "Barbell Back Squat",
            "muscle_group": "legs",
            "equipment": "barbell",
            "difficulty": "intermediate",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == str(exercise_id)
    assert body["name"] == "Barbell Back Squat"
    db_session.add.assert_called_once()
    db_session.commit.assert_awaited_once()
