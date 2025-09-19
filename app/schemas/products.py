from pydantic import BaseModel

# Pydantic schema for validating product creation
class ProductCreate(BaseModel):
    upc: int
    name: str
    quantity: int
    price: float
    report_code: int
    reorder_threshold: int