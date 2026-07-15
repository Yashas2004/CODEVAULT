import os, redis
from dotenv import load_dotenv
load_dotenv()


def make_redis_client(url: str):
    return redis.from_url(url, decode_responses=True)


redis_client = make_redis_client(os.getenv("REDIS_URL"))


def get_redis():
    """FastAPI dependency that yields the app's Redis client.
    Tests override this to point at TEST_REDIS_URL instead, the same
    way conftest.py overrides get_db to point at TEST_DATABASE_URL."""
    return redis_client