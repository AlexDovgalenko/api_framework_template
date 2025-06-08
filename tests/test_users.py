"""
Functional tests – each test using the `auth_headers` fixture is executed
three times (unauthenticated, Basic auth, Bearer token).
"""

import base64
import uuid

import pytest
import requests

from utils.constants import TEST_USER_EMAIL



def test_list_users(client, mock_user_details):
    response = client.get("/user/details")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json() == list(mock_user_details.values())

@pytest.mark.parametrize("user_id", ["1", "2", "3"])
def test_get_user_by_id(client, mock_user_details, user_id):
    response = client.get(f"/user/details/{user_id}")
    assert response.status_code == 200
    assert response.json() == mock_user_details[user_id]

def test_create_and_fetch_user(client: requests.Session):
    unique_email = f"{uuid.uuid4()}@example.com"

    create_response = client.post(
        "/users", json={"email": unique_email, "password": "secret"}
    )
    assert create_response.status_code == 201
    created_user_id = create_response.json()["id"]

    fetch_response = client.get(f"/users/{unique_email}")
    assert fetch_response.status_code == 200
    assert fetch_response.json() == {"id": created_user_id, "email": unique_email}


def test_duplicate_email_returns_409(client):
    duplicate_email = f"{uuid.uuid4()}@dup.com"
    client.post("/users", json={"email": duplicate_email, "password": "x"})
    conflict_response = client.post(
        "/users", json={"email": duplicate_email, "password": "x"}
    )
    assert conflict_response.status_code == 409


@pytest.mark.parametrize(
    "invalid_email", ["plain", "missing-at.com", "invalid@.com", ""]
)
def test_invalid_email_returns_422(client, invalid_email):
    response = client.post("/users", json={"email": invalid_email, "password": "x"})
    assert response.status_code == 422


@pytest.mark.usefixtures("auth_headers")
def test_protected_endpoint(client, auth_headers):
    response = client.get("/protected", headers=auth_headers)

    if not auth_headers:
        # Anonymous request must fail
        assert response.status_code == 401
    else:
        # Both Basic and Bearer must succeed
        assert response.status_code == 200
        assert response.json()["hello"] == TEST_USER_EMAIL


def test_basic_auth_with_wrong_password_fails(client):
    wrong_credentials = base64.b64encode(b"TEST_USER_EMAIL:WRONG").decode()
    response = client.get(
        "/protected", headers={"Authorization": f"Basic {wrong_credentials}"}
    )
    assert response.status_code == 401


def test_bearer_auth_with_wrong_token_fails(client):
    wrong_token = "invalid_token"
    response = client.get(
        "/protected", headers={"Authorization": f"Bearer {wrong_token}"}
    )
    assert response.status_code == 401
