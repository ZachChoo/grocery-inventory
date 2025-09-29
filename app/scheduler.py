from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import atexit

from app.services.notifications import notification_service

scheduler = BackgroundScheduler()

def daily_notification_check():
    """Run daily at 9 AM"""
    print(f"Daily notification check at {datetime.now()}")
    notifications_sent = notification_service.process_expiring_sales()
    print(f"Sent {notifications_sent} notifications")

def start_scheduler():
    """Start daily notifications"""
    scheduler.add_job(
        func=daily_notification_check,
        trigger=CronTrigger(hour=9, minute=0, timezone="America/Los_Angeles"),
        id='daily_notifications',
        replace_existing=True
    )
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    print("Daily notification scheduler started")