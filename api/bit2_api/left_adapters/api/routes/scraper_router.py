from http import HTTPStatus

import inject
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi_versioning import version

from bit2_api.core.domains.commands import ExtractGameResultCommand
from bit2_api.core.domains.errors import InvalidGameResultError
from bit2_api.core.use_cases import ExtractGameResult
from bit2_api.right_adapters.web_scraper import ScraperRepository

router = APIRouter()


@router.get(
    "/scrape",
    status_code=HTTPStatus.CREATED,
    # response_model=DocumentViewModel,
    tags=["Game Results"],
    summary="Scrape lottery results",
)
@version(1)
def scrape_results(
    month: str,
    year: str,
    scraper: ScraperRepository = Depends(ScraperRepository),
):
    """
    Scrape lottery results from an external source and store them in the database."""
    uc_ = inject.instance(ExtractGameResult)

    # Fetch results using the scraper
    # current_day_scraper_results = scraper.fetch_current_results(month="", draw="")
    scraped_results = scraper.fetch_results(month=f"{month} {year}", draw="")

    if not scraped_results:
        raise InvalidGameResultError

    # sort the results by draw_date
    # current_day_scraper_results.sort(key=lambda x: x.draw_date)
    scraped_results.sort(key=lambda x: x.draw_date)

    for result in scraped_results:
        # Assuming result contains draw_date, numbers, bonus, and type
        command = ExtractGameResultCommand(
            draw_date=result.draw_date,
            numbers=result.numbers,
            bonus=result.bonus,
            type=result.type,
        )
        uc_.execute(command)

    # Convert results to JSON-serializable format
    serialized_results = [result.to_dict() for result in scraped_results]

    # Process results as needed
    # For example, you can return the results as a JSON response
    return JSONResponse(
        content={
            "message": "Scraping completed successfully.",
            "results": serialized_results,
        },
        status_code=HTTPStatus.OK,
    )
