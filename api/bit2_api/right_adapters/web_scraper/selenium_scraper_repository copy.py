import json
import logging
from datetime import datetime
from typing import List

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from bit2_api.core.domains.models import GameResult as LotteryResult
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
    ) -> List[LotteryResult]:
        """
        Fetch lottery results for the specified month (e.g., "janvier 2025") and optional draw type.
        :param month: Month filter as a string (e.g., "janvier 2025").
        :param draw: Optional draw filter (e.g., "Fortune", "Star", etc.).
        :return: A list of LotteryResult instances.
        """
        try:
            self.driver.get(self.base_url)
            wait = WebDriverWait(self.driver, 10 * wait_time)
            print("Waiting for the page to load...")
            # Wait and select the desired month with retry logic
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    print(f"Selecting month (attempt {attempt+1}/{max_attempts})...")
                    # Re-locate the element in each attempt to avoid stale references
                    month_select_elem = wait.until(
                        EC.presence_of_element_located((By.ID, "month"))
                    )
                    print("Month select element found.")
                    month_select = Select(month_select_elem)
                    print("Selecting month:", month)
                    wait.until(
                        lambda d: d.execute_script("return document.readyState")
                        == "complete"
                    )
                    available_options = [option.text for option in month_select.options]
                    print("Available options:", available_options)
                    month_select.select_by_visible_text(month)
                    print(f"Selected month: {month}")

                    # Wait for page to update after selection
                    wait = WebDriverWait(self.driver, 10)

                    wait.until(
                        lambda d: d.execute_script("return document.readyState")
                        == "complete"
                    )

                    # Verify the month was actually selected
                    new_month_select_elem = wait.until(
                        EC.presence_of_element_located((By.ID, "month"))
                    )
                    new_month_select = Select(new_month_select_elem)
                    if new_month_select.first_selected_option.text == month:
                        print("Month selected successfully.")
                        logger.info("Selected month: %s", month)
                        break
                except (StaleElementReferenceException, TimeoutException) as e:
                    if attempt == max_attempts - 1:
                        raise
                    logger.warning(
                        f"Selection attempt {attempt+1} failed: {e}. Retrying..."
                    )
                    self.driver.refresh()
                    month_select_elem = wait.until(
                        EC.presence_of_element_located((By.ID, "month"))
                    )

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
                                    LotteryResult(
                                        draw_date=draw_date,
                                        numbers=numbers,
                                        type=draw_name,
                                        bonus=None,
                                    )
                                )
            logger.info("Found %d results for month %s", len(results), month)
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
