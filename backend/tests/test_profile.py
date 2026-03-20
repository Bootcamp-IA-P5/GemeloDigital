def test_create_profile_authenticated(client, auth_headers):
    payload = {
        "user_id": "will-be-overridden",
        "currentRole": "Developer",
        "experience": 3,
        "competencies": {"React": 3},
        "targetRole": "Cloud Engineer",
        "deadline": "6 months",
        "learningStyle": "autodidacta",
        "pace": "intensivo"
    }
    
    response = client.post("/api/profile", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["recommended_approach"] == "GENERALIST"

def test_create_profile_unauthenticated(client):
    response = client.post("/api/profile", json={
        "user_id": "test",
        "currentRole": "Dev",
        "experience": 1,
        "competencies": {},
        "targetRole": "Sen",
        "deadline": "1",
        "learningStyle": "a",
        "pace": "a"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
