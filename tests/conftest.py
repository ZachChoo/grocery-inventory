import pytest
import os, sys

# make sure the project root (grocery-inventory) is in sys.path, not test/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from sqlalchemy import create_engine
from fastapi.testclient import TestClient
from app.config import settings

# Store original database URL
original_database_url = os.environ.get("DATABASE_URL")

# Set test database URL
os.environ["DATABASE_URL"] = settings.TEST_DATABASE_URL

# Import after setting environment variable
from app.database import Base, engine
from app.main import app

@pytest.fixture(autouse=True, scope="session")
def restore_environment():
    """Restore original environment after all tests"""
    yield
    # Restore original DATABASE_URL after all tests complete
    if original_database_url:
        os.environ["DATABASE_URL"] = original_database_url
    elif "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]