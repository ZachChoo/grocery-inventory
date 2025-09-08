from sqlalchemy import Column, Integer, String, Float

from app.database import Base

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    upc = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Integer)
    price = Column(Float, nullable=False)
    report_code = Column(Integer)
    reorder_threshold = Column(Integer)