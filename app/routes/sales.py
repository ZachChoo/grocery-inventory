from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated
from sqlalchemy.orm import joinedload

from app.models.sale import Sale
from app.schemas.sales import SaleCreate
from app.database import SessionLocal
from app.models.user import User
from app.core.security import require_role, get_current_user
from app.config import settings

router = APIRouter()

# lists all sales
@router.get("/")
def get_sales(page: int = 1, size: int = settings.DEFAULT_PAGE_SIZE):
    if size > settings.MAX_PAGE_SIZE:
        size = settings.MAX_PAGE_SIZE
    with SessionLocal() as session:
        skip = (page - 1) * size
        sales = session.query(Sale).options(joinedload(Sale.product)).offset(skip).limit(size).all()
        return {
            "sales": sales,
            "page": page,
            "size": size
        }
    
# creates a sale, must be logged in
@router.post("/")
def create_sale(sale_data: SaleCreate, _: Annotated[User, Depends(get_current_user)]):
    with SessionLocal() as session:
        try:
            new_sale = Sale(**sale_data.model_dump())
            session.add(new_sale)
            session.commit()
            return {"message": "Sale created!"}
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid sale")
    
# deletes a sale, must be a manager
@router.delete("/{sale_id}")
def delete_sale(sale_id: int, _: Annotated[User, Depends(require_role("manager"))]):
    with SessionLocal() as session:
        sale_to_delete = session.query(Sale).filter(Sale.id == sale_id).first()
        if sale_to_delete:
            session.delete(sale_to_delete)
            session.commit()
            return {"message": "Sale deleted!"}
        else:
            raise HTTPException(status_code=404, detail="Sale not found!")