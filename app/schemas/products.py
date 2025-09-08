from pydantic import BaseModel

# Pydantic schema for validating product creation
class ProductCreate(BaseModel):
    upc: int
    name: str
    quantity: int
    price: float
    reorder_threshold: int