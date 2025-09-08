from fastapi import APIRouter

from app.models.product import Product
from app.schemas.products import ProductCreate
from app.database import SessionLocal

router = APIRouter()

@router.get("/")
def get_products():
    with SessionLocal() as session:
        products = session.query(Product).all()
        return {"products": products}
    
@router.post("/")
def create_product(product_data: ProductCreate):
    with SessionLocal() as session:
        new_product = Product(**product_data.model_dump())
        session.add(new_product)
        session.commit()
        return {"message": "Product created!"}