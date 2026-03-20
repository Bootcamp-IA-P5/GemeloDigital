import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.main import app
from app.database import Base, get_db
from app.models import User
from app.core.security import get_password_hash, create_access_token

# InMemory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db):
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("password123"),
        name="Test User",
        role="user",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(data={"user_id": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(autouse=True)
def mock_services():
    """Mock LLM services to prevent actual API calls during testing"""
    with patch("app.api.routes.profile.profile_service") as mock_prof, \
         patch("app.api.routes.roadmap.roadmap_service") as mock_road:
        
        # Mock profile return
        mock_prof.create_profile.return_value = {
            "user_id": "mock-user-id",
            "profile_id": "mock-profile-id",
            "current_role": "Developer",
            "target_role": "Cloud Engineer",
            "experience_years": 3,
            "competencies": [
                {
                    "id": "py-1",
                    "label": "Python",
                    "domain": "General",
                    "current_level": 3,
                    "target_level": 4,
                    "gap": 1,
                    "score": 0.75
                }
            ],
            "recommended_approach": "GENERALIST",
            "summary": "Mock profile summary"
        }
        
        # Mock roadmap return
        mock_road.generate_roadmap.return_value = {
            "roadmap_id": "mock-roadmap-id",
            "user_id": "mock-user-id",
            "trajectory": "A",
            "phases": [{"phase_order": 1, "name": "Testing", "blocks": []}]
        }
        
        yield
