import logging
import re
from datetime import datetime, timedelta
from typing import List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from bit2_api.core.domains.models import GameResult
from bit2_api.core.domains.utils.enums import GameTypeEnum
from bit2_api.core.domains.utils.env import get_env_variable
from bit2_api.core.ports import IScraperRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ScraperRepository(IScraperRepository):
    """
    ScraperRepository is a class that implements the IScraperRepository interface.
    It uses Selenium to scrape lottery results from a specified URL.
    """

    def __init__(self):
        self.archive_scraping_url = get_env_variable(
            "BASE_SCRAPING_URL",
            default="https://sites.google.com/view/lotobonheur/archive-benin",
        )

        self.current_scraping_url = get_env_variable(
            "BASE_SCRAPING_URL",
            default="https://sites.google.com/view/lotobonheur/loto-benin?authuser=0",
        )
        self.selenium_url = get_env_variable(
            "BASE_SELENIUM_URL", "http://localhost:4444/wd/hub"
        )
        logger.info("Using base URL: %s", self.archive_scraping_url)

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        # options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")

        self.options = options

        # self.driver = webdriver.Chrome(options=options)
        self.driver = webdriver.Remote(
            command_executor=self.selenium_url, options=options
        )

        logger.info("Selenium driver initialized")

    def fetch_current_results(
        self, month: str, draw: str = "", wait_time: int = 1
    ) -> List[GameResult]:
        logger.info("Fetching current results...")
        _ = month
        _ = draw
        _ = wait_time
        try:
            self.driver.get(self.current_scraping_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "p"))
            )

            # Extract page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            paragraphs = [
                [span.get_text(strip=True) for span in p.find_all("span")]
                for p in soup.find_all("p")
            ]

            logger.info("Page source extracted and parsed")

            # print(paragraphs)
            # Extract the relevant data from the paragraphs
            results = parse_results(paragraphs)

            self.driver.close()  # Close the browser
            # print(paragraphs[:10])
            print(results)

            return results
        except Exception as e:
            logger.error("An error occurred: %s", e)
            self.driver.quit()  # Close the browser
            return []
        return []

    def fetch_results(
        self, month: str, draw: str = "", wait_time: int = 1
    ) -> List[GameResult]:

        _ = month
        _ = draw
        _ = wait_time

        logger.info("Fetching results...")
        try:
            self.driver.get(self.archive_scraping_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "p"))
            )

            # Extract page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            paragraphs = [
                [span.get_text(strip=True) for span in p.find_all("span")]
                for p in soup.find_all("p")
            ]

            logger.info("Page source extracted and parsed")

            # print(paragraphs)
            # Extract the relevant data from the paragraphs
            results = parse_results(paragraphs)

            # print(paragraphs[:10])
            print(results[:10])

            self.driver.quit()  # Close the browser

            return results

        except Exception as e:
            logger.error("An error occurred: %s", e)
            self.driver.quit()  # Close the browser
            return []
        return []


def decrement_date(date: datetime) -> datetime:
    """
    Decrement the given date by one day.
    """
    return date - timedelta(days=1)


def parse_results(paragraphs: List[str]) -> List[GameResult]:
    results = []
    current_date = datetime.now()  # Start with the current date

    logger.info("Parsing results...")

    for paragraph in paragraphs:
        # Check if this is a date marker (starts and ends with 'ii')
        if len(paragraph) >= 2 and paragraph[0] == "ii" and paragraph[-1] == "ii":
            paragraph = " ".join([p for p in paragraph[1:-1] if p.strip()])
            paragraph = paragraph.split(" ")
            try:
                # Extract date components
                day_part = paragraph[1].strip()  # "Dimanche 30"
                month_part = paragraph[2].strip()  # "mars 2025"

                # Extract day number
                day_match = re.search(r"\d+", day_part)
                if day_match:
                    day = int(day_match.group())
                else:
                    print("Day not found in date string: %s", paragraph)
                    continue

                # Extract month and year
                year_parts = paragraph[-1].strip()
                month_str = month_part[0].lower()

                year_match = re.search(r"\d{4}", year_parts)
                if year_match:
                    year = int(year_match.group())
                else:
                    print("Year not found in date string")
                    continue

                # Convert month name to number (French months)
                month_map = {
                    "janvier": 1,
                    "février": 2,
                    "mars": 3,
                    "avril": 4,
                    "mai": 5,
                    "juin": 6,
                    "juillet": 7,
                    "août": 8,
                    "septembre": 9,
                    "octobre": 10,
                    "novembre": 11,
                    "décembre": 12,
                }
                month = month_map.get(month_str, None)

                current_date = decrement_date(current_date)
            except Exception as e:
                logger.error(f"Error parsing date: {e}")
                continue

        # Check if this is a game result
        elif current_date and len(paragraph) > 3 and paragraph[0] == "j":
            try:
                game_info = paragraph[1]  # e.g., "DIGITAL 1 Tirage 00H"

                # Extract game type
                if "DIGITAL 1" in game_info:
                    game_type = GameTypeEnum.DIGITAL_1
                elif "DIGITAL 2" in game_info:
                    game_type = GameTypeEnum.DIGITAL_2
                elif "RESULTAT 1" in game_info:
                    game_type = GameTypeEnum.RESULTAT_1
                elif "RESULTAT 2" in game_info:
                    game_type = GameTypeEnum.RESULTAT_2
                elif "RESULTAT 3" in game_info:
                    game_type = GameTypeEnum.RESULTAT_3
                else:
                    continue

                # Extract time
                time_match = re.search(r"Tirage (\d+)H", game_info)
                if time_match:
                    hour = int(time_match.group(1))
                    draw_datetime = current_date.replace(hour=hour, minute=0, second=0)
                else:
                    draw_datetime = current_date

                # Find the number string in the paragraph
                numbers = []
                for item in paragraph:
                    if "-" in item and any(char.isdigit() for char in item):
                        # Skip patterns like '. - . - . - . - .'
                        if all(part.strip() in [".", ""] for part in item.split("-")):
                            continue

                        # Process patterns like "10 - 60 - 13 - 31 - 87"
                        nums = []
                        for num_str in item.split("-"):
                            num_str = num_str.strip()
                            if num_str.isdigit():
                                nums.append(int(num_str))

                        if nums:
                            numbers.extend(nums)

                if numbers:
                    # Create LotteryResult instance
                    result = GameResult(
                        draw_date=draw_datetime,
                        numbers=numbers,
                        bonus=None,  # No bonus in the example data
                        type=game_type,
                    )
                    results.append(result)
            except Exception as e:
                logger.error(f"Error parsing game result: {e}")

    return results
