from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)

Base = declarative_base()

SessionLocal = sessionmaker(bind=engine)
