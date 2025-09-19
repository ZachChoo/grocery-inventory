from sqlalchemy import Column, Integer, Float, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

class Sale(Base):
    __tablename__ = 'sales'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    sale_price = Column(Float, nullable=False)
    sale_start = Column(Date, nullable=False)
    sale_end = Column(Date, nullable=False)

    product = relationship(
        'Product',
        back_populates='sales'
        )