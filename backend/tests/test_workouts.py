from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_REQUEST = {
    "goal": "strength",
    "experience_level": "beginner",
    "days_per_week": 3,
    "equipment": ["barbell"],
}


def test_generate_workout_returns_200() -> None:
    response = client.post("/workouts/generate", json=VALID_REQUEST)
    assert response.status_code == 200


def test_generate_workout_returns_expected_shape() -> None:
    response = client.post("/workouts/generate", json=VALID_REQUEST)
    workout = response.json()

    assert workout.keys() == {"name", "description", "exercises"}
    assert isinstance(workout["exercises"], list)
    assert workout["exercises"]
    for exercise in workout["exercises"]:
        assert {"exercise_id", "name", "sets", "reps"} <= exercise.keys()
        assert isinstance(exercise["sets"], int)


def test_generate_workout_defaults_equipment_to_empty_list() -> None:
    request = {key: value for key, value in VALID_REQUEST.items() if key != "equipment"}
    response = client.post("/workouts/generate", json=request)
    assert response.status_code == 200


def test_generate_workout_rejects_missing_required_field() -> None:
    request = {key: value for key, value in VALID_REQUEST.items() if key != "goal"}
    response = client.post("/workouts/generate", json=request)
    assert response.status_code == 422


def test_generate_workout_rejects_days_per_week_out_of_range() -> None:
    for days in (0, 8):
        response = client.post(
            "/workouts/generate", json={**VALID_REQUEST, "days_per_week": days}
        )
        assert response.status_code == 422
