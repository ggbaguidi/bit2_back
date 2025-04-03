import logging
import time
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler

from bit2_api.right_adapters.web_scraper import ScraperRepository

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
current_month = date.today().strftime("%B %Y").lower()  # Get current month and year
print(f"Current month: {current_month}")
# To french
current_month = (
    current_month.replace("january", "janvier")
    .replace("february", "février")
    .replace("march", "mars")
    .replace("april", "avril")
    .replace("may", "mai")
    .replace("june", "juin")
    .replace("july", "juillet")
    .replace("august", "août")
    .replace("september", "septembre")
    .replace("october", "octobre")
    .replace("november", "novembre")
    .replace("december", "décembre")
)
print(f"Current month in French: {current_month}")
# current_month = "mars 2025"  # For testing, you can set a specific month and year
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
    logger.info("Initiating scrape...")
    results = scraper.fetch_results(
        current_month, draw=current_draw, wait_time=wait_time
    )
    logger.info(f"Scraped {len(results)} results for month: {current_month}")
    # Process the results as needed

    # Here, you can store the results or process them further.
    # Optionally, update current_month based on your business logic
    # For example, to move to the previous month, you could create a helper function:
    current_month = get_previous_month(*current_month.split())
    wait_time += 1  # Increment wait time for the next scrape
    # (You may need to implement a month decrement logic based on your data.)


def start_scheduler():
    """Start the background scheduler."""
    logger.info("Starting the scheduler...")
    scheduler = BackgroundScheduler()
    # Schedule job to run at a desired interval (e.g., every day or hour)
    scheduler.add_job(scrape_job, "interval", seconds=120)
    scheduler.start()


if __name__ == "__main__":
    start_scheduler()
    # Block to keep the scheduler running
    logger.info("Scheduler started. Press Ctrl+C to exit.")

    while True:
        try:
            time.sleep(1)  # Keep the main thread alive
        except KeyboardInterrupt:
            logger.info("Scheduler stopped.")
            break
