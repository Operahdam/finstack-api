
def register(client, email="boss@finstack.com"):
    return client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
        },
    )


def test_user_registration(client):
    response = register(client)

    assert response.status_code == 201
    assert response.json()["email"] == "boss@finstack.com"
    assert "password_hash" not in response.json()


def test_duplicate_registration(client):
    register(client)

    response = register(client)

    assert response.status_code == 409


def test_user_login(client):
    register(client)

    response = client.post(
        "/auth/login",
        json={
            "email": "boss@finstack.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_invalid_password(client):
    register(client)

    response = client.post(
        "/auth/login",
        json={
            "email": "boss@finstack.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_get_authenticated_user(client):
    register(client)

    login = client.post(
        "/auth/login",
        json={
            "email": "boss@finstack.com",
            "password": "StrongPassword123!",
        },
    )

    token = login.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "boss@finstack.com"


def test_authenticated_endpoint_without_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
