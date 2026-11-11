import pytest


@pytest.fixture
def auth_headers(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "wallet-test@finstack.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "email": "wallet-test@finstack.com",
            "password": "StrongPassword123!",
        },
    )

    token = login.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def test_create_wallet(client, auth_headers):
    response = client.post(
        "/wallets",
        json={"currency": "NGN"},
        headers=auth_headers,
    )

    assert response.status_code == 201

    data = response.json()
    assert data["currency"] == "NGN"
    assert data["balance"] == "0.00"
    assert "id" in data


def test_get_wallet(client, auth_headers):
    created = client.post(
        "/wallets",
        json={"currency": "NGN"},
        headers=auth_headers,
    )

    wallet_id = created.json()["id"]

    response = client.get(
        f"/wallets/{wallet_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == wallet_id


def test_get_wallet_balance(client, auth_headers):
    created = client.post(
        "/wallets",
        json={"currency": "NGN"},
        headers=auth_headers,
    )

    wallet_id = created.json()["id"]

    response = client.get(
        f"/wallets/{wallet_id}/balance",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["balance"] == "0.00"


def test_get_nonexistent_wallet(client, auth_headers):
    import uuid

    response = client.get(
        f"/wallets/{uuid.uuid4()}",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_invalid_wallet_currency(client, auth_headers):
    response = client.post(
        "/wallets",
        json={"currency": "naira"},
        headers=auth_headers,
    )

    assert response.status_code == 422
