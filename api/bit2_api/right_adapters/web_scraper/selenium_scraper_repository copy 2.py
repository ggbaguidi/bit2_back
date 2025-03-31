import json
import logging
import time
from datetime import datetime
from typing import List

from bs4 import BeautifulSoup
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
    def __init__(self):
        self.base_url = get_env_variable(
            "BASE_SCRAPING_URL", default="https://www.lnbloto.bj/resultats"
        )
        self.selenium_url = get_env_variable(
            "BASE_SELENIUM_URL", "http://localhost:4444/wd/hub"
        )
        logger.info("Using base URL: %s", self.base_url)

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        # options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")

        # self.driver = webdriver.Chrome(options=options)
        self.driver = webdriver.Remote(
            command_executor=self.selenium_url, options=options
        )

        time.sleep(2)  # Allow time for the driver to initialize

        logger.info("Selenium driver initialized.")

    def fetch_results(
        self, month: str, draw: str, wait_time: int = 1
    ) -> List[LotteryResult]:
        logger.info("Fetching results...")
        try:
            self.driver.get(self.base_url)
            wait = WebDriverWait(self.driver, 10)

            # Select month directly
            month_select = Select(
                wait.until(EC.element_to_be_clickable((By.ID, "month")))
            )
            month_select.select_by_visible_text(month)
            month_select.select_by_value(month)
            logger.info("Selected month: %s", month)

            if draw:
                draw_select = Select(
                    wait.until(EC.element_to_be_clickable((By.ID, "draw")))
                )
                draw_select.select_by_visible_text(draw)
                logger.info("Selected draw type: %s", draw)

            # wait.until(EC.presence_of_element_located((By.ID, "__NEXT_DATA__")))
            # json_text = self._get_fresh_next_data(wait)
            # data = json.loads(json_text)

            # results_data = data.get("props", {}).get("pageProps", {}).get("resultsData", {})
            # if not results_data:
            #     logger.error("No resultsData found in the JSON")
            #     return []

            # Wait for the dynamic container to update (using CSS selector)
            dynamic_container = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#__next > main > div > div > div > div > div")
                )
            )
            # Additional wait to ensure content is fully loaded
            time.sleep(wait_time)

            # Get the updated HTML from the container
            updated_html = dynamic_container.get_attribute("outerHTML")

            # Parse the updated HTML using CSS selectors.
            return parse_results_from_container(updated_html)

        except Exception as e:
            logger.error("Error during Selenium scraping: %s", e)
            return []

    def _get_fresh_next_data(self, wait: WebDriverWait, max_retries: int = 3) -> str:
        retries = 0
        while retries < max_retries:
            try:
                script_elem = wait.until(
                    EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
                )
                return script_elem.get_attribute("textContent")
            except StaleElementReferenceException:
                logger.warning("Stale element reference encountered; retrying...")
            retries += 1
            self.driver.implicitly_wait(1)
        raise TimeoutException(
            "Unable to retrieve fresh __NEXT_DATA__ element after multiple retries."
        )

    def _parse_results(self, results_data: dict) -> List[LotteryResult]:
        results = []
        for week_data in results_data.get("drawsResultsWeekly", []):
            start_date = week_data.get("startDate")
            year = datetime.strptime(start_date, "%d/%m/%Y").year
            for day_data in week_data.get("drawResultsDaily", []):
                try:
                    date_numeric = day_data.get("date").split()[1]
                    draw_date = datetime.strptime(
                        f"{date_numeric}/{year}", "%d/%m/%Y"
                    ).date()
                except Exception as e:
                    logger.error("Error parsing date: %s", e)
                    continue
                for category in ["standardDraws", "nightDraws"]:
                    for draw_item in day_data.get("drawResults", {}).get(category, []):
                        numbers = [
                            int(num.strip())
                            for num in draw_item.get("winningNumbers", "").split("-")
                            if num.strip().isdigit()
                        ]
                        if numbers:
                            results.append(
                                LotteryResult(
                                    draw_date=draw_date,
                                    numbers=numbers,
                                    type=draw_item.get("drawName"),
                                    bonus=None,
                                )
                            )
        logger.info("Found %d results", len(results))
        return results

    def close(self):
        self.driver.quit()


def parse_results_from_container(html: str) -> List[LotteryResult]:
    results = []
    soup = BeautifulSoup(html, "html.parser")

    # # Locate the main container using a CSS selector or other means:
    # main_container = soup.select_one("#__next > main > div > div > div")
    # if not main_container:
    #     logger.error("Main container not found.")
    #     return results

    print(soup.prettify())

    # The first div likely contains the title and select inputs.
    # The subsequent divs each represent a week.
    week_divs = main_container.find_all("div", recursive=False)[1:]
    for week_div in week_divs:
        # Find the week header, usually an h4, e.g., "Semaine du 28/10/2024 au 03/11/2024"
        week_header = week_div.find("h4")
        if not week_header:
            continue
        week_text = week_header.get_text().strip()
        # Optionally, extract start and end dates from the header if needed.
        try:
            # Example: "Semaine du 28/10/2024 au 03/11/2024"
            parts = week_text.split("du")[-1].split("au")
            start_date_str = parts[0].strip()
            # Use the start date's year (or both dates if available)
            year = datetime.strptime(start_date_str, "%d/%m/%Y").year
        except Exception as e:
            logger.error("Error parsing week header dates: %s", e)
            continue

        # The rest of the week_div should have a block for each day.
        # Each day block might have an h5 for the day (e.g., "Jeudi 31/10")
        day_blocks = week_div.find_all("div", recursive=False)
        for day_block in day_blocks:
            day_header = day_block.find("h5")
            if not day_header:
                continue
            day_text = day_header.get_text().strip()  # e.g., "Jeudi 31/10"
            try:
                # Extract the numeric date part, e.g., "31/10"
                day_parts = day_text.split()
                date_numeric = day_parts[-1]
                draw_date = datetime.strptime(
                    f"{date_numeric}/{year}", "%d/%m/%Y"
                ).date()
            except Exception as e:
                logger.error("Error parsing day header: %s", e)
                continue

            # The remaining content in the day block should be the draw cards.
            # Assuming each draw is contained in a div with a specific class (e.g., "rounded-md").
            draw_cards = day_block.find_all(
                "div", class_=lambda x: x and "rounded-md" in x
            )
            for card in draw_cards:
                try:
                    # Get draw name from an element, e.g., a div with font-bold class.
                    draw_name_elem = card.find(
                        "div", class_=lambda x: x and "font-bold" in x
                    )
                    draw_name = (
                        draw_name_elem.get_text().strip() if draw_name_elem else ""
                    )

                    # Extract winning numbers.
                    # For example, numbers might be in <p> elements within the card.
                    number_elements = card.find_all("p")
                    numbers = []
                    for num_elem in number_elements:
                        num_text = num_elem.get_text().strip()
                        # Check if it is numeric.
                        if num_text.isdigit():
                            numbers.append(int(num_text))
                    if numbers:
                        results.append(
                            LotteryResult(
                                draw_date=draw_date,
                                numbers=numbers,
                                type=draw_name,
                                bonus=None,
                            )
                        )
                except Exception as e:
                    logger.error("Error parsing draw card: %s", e)
                    continue
    logger.info("Parsed %d lottery results.", len(results))
    return results
