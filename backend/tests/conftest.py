"""Shared test setup.

The API is rate limited per client address and every TestClient request comes from the same address, so
without this the counters would carry over from one test to the next and later tests would get 429.
If you already have a conftest.py, copy this fixture into it instead of replacing the file."""
import pytest

from app.main import limiter


@pytest.fixture(autouse=True)
def reset_rate_limits():
    limiter.hits.clear()
    yield
    limiter.hits.clear()
