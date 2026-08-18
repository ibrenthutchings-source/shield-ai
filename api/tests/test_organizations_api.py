def _register(client, email, org_name, password="supersecret1"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "org_name": org_name},
    )
    return response.json()


def _login(client, email, password="supersecret1"):
    response = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_owner_can_create_invite(client):
    _register(client, "owner@school.org", "Riverside Charter")
    headers = _login(client, "owner@school.org")

    response = client.post(
        "/api/v1/organizations/invites", headers=headers, json={"email": "teammate@school.org"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["invite_token"]
    assert body["expires_at"] > 0


def test_invited_user_joins_same_organization_as_member(client):
    owner = _register(client, "owner2@school.org", "Riverside Charter")
    owner_headers = _login(client, "owner2@school.org")

    invite = client.post(
        "/api/v1/organizations/invites", headers=owner_headers, json={"email": "teammate2@school.org"}
    ).json()

    response = client.post(
        "/api/v1/auth/register-invited",
        json={"invite_token": invite["invite_token"], "password": "supersecret1"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "teammate2@school.org"
    assert body["role"] == "member"
    assert body["organization"]["id"] == owner["organization"]["id"]


def test_member_cannot_create_invite(client):
    _register(client, "owner3@school.org", "Org")
    owner_headers = _login(client, "owner3@school.org")
    invite = client.post(
        "/api/v1/organizations/invites", headers=owner_headers, json={"email": "member3@school.org"}
    ).json()
    client.post(
        "/api/v1/auth/register-invited",
        json={"invite_token": invite["invite_token"], "password": "supersecret1"},
    )
    member_headers = _login(client, "member3@school.org")

    response = client.post(
        "/api/v1/organizations/invites", headers=member_headers, json={"email": "someone-else@school.org"}
    )

    assert response.status_code == 403


def test_teammates_share_visibility_into_same_incidents(client):
    _register(client, "owner4@school.org", "Org")
    owner_headers = _login(client, "owner4@school.org")
    invite = client.post(
        "/api/v1/organizations/invites", headers=owner_headers, json={"email": "member4@school.org"}
    ).json()
    client.post(
        "/api/v1/auth/register-invited",
        json={"invite_token": invite["invite_token"], "password": "supersecret1"},
    )
    member_headers = _login(client, "member4@school.org")

    client.post("/api/v1/assets", headers=owner_headers, json={"host": "shared.school.org"})

    response = client.get("/api/v1/assets", headers=member_headers)

    assert response.status_code == 200
    hosts = [a["host"] for a in response.json()]
    assert "shared.school.org" in hosts


def test_invite_rejects_already_registered_email(client):
    _register(client, "owner5@school.org", "Org")
    owner_headers = _login(client, "owner5@school.org")

    response = client.post(
        "/api/v1/organizations/invites", headers=owner_headers, json={"email": "owner5@school.org"}
    )

    assert response.status_code == 409


def test_register_invited_rejects_garbage_token(client):
    response = client.post(
        "/api/v1/auth/register-invited",
        json={"invite_token": "not-a-real-token", "password": "supersecret1"},
    )

    assert response.status_code == 400
