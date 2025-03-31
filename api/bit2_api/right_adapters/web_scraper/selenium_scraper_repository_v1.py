import json
import logging
from datetime import datetime
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from bit2_api.core.domains.models import GameResult as LotteryResult
from bit2_api.core.domains.utils.env import get_env_variable
from bit2_api.core.ports import IScraperRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ScraperRepository(IScraperRepository):
    """
    SeleniumScraperRepository uses Selenium to load the LNBLoto results page (https://www.lnbloto.bj/resultats),
    extract the JSON data from the <script id="__NEXT_DATA__"> element, and then parse the weekly lottery results.
    """

    def __init__(self):
        # Use the environment variable or fallback default URL
        self.base_url = get_env_variable(
            "BASE_SCRAPING_URL", default="https://www.lnbloto.bj/resultats"
        )
        logger.info("Using base URL: %s", self.base_url)

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")
        options.binary_location = "/usr/bin/chromium"
        # Ensure that the appropriate driver (e.g., chromedriver) is in your PATH.
        self.driver = webdriver.Chrome(options=options)

    def fetch_results(self, week: str) -> List[LotteryResult]:
        """
        Fetch lottery results for a specified week.
        :param week: A string representing the week in the format "startDate - endDate" (e.g., "24/03/2025 - 30/03/2025")
        :return: A list of LotteryResult instances.
        """
        try:
            self.driver.get(self.base_url)
            wait = WebDriverWait(self.driver, 10)
            # Wait until the __NEXT_DATA__ script tag is present
            script_elem = wait.until(
                EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
            )
            json_text = script_elem.get_attribute("textContent")
            data = json.loads(json_text)

            results_data = (
                data.get("props", {}).get("pageProps", {}).get("resultsData", {})
            )
            if not results_data:
                logger.error("No resultsData found in the JSON")
                return []

            weekly_draws = results_data.get("drawsResultsWeekly", [])
            # Loop through weeks until we find the one matching the given week range
            for week_data in weekly_draws:
                start_date = week_data.get("startDate")
                end_date = week_data.get("endDate")
                week_range = f"{start_date} - {end_date}"
                if week_range == week:
                    daily_results = week_data.get("drawResultsDaily", [])
                    results = []
                    for day_data in daily_results:
                        date_str = day_data.get("date")  # e.g., "dimanche 30/03"
                        # Extract numeric date part (assumes format like "dimanche 30/03")
                        parts = date_str.split()
                        date_numeric = parts[1] if len(parts) == 2 else date_str
                        # Assume the year from the week's start date
                        year = datetime.strptime(start_date, "%d/%m/%Y").year
                        try:
                            draw_date = datetime.strptime(
                                f"{date_numeric}/{year}", "%d/%m/%Y"
                            ).date()
                        except Exception as e:
                            logger.error("Error parsing date '%s': %s", date_numeric, e)
                            continue

                        # Extract all draws for the day from both categories.
                        draw_results = day_data.get("drawResults", {})
                        for category in ["standardDraws", "nightDraws"]:
                            for draw in draw_results.get(category, []):
                                draw_name = draw.get("drawName", "")
                                winning_numbers_str = draw.get("winningNumbers", "")
                                try:
                                    numbers = [
                                        int(num.strip())
                                        for num in winning_numbers_str.split("-")
                                        if num.strip().isdigit()
                                    ]
                                except Exception as e:
                                    logger.error("Error parsing numbers: %s", e)
                                    numbers = []
                                # Append a result if valid numbers are found.
                                if numbers:
                                    results.append(
                                        LotteryResult(
                                            draw_date=draw_date,
                                            numbers=numbers,
                                            type=draw_name,
                                            bonus=None,
                                        )
                                    )
                    logger.info("Found %d results for week %s", len(results), week)
                    return results
            logger.error("Specified week '%s' not found", week)
            return []
        except Exception as e:
            logger.error("Error during Selenium scraping: %s", e)
            return []
        finally:
            self.driver.quit()
