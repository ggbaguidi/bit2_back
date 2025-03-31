import logging
import time

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

from bit2_api.right_adapters.web_scraper import ScraperRepository

executors = {
    "default": ThreadPoolExecutor(max_workers=3)  # Adjust max_workers as needed
}

MONTH = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]
YEARS = ["2023", "2024", "2025"]

# Global variable to maintain current month (e.g., "mars 2025")
current_month = "mars 2025"
current_draw = ""  # Optionally, set a draw filter like "Fortune" or "Star" if needed
wait_time = 1  # Default wait time for Selenium operations


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_previous_month(month: str, year: str) -> str:
    """
    Given the month and year in "month year" format,
    return the previous month in the same format.
    """
    month_index = MONTH.index(month)
    if month_index == 0:
        # If it's January, go to December of the previous year
        previous_month = MONTH[-1]
        previous_year = str(int(year) - 1)
    else:
        # Otherwise, just go to the previous month
        previous_month = MONTH[month_index - 1]
        previous_year = year
    return f"{previous_month} {previous_year}"


def scrape_job():
    """Job to scrape game results for the current month, then update to the previous month if new results exist."""

    global current_month, wait_time, current_draw
    scraper = ScraperRepository()
    logger.info(f"Initiating scrape...")
    results = scraper.fetch_results(
        current_month, draw=current_draw, wait_time=wait_time
    )
    logger.info(f"Scraped {len(results)} results for month: {current_month}")
    # Process the results as needed

    # Here, you can store the results or process them further.
    # Optionally, update current_month based on your business logic
    # For example, to move to the previous month, you could create a helper function:
    current_month = get_previous_month("mars", "2025")
    wait_time += 1  # Increment wait time for the next scrape
    # (You may need to implement a month decrement logic based on your data.)


def start_scheduler():
    """Start the background scheduler."""
    logger.info("Starting the scheduler...")
    scheduler = BackgroundScheduler(executors=executors)
    # Schedule job to run at a desired interval (e.g., every day or hour)
    scheduler.add_job(scrape_job, "interval", seconds=10, coalesce=True)
    scheduler.start()


# if __name__ == "__main__":
#     start_scheduler()
#     # Block to keep the scheduler running
#     logger.info("Scheduler started. Press Ctrl+C to exit.")

#     while True:
#         try:
#             time.sleep(1)  # Keep the main thread alive
#         except KeyboardInterrupt:
#             logger.info("Scheduler stopped.")
#             break
