from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)

# event listener to enable foreign key constraints, only needed for SQLite
if settings.DATABASE_URL == "sqlite:///./grocery_inventory.db":
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

Base = declarative_base()

SessionLocal = sessionmaker(bind=engine)