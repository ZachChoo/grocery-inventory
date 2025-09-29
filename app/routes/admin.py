from fastapi import APIRouter #, Depends
#from typing import Annotated

#from app.models.user import User
from app.services.notifications import notification_service
#from app.core.security import require_role


router = APIRouter()
# TODO: might want to add _: Annotated[User, Depends(require_role("manager"))]
# Simple manual test endpoint
@router.post("/notify-sales")
def manual_check():
    notifications_sent = notification_service.process_expiring_sales()
    return {
        "message": f"Checked sales. {notifications_sent} notifications sent.",
        "notifications_sent": notifications_sent
    }