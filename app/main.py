from fastapi import FastAPI

from app.database import engine, Base, SessionLocal
from app.routes.products import router as products_router
from app.routes.sales import router as sales_router

app = FastAPI()

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

app.include_router(products_router, prefix="/products", tags=["products"])
app.include_router(sales_router, prefix="/sales", tags=["sales"])

@app.get("/")
async def root():
    return {"message": "Hello World"}