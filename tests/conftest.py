import os, sys

# make sure the project root (grocery-inventory) is in sys.path, not test/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
from sqlalchemy import create_engine
from app.database import SessionLocal, Base
from app.config import settings

# bind session to the test
engine = create_engine(settings.TEST_DATABASE_URL, echo=False)
TestingSessionLocal = SessionLocal.configure(bind=engine)

@pytest.fixture(autouse=True)
def use_test_database():
    # Reset DB for each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield