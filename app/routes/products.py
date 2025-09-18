from fastapi import APIRouter, Depends
from typing import Annotated

from app.models.product import Product
from app.models.user import User
from app.schemas.products import ProductCreate
from app.database import SessionLocal
from app.core.security import get_current_user

router = APIRouter()

# Gets all products
@router.get("/")
def get_products():
    with SessionLocal() as session:
        products = session.query(Product).all()
        return {"products": products}
    
# Creates a product. User must be logged in
@router.post("/")
def create_product(product_data: ProductCreate, _: Annotated[User, Depends(get_current_user)]):
    with SessionLocal() as session:
        new_product = Product(**product_data.model_dump())
        session.add(new_product)
        session.commit()
        return {"message": "Product created!"}