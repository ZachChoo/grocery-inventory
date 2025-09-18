from fastapi import APIRouter, HTTPException

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
    
@router.delete("/{sale_id}")
def delete_sale(sale_id: int):
    with SessionLocal() as session:
        sale_to_delete = session.query(Sale).filter(Sale.id == sale_id).first()
        if sale_to_delete:
            session.delete(sale_to_delete)
            session.commit()
            return {"message": "Sale deleted!"}
        else:
            raise HTTPException(status_code=404, detail="Sale not found!")