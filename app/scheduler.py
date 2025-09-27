from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit
import datetime

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
        trigger=CronTrigger(hour=9, minute=0),
        id='daily_notifications',
        replace_existing=True
    )
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    print("Daily notification scheduler started")