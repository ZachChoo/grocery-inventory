from fastapi import FastAPI

from app.database import engine, Base, SessionLocal
from app.routes.products import router as products_router

app = FastAPI()

Base.metadata.create_all(engine)

app.include_router(products_router, prefix="/products", tags=["products"])

@app.get("/")
async def root():
    return {"message": "Hello World"}