def test_register_creates_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "admin@school.org", "password": "supersecret1", "org_name": "Riverside Charter"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "admin@school.org"
    assert body["role"] == "owner"
    assert body["organization"]["name"] == "Riverside Charter"
    assert "id" in body
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_rejects_duplicate_email(client):
    payload = {"email": "dup@school.org", "password": "supersecret1", "org_name": "Org"}

    first = client.post("/api/v1/auth/register", json=payload)
    second = client.post("/api/v1/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_login_returns_bearer_token(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "login@school.org", "password": "supersecret1", "org_name": "Org"},
    )

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "login@school.org", "password": "supersecret1"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_rejects_wrong_password(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "wrong@school.org", "password": "supersecret1", "org_name": "Org"},
    )

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "wrong@school.org", "password": "notthepassword"},
    )

    assert response.status_code == 401


def test_protected_endpoint_requires_token(client):
    response = client.get("/api/v1/incidents")

    assert response.status_code == 401
