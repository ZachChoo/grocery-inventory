from fastapi import FastAPI

from app.database import engine, Base
from app.routes.products import router as products_router
from app.routes.users import router as users_router
from app.routes.sales import router as sales_router
from app.config import settings

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    debug=settings.DEBUG
)

Base.metadata.create_all(engine)

app.include_router(products_router, prefix="/products", tags=["products"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(sales_router, prefix="/sales", tags=["sales"])

@app.get("/")
async def root():
    return {"message": "Hello World"}