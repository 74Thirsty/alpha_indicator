from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("MASTER_KEY_B64", "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=")

from app.database import Base, get_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import User, UserRole  # noqa: E402
from app.services.auth_service import pwd_context  # noqa: E402


@pytest.fixture()
def db_session(tmp_path: Path):
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def user(db_session):
    row = User(email="user@example.com", password_hash=pwd_context.hash("very-secure-password"), role=UserRole.USER)
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    return row


@pytest.fixture()
def admin(db_session):
    row = User(email="admin@example.com", password_hash=pwd_context.hash("very-secure-password"), role=UserRole.ADMIN)
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    return row


@pytest.fixture()
def client(db_session):
    app = create_app()

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c
