from fastapi import APIRouter

from app.models.sale import Sale
from app.schemas.sales import SaleCreate
from app.database import SessionLocal

router = APIRouter()

@router.get("/")
def get_sales():
    with SessionLocal() as session:
        sales = session.query(Sale).all()
        return {"sales": sales}
    
@router.post("/")
def create_sale(sale_data: SaleCreate):
    with SessionLocal() as session:
        new_sale = Sale(**sale_data.model_dump())
        session.add(new_sale)
        session.commit()
        return {"message": "Sale created!"}