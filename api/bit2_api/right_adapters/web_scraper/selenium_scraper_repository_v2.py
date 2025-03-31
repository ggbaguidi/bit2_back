import json
import logging
import time
from datetime import datetime
from typing import List

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from bit2_api.core.domains.models import GameResult
from bit2_api.core.domains.utils.env import get_env_variable
from bit2_api.core.ports import IScraperRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ScraperRepository(IScraperRepository):
    """
    SeleniumScraperRepository uses Selenium to load the LNBLoto results page,
    selects a month (and optionally a draw type), and extracts the JSON data
    from the <script id="__NEXT_DATA__"> element.
    """

    def __init__(self):
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
        self.driver = webdriver.Chrome(options=options)

    def fetch_results(
        self, month: str, draw: str = "", wait_time: int = 1
    ) -> List[GameResult]:
        """
        Fetch lottery results for the specified month (e.g., "janvier 2025") and optional draw type.
        :param month: Month filter as a string (e.g., "janvier 2025").
        :param draw: Optional draw filter (e.g., "Fortune", "Star", etc.).
        :return: A list of LotteryResult instances.
        """
        try:
            self.driver.get(self.base_url)
            wait = WebDriverWait(self.driver, 30)
            # Wait until the page is fully loaded and React has finished processing.
            wait.until(
                lambda d: d.execute_script(
                    'return document.readyState === "complete" && !document.querySelector(".loading-indicator")'
                )
            )
            print("Page loaded and React processed the change.")

            # Use a stable element finder to get the month select element.
            month_select_element = get_stable_element(self.driver, By.ID, "month")
            wait.until(EC.element_to_be_clickable((By.ID, "month")))
            print("Month select element found.")

            month_select = Select(month_select_element)

            print("Selecting month...")
            month_select.select_by_visible_text("janvier 2025")

            print("Month selected.")

            # Optionally select the draw type.
            if draw:
                draw_select_elem = wait.until(
                    EC.presence_of_element_located((By.ID, "draw"))
                )
                draw_select = Select(draw_select_elem)
                draw_select.select_by_visible_text(draw)
                logger.info("Selected draw type: %s", draw)

            # Wait for the page to update after selection.
            wait.until(EC.presence_of_element_located((By.ID, "__next")))
            wait.until(EC.presence_of_element_located((By.ID, "__NEXT_DATA__")))

            # Attempt to retrieve the JSON data with retry logic.
            json_text = self._get_fresh_next_data(wait)
            data = json.loads(json_text)

            results_data = (
                data.get("props", {}).get("pageProps", {}).get("resultsData", {})
            )
            if not results_data:
                logger.error("No resultsData found in the JSON")
                return []

            weekly_draws = results_data.get("drawsResultsWeekly", [])
            results = []
            # Process each week available.
            for week_data in weekly_draws:
                start_date = week_data.get("startDate")
                end_date = week_data.get("endDate")
                daily_results = week_data.get("drawResultsDaily", [])
                for day_data in daily_results:
                    date_str = day_data.get("date")  # e.g., "dimanche 30/03"
                    parts = date_str.split()
                    date_numeric = parts[1] if len(parts) == 2 else date_str
                    year = datetime.strptime(start_date, "%d/%m/%Y").year
                    try:
                        draw_date = datetime.strptime(
                            f"{date_numeric}/{year}", "%d/%m/%Y"
                        ).date()
                    except Exception as e:
                        logger.error("Error parsing date '%s': %s", date_numeric, e)
                        continue

                    draw_results = day_data.get("drawResults", {})
                    for category in ["standardDraws", "nightDraws"]:
                        for draw_item in draw_results.get(category, []):
                            draw_name = draw_item.get("drawName", "")
                            winning_numbers_str = draw_item.get("winningNumbers", "")
                            try:
                                numbers = [
                                    int(num.strip())
                                    for num in winning_numbers_str.split("-")
                                    if num.strip().isdigit()
                                ]
                            except Exception as e:
                                logger.error("Error parsing numbers: %s", e)
                                numbers = []
                            if numbers:
                                results.append(
                                    GameResult(
                                        draw_date=draw_date,
                                        numbers=numbers,
                                        type=draw_name,
                                        bonus=None,
                                    )
                                )
            logger.info("Found %d results for month %s", len(results), month)

            print("Results fetched successfully.")
            print("Results:", results)
            return results

        except Exception as e:
            logger.error("Error during Selenium scraping: %s", e)
            return []
        finally:
            self.driver.quit()

    def _get_fresh_next_data(self, wait: WebDriverWait, max_retries: int = 3) -> str:
        """
        Attempt to retrieve the __NEXT_DATA__ element text, retrying if a stale element is encountered.
        """
        retries = 0
        while retries < max_retries:
            try:
                script_elem = wait.until(
                    EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
                )
                text = script_elem.get_attribute("textContent")
                if text:
                    return text
            except StaleElementReferenceException:
                logger.warning("Stale element reference encountered; retrying...")
            retries += 1
            # Wait a moment before retrying.
            wait._driver.implicitly_wait(1)
        raise Exception(
            "Unable to retrieve fresh __NEXT_DATA__ element after multiple retries."
        )


def get_stable_element(driver, by, locator, retries=5, delay=1):
    """Locate an element and retry if a StaleElementReferenceException is encountered."""
    for i in range(retries):
        try:
            element = driver.find_element(by, locator)
            # Try to access a property to ensure it is still attached to the DOM.
            _ = element.tag_name
            return element
        except StaleElementReferenceException:
            time.sleep(delay)
    raise Exception(
        f"Element with locator {locator} remains stale after {retries} retries."
    )
