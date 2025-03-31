import logging
from datetime import datetime
from typing import List

import httpx
from bs4 import BeautifulSoup

from bit2_api.core.domains.models import GameResult
from bit2_api.core.domains.utils.env import get_env_variable
from bit2_api.core.ports import IScraperRepository

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ScraperRepository(IScraperRepository):
    """
    ScraperRepository is a concrete implementation of the IScraperRepository interface.
    It is responsible for fetching and parsing game results from a web source.
    """

    def __init__(self):
        self.base_url = get_env_variable(
            "BASE_SCRAPING_URL", default="https://www.lnbloto.bj/resultats"
        )

    def fetch_results(
        self, month: str, draw: str, wait_time: int = 1
    ) -> List[GameResult]:
        try:
            html = self._fetch_page()
        except Exception as e:
            logger.error("Failed to fetch page: %s", e)
            return []

        if not html:
            logger.error("Empty HTML content received")
            return []

        logger.info("Fetched HTML content successfully")
        results = self._parse_results(html)
        logger.info("Parsed %d results", len(results))
        return results

    def _fetch_page(self) -> str:
        response = httpx.get(self.base_url, timeout=10)
        response.raise_for_status()
        return response.text

    def _parse_results(self, html: str) -> List[GameResult]:
        """
        Parses the HTML content to extract lottery results.
        This method uses BeautifulSoup to navigate the HTML structure
        and extract relevant data such as draw dates and winning numbers.
        """
        return parse_results_from_container(html)


def parse_results_from_container(html: str) -> List[GameResult]:
    results = []
    soup = BeautifulSoup(html, "html.parser")

    # Locate the main container using a CSS selector or other means:
    main_container = soup.select_one("#__next > main > div > div > div > div")
    if not main_container:
        logger.error("Main container not found.")
        return results

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
    return results
