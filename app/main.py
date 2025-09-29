from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.routes.products import router as products_router
from app.routes.users import router as users_router
from app.routes.sales import router as sales_router
from app.routes.admin import router as admin_router
from app.config import settings

from app.scheduler import start_scheduler, scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

Base.metadata.create_all(engine)

app.include_router(products_router, prefix="/products", tags=["products"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(sales_router, prefix="/sales", tags=["sales"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])

@app.get("/")
def root():
    return {
        "message": "Hello World",
        "scheduler_running": scheduler.running if 'scheduler' in globals() else False
        }