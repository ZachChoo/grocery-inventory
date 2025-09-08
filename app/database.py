from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///./grocery_inventory.db", echo=True)

Base = declarative_base()

SessionLocal = sessionmaker(bind=engine)
