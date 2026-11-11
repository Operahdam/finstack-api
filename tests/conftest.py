
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Wallet, WalletTransaction


TEST_DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{os.getenv('DB_USER', 'finstack_user')}:"
    f"{os.getenv('DB_PASSWORD', '222444')}@"
    f"{os.getenv('DB_HOST', 'localhost')}:"
    f"{os.getenv('DB_PORT', '5432')}/"
    f"{os.getenv('DB_NAME', 'finstack_test_db')}"
)

if "finstack_test_db" not in TEST_DATABASE_URL:
    raise RuntimeError("Tests must use finstack_test_db")

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
    join_transaction_mode="create_savepoint",
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    outer_transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()

        if outer_transaction.is_active:
            outer_transaction.rollback()

        connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
@pytest.fixture
def auth_headers(client):
    # Register a test user
    register_response = client.post(
        "/auth/register",
        json={
            "email": "testuser@finstack.com",
            "password": "StrongPassword123!",
        },
    )

    assert register_response.status_code == 201

    # Log in and obtain JWT
    login_response = client.post(
        "/auth/login",
        json={
            "email": "testuser@finstack.com",
            "password": "StrongPassword123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }
