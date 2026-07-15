import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

from app.main import app
from app.database import Base, get_db
from app.redis_client import get_redis, redis_client

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Note: this Redis Cloud plan only supports a single logical DB (index 0),
# so true multi-DB isolation like we have for Postgres isn't available here.
# We fall back to sharing the same Redis instance as dev, and rely on
# flushing it clean before and after every test run instead.


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_redis():
    return redis_client


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_redis] = override_get_redis


@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function", autouse=True)
def flush_redis():
    """Clear Redis before AND after every test. Since this instance is
    shared with the dev server (see note above), running tests while the
    dev server is active will reset its rate-limit counters and caches —
    that's expected, not a bug."""
    redis_client.flushdb()
    yield
    redis_client.flushdb()


@pytest.fixture
def client():
    return TestClient(app)