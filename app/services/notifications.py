from datetime import datetime, timedelta
import logging
from typing import List

from app.database import SessionLocal
from app.models.sale import Sale
from app.models.user import User
from app.services.emails import email_service

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.notifications_sent = []  # Simple in-memory storage for demo
    
    def get_managers_with_email(self) -> List[str]:
        """Get email addresses of managers who want notifications"""
        with SessionLocal() as session:
            managers = session.query(User).filter(
                User.role == 'manager',
                User.email.isnot(None)
            ).all()
            return [manager.email for manager in managers]
    
    def check_expiring_sales(self, days_ahead: int = 30) -> List[Sale]:
        """Find sales expiring within X days"""
        cutoff_date = datetime.now().date() + timedelta(days=days_ahead)
        
        with SessionLocal() as session:
            expiring_sales = session.query(Sale).filter(
                Sale.sale_end <= cutoff_date,
                Sale.sale_end >= datetime.now().date()
            ).all()
            return [{
                "sale_end": sale.sale_end,
                "sale_price": sale.sale_price,
                "product": {"name": sale.product.name}
            } for sale in expiring_sales]

    def send_notification_email(self, manager_emails: List[str], expiring_sales: List[Sale]) -> bool:
        """Send email notification about expiring sales"""
        if not manager_emails or not expiring_sales:
            return False
        
        try:
            email_service.send_sale_notification_email(manager_emails, expiring_sales)
            
            # Store for testing
            self.notifications_sent.append({
                "sent_at": datetime.now(),
                "recipients": manager_emails,
                "sales_count": len(expiring_sales)
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    def process_expiring_sales(self) -> int:
        """Main function: check sales and send notifications"""
        expiring_sales = self.check_expiring_sales(days_ahead=30)
        if not expiring_sales:
            logger.info("No expiring sales found")
            return 0
        
        manager_emails = self.get_managers_with_email()
        if not manager_emails:
            logger.warning("No managers found to notify")
            return 0
        
        success = self.send_notification_email(manager_emails, expiring_sales)
        return 1 if success else 0


# Global instance
notification_service = NotificationService()