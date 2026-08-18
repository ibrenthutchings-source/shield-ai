def test_create_asset_returns_risk_findings(client, auth_headers):
    response = client.post(
        "/api/v1/assets",
        headers=auth_headers,
        json={"host": "rdp.school.org", "port": 3389, "service": "rdp"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["host"] == "rdp.school.org"
    assert len(body["risk_findings"]) == 1
    assert body["risk_findings"][0]["technique_id"] == "T1021.001"


def test_create_asset_with_no_findings_has_empty_list(client, auth_headers):
    response = client.post(
        "/api/v1/assets",
        headers=auth_headers,
        json={"host": "benign.school.org", "port": 443, "service": "https", "tls_valid": True},
    )

    assert response.status_code == 201
    assert response.json()["risk_findings"] == []


def test_list_assets_scoped_to_current_user(client, auth_headers):
    client.post(
        "/api/v1/assets",
        headers=auth_headers,
        json={"host": "a.school.org"},
    )
    client.post(
        "/api/v1/assets",
        headers=auth_headers,
        json={"host": "b.school.org"},
    )

    response = client.get("/api/v1/assets", headers=auth_headers)

    assert response.status_code == 200
    hosts = {asset["host"] for asset in response.json()}
    assert hosts == {"a.school.org", "b.school.org"}


def test_assets_endpoint_requires_auth(client):
    response = client.post("/api/v1/assets", json={"host": "no-auth.school.org"})

    assert response.status_code == 401
