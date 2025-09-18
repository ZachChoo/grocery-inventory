from fastapi import APIRouter, Depends
from typing import Annotated

from app.models.product import Product
from app.models.user import User
from app.schemas.products import ProductCreate
from app.database import SessionLocal
from app.core.security import get_current_user
from app.config import settings


router = APIRouter()

# Gets all products with pagination
@router.get("/")
def get_products(page: int = 1, size: int = settings.DEFAULT_PAGE_SIZE):
    if size > settings.MAX_PAGE_SIZE:
            size = settings.MAX_PAGE_SIZE
    with SessionLocal() as session:
        skip = (page - 1) * size
        products = session.query(Product).offset(skip).limit(size).all()
        return {
            "products": products,
            "page": page,
            "size": size
            }
    
# Creates a product. User must be logged in
@router.post("/")
def create_product(product_data: ProductCreate, _: Annotated[User, Depends(get_current_user)]):
    with SessionLocal() as session:
        new_product = Product(**product_data.model_dump())
        session.add(new_product)
        session.commit()
        return {"message": "Product created!"}