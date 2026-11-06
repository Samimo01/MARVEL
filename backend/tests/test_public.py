def test_campagnes_publiques_liste_vide(client):
    response = client.get("/api/v1/public/campaigns")
    assert response.status_code == 200
    assert response.json() == []


def test_cors_autorise_les_deux_frontends(client):
    for origin in ("http://localhost:5173", "http://localhost:5174"):
        response = client.get("/api/v1/health", headers={"Origin": origin})
        assert response.headers["access-control-allow-origin"] == origin


def test_cors_refuse_une_origine_inconnue(client):
    response = client.get("/api/v1/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_login_non_implemente(client):
    response = client.post("/api/v1/auth/login", json={"email": "a@b.c", "password": "x"})
    assert response.status_code == 501
