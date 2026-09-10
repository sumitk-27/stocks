import time
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from predictor import generate_predictions

IST = pytz.timezone("Asia/Kolkata")

def run_morning_job():
    print("[Scheduler] Triggering 09:00 AM IST Pre-Market Prediction Run...")
    generate_predictions(slot="9AM_PRE_MARKET")

def run_evening_job():
    print("[Scheduler] Triggering 09:00 PM IST Evening Analysis Run...")
    generate_predictions(slot="9PM_EVENING")

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=IST)
    # Cron triggers set for 09:00 and 21:00 IST
    scheduler.add_job(run_morning_job, 'cron', hour=9, minute=0)
    scheduler.add_job(run_evening_job, 'cron', hour=21, minute=0)
    scheduler.start()
    
    print("Background Scheduler running. Configured for 09:00 IST and 21:00 IST.")
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    start_scheduler()