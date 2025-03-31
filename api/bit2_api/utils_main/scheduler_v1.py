import json
import logging
import time
from datetime import datetime, timedelta
from typing import List

from apscheduler.schedulers.background import BackgroundScheduler

from bit2_api.core.domains.models import GameResult as LotteryResult
from bit2_api.right_adapters.web_scraper import ScraperRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global state to keep track of the current week range.
# Initially set to the most recent week you want to scrape.
current_week = {"start": "08/05/2023", "end": "14/05/2023"}

# Optionally store last fetched results to avoid re-processing if nothing new appears.
last_fetched_results: List[LotteryResult] = []


def format_date(date_obj: datetime.date) -> str:
    return date_obj.strftime("%d/%m/%Y")


def get_previous_week(start_str: str, end_str: str):
    """
    Given the start and end of a week in DD/MM/YYYY format,
    return the start and end dates of the previous week.
    """
    start_date = datetime.strptime(start_str, "%d/%m/%Y").date()
    end_date = datetime.strptime(end_str, "%d/%m/%Y").date()
    previous_start = start_date - timedelta(days=7)
    previous_end = end_date - timedelta(days=7)
    return format_date(previous_start), format_date(previous_end)


def scrape_job():
    """Job to scrape game results for the current week, then update week if new results exist."""
    global current_week, last_fetched_results
    week_range = f"{current_week['start']} - {current_week['end']}"
    logger.info("Scraping results for week: %s", week_range)

    scraper = ScraperRepository()
    results = scraper.fetch_results(week_range)

    if results:
        # Check if the new results differ from the previous results.
        if results != last_fetched_results:
            logger.info(
                "New results found for week %s: %d draws", week_range, len(results)
            )
            last_fetched_results = results
            # Here you can store results in your database or process them further.
            print(f"Scraped {len(results)} results for week {week_range}.")
            print(results)
            # Advance the week state (move one week back)
            current_week["start"], current_week["end"] = get_previous_week(
                current_week["start"], current_week["end"]
            )
            logger.info(
                "Next week set to: %s - %s", current_week["start"], current_week["end"]
            )
        else:
            logger.info("No new results for week %s.", week_range)
    else:
        logger.info("No results found for week %s. Retrying later.", week_range)


def start_scheduler():
    """Start the background scheduler."""
    scheduler = BackgroundScheduler()
    # For testing, run every 1 minute (adjust interval as needed for production)
    scheduler.add_job(scrape_job, "interval", seconds=10)
    scheduler.start()
