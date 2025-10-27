import schedule
import time
from weather_etl.pipeline import run_etl

schedule.every().day.at("09:00").do(run_etl)

print("Scheduler started. Running daily at 09:00...")
while True:
    schedule.run_pending()
    time.sleep(60)
