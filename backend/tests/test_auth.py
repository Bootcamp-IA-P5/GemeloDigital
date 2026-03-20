from app.models import User

def test_register_success(client, db):
    response = client.post("/auth/register", json={
        "email": "newuser@example.com",
        "password": "strongpassword",
        "nombre": "New User"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Verify user was saved
    user = db.query(User).filter(User.email == "newuser@example.com").first()
    assert user is not None
    assert user.name == "New User"

def test_register_duplicate_email(client, test_user):
    response = client.post("/auth/register", json={
        "email": test_user.email,
        "password": "anotherpassword",
        "nombre": "Duplicate"
    })
    
    assert response.status_code == 409
    assert "registrado" in response.json()["detail"]

def test_login_success(client, test_user):
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_login_invalid_password(client, test_user):
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401
    assert "Credenciales inválidas" in response.json()["detail"]

def test_login_invalid_email(client):
    response = client.post("/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "password123"
    })
    
    assert response.status_code == 401
