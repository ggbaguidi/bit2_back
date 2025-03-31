import logging
import os
import pickle
import time
from datetime import datetime
from typing import List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
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
    def __init__(self):
        self.base_url = get_env_variable(
            "BASE_SCRAPING_URL", "https://www.lnbloto.bj/resultats"
        )
        self.selenium_url = get_env_variable(
            "BASE_SELENIUM_URL", "http://localhost:4444/wd/hub"
        )
        logger.info("Using base URL: %s", self.base_url)

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--remote-debugging-port=9222")

        self.driver = webdriver.Remote(
            command_executor=self.selenium_url, options=options
        )
        # self.driver = webdriver.Chrome(options=options)
        logger.info("Selenium driver initialized.")

    def fetch_results(
        self, month: str, draw: str, wait_time: int = 1
    ) -> List[GameResult]:
        logger.info("Fetching results for month: %s, draw: %s", month, draw)
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
            month_select.select_by_visible_text(month)

            print("Month selected.")

            if draw:
                draw_select = Select(
                    wait.until(EC.element_to_be_clickable((By.ID, "draw")))
                )
                draw_select.select_by_visible_text(draw)
                logger.info("Selected draw type: %s", draw)

            # Wait for new container to load
            dynamic_container = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#__next > main > div > div > div > div > div")
                )
            )

            # Wait for the page to load
            time.sleep(10)

            updated_html = dynamic_container.get_attribute("innerHTML")

            # Wait for the page to load completely
            time.sleep(10)

            print("Waiting for the page to load completely...")
            # Scroll to the bottom of the page to ensure all elements are loaded
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(5)

            results = parse_results_from_container(updated_html)

            path_file = f"./data/{month}/{datetime.now().isoformat()}.pkl"

            save_to_path(path_file, results)

            logger.info("Results fetched and saved successfully.")
            return results

        except (
            TimeoutException,
            NoSuchElementException,
            StaleElementReferenceException,
        ) as e:
            logger.error("Error during Selenium scraping: %s", e.msg)
            return []
        finally:
            self.driver.quit()

    def close(self):
        self.driver.quit()


def parse_results_from_container(html: str) -> List[GameResult]:
    results = []
    soup = BeautifulSoup(html, "html.parser")

    # Locate the main container; adjust this selector based on your actual HTML.
    main_container = soup
    if not main_container:
        logger.error("Main container not found.")
        return results

    # Assuming the first child is not a week container, skip it.
    week_divs = main_container.find_all("div", recursive=False)[1:]

    for week_div in week_divs:
        week_header = week_div.find("h4")
        if not week_header:
            logger.debug("Week division skipped: no week header found.")
            continue

        week_text = week_header.get_text().strip()
        try:
            # Example: "Some text du 01/01/2025 au ..." – extract the start date.
            parts = week_text.split("du")[-1].split("au")
            start_date_str = parts[0].strip()
            year = datetime.strptime(start_date_str, "%d/%m/%Y").year
        except Exception as e:
            logger.error("Error parsing week header dates ('%s'): %s", week_text, e)
            continue

        # Process each day block within the current week division.
        day_blocks = week_div.find_all("div", recursive=False)
        for day_block in day_blocks:
            day_header = day_block.find("h5")
            if not day_header:
                logger.debug("Day block skipped: no day header found.")
                continue

            day_text = day_header.get_text().strip()
            try:
                # Assuming the day header is something like "Mercredi 01/01"
                day_parts = day_text.split()
                date_numeric = day_parts[-1]
                draw_date = datetime.strptime(
                    f"{date_numeric}/{year}", "%d/%m/%Y"
                ).date()
            except Exception as e:
                logger.error("Error parsing day header ('%s'): %s", day_text, e)
                continue

            # Locate all draw cards within the day block.
            draw_cards = day_block.find_all(
                "div", class_=lambda x: x and "rounded-md" in x
            )
            for card in draw_cards:
                try:
                    # Extract the draw name (e.g., "Digital 00H")
                    draw_name_elem = card.find(
                        "div", class_=lambda x: x and "font-bold" in x
                    )
                    draw_name = (
                        draw_name_elem.get_text().strip() if draw_name_elem else ""
                    )

                    # Extract lottery numbers from all <p> elements that contain digits.
                    number_elements = card.find_all("p")
                    numbers = [
                        int(num.get_text().strip())
                        for num in number_elements
                        if num.get_text().strip().isdigit()
                    ]

                    draw_name = draw_name.upper().replace(" ", "_")

                    if numbers:
                        results.append(
                            GameResult(
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

    # print("Parsed %d lottery results.", len(results))
    # print("Parsed results:", results)

    return results


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


def save_to_path(path: str, results: List[GameResult]):
    """Save results to a file using pickle."""

    # Ensure the directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Save the results to the specified path
    with open(path, "wb") as f:
        results = [result.to_dict() for result in results]
        pickle.dump(results, f)
    ##############
    # Example usage
    # scraper = ScraperRepository()
    # results = scraper.fetch_results("mars 2025", draw="Fortune")
    # path = "results.pkl"
    # save_to_path(path, results)
    logger.info("Results saved to %s", path)
