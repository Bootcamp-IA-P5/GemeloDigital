def test_create_roadmap_authenticated(client, auth_headers):
    payload = {
        "user_id": "will-be-overridden",
        "approach": "GENERALIST"
    }
    
    response = client.post("/api/roadmap", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["trajectory"] == "A"

def test_create_roadmap_unauthenticated(client):
    response = client.post("/api/roadmap", json={
        "user_id": "test",
        "approach": "GENERALIST"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
