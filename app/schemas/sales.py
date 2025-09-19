from pydantic import BaseModel, field_validator
from datetime import date

# Pydantic schema for validating product creation
class SaleCreate(BaseModel):
    product_id: int
    sale_price: float
    sale_start: date
    sale_end: date

    @field_validator('sale_end')
    @classmethod
    def end_date_after_start_date(cls, v, info):
        if 'sale_start' in info.data and v < info.data['sale_start']:
            raise ValueError('End date must be after start date')
        return v