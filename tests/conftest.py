import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from unittest.mock import MagicMock

from app.database import get_session
from app.main import app
from app.models.user import User
from app.auth import hash_password, create_access_token
from app.services.vector_store import get_vector_store


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="mock_vector_store")
def mock_vector_store_fixture():
    mock = MagicMock()
    mock.add_items = MagicMock()
    mock.delete_by_invoice = MagicMock()
    mock.search = MagicMock(return_value=[])
    return mock


@pytest.fixture(name="client")
async def client_fixture(session: Session, mock_vector_store):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_vector_store] = lambda: mock_vector_store

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(session: Session) -> User:
    user = User(username="testuser", hashed_password=hash_password("password123"))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user: User) -> str:
    return create_access_token(test_user.id)


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}
