from unittest.mock import AsyncMock


# ── GET /users/me ──────────────────────────────────────────────────────────────

def test_get_users_me_requires_auth(client) -> None:
    response = client.get("/users/me")
    assert response.status_code == 401


def test_get_users_me_returns_current_user(auth_client, auth_user) -> None:
    response = auth_client.get("/users/me")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(auth_user.id)
    assert body["email"] == auth_user.email


# ── PUT /users/me ──────────────────────────────────────────────────────────────

def test_put_users_me_requires_auth(client) -> None:
    response = client.put("/users/me", json={"sex": "male"})
    assert response.status_code == 401


def test_put_users_me_updates_sex_and_dob(auth_client, db_session, auth_user) -> None:
    response = auth_client.put(
        "/users/me",
        json={"sex": "female", "date_of_birth": "1990-05-20"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["sex"] == "female"
    assert body["date_of_birth"] == "1990-05-20"
    assert auth_user.sex == "female"
    db_session.commit.assert_awaited_once()


def test_put_users_me_partial_update_leaves_other_fields(
    auth_client, auth_user
) -> None:
    """Only fields present in the payload are touched."""
    auth_user.sex = "male"

    response = auth_client.put("/users/me", json={"date_of_birth": "1985-01-01"})

    assert response.status_code == 200
    body = response.json()
    assert body["date_of_birth"] == "1985-01-01"
    assert body["sex"] == "male"  # untouched


def test_put_users_me_rejects_future_dob(auth_client) -> None:
    response = auth_client.put("/users/me", json={"date_of_birth": "3000-01-01"})
    assert response.status_code == 422


def test_put_users_me_rejects_invalid_sex(auth_client) -> None:
    response = auth_client.put("/users/me", json={"sex": "robot"})
    assert response.status_code == 422
