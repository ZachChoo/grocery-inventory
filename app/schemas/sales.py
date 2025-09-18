from pydantic import BaseModel
from datetime import date

# Pydantic schema for validating product creation
class SaleCreate(BaseModel):
    product_id: int
    sale_price: float
    sale_start: date
    sale_end: date