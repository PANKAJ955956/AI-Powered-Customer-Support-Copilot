import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from backend.app.main import app
from backend.app.database.connection import get_session
from backend.app.database.models import User, Customer, Ticket
from backend.app.api.auth import get_password_hash
from backend.app.tools.crm_tools import get_customer_profile, check_order_status
from backend.app.memory.memory_manager import memory_manager

# Setup separate in-memory SQLite database for testing
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)

# Force the CRM tools to run against the in-memory test database during tests
import backend.app.tools.crm_tools
backend.app.tools.crm_tools.engine = engine

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_user_registration(client: TestClient):
    response = client.post(
        "/api/auth/register",
        data={"email": "new_agent@copilot.com", "password": "newpassword123", "role": "Agent"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new_agent@copilot.com"
    assert data["role"] == "Agent"

def test_user_login(client: TestClient, session: Session):
    # Seed a user directly
    user = User(email="test_agent@copilot.com", hashed_password=get_password_hash("password123"), role="Agent")
    session.add(user)
    session.commit()
    
    response = client.post(
        "/api/auth/login",
        data={"username": "test_agent@copilot.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test_agent@copilot.com"

def test_crm_tools_execution(session: Session):
    # Seed a customer
    cust = Customer(name="John Doe", email="john@doe.com", phone="+1-000-0000", subscription_plan="Enterprise", billing_status="Paid")
    session.add(cust)
    session.commit()
    session.refresh(cust)
    
    # Run the langchain tool function directly
    profile_data = get_customer_profile.invoke({"customer_id": cust.id})
    assert "John Doe" in profile_data
    assert "Enterprise" in profile_data

def test_local_memory_fallback(session: Session):
    cust = Customer(name="Jane Doe", email="jane@doe.com", phone="+1-000-0001", subscription_plan="Growth", billing_status="Paid")
    session.add(cust)
    session.commit()
    session.refresh(cust)
    
    # Save a memory text block
    memory_manager.add_memory(cust.id, "User requested billing reminder on the 10th.", db_session=session)
    
    memories = memory_manager.get_memories(cust.id, db_session=session)
    assert len(memories) > 0
    # Clean up test.db file after run
    if os.path.exists("./test.db"):
        try:
            os.remove("./test.db")
        except Exception:
            pass
