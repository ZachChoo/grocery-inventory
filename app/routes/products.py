from fastapi import APIRouter, HTTPException

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
    
@router.delete("/{upc}")
def delete_product(upc: int):
    with SessionLocal() as session:
        product_to_delete = session.query(Product).filter(Product.upc == upc).first()
        if product_to_delete:
            session.delete(product_to_delete)
            session.commit()
            return {"message": "Product deleted!"}
        else:
            raise HTTPException(status_code=404, detail="Product not found!")