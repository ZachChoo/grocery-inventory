from fastapi import FastAPI

from app.database import engine, Base
from app.routes.products import router as products_router
from app.routes.users import router as users_router
from app.routes.sales import router as sales_router
from app.config import settings

from app.scheduler import start_scheduler, scheduler
from app.services.notifications import notification_service

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    debug=settings.DEBUG
)

@app.on_event("startup")
async def startup_event():
    start_scheduler()

Base.metadata.create_all(engine)

app.include_router(products_router, prefix="/products", tags=["products"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(sales_router, prefix="/sales", tags=["sales"])

@app.get("/")
async def root():
    return {
        "message": "Hello World",
        "scheduler_running": scheduler.running if 'scheduler' in globals() else False
        }

# Simple manual test endpoint
@app.post("/admin/check-sales")
async def manual_check():
    notifications_sent = notification_service.process_expiring_sales()
    return {
        "message": f"Checked sales. {notifications_sent} notifications sent.",
        "notifications_sent": notifications_sent
    }