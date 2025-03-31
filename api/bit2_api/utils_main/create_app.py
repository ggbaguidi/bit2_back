# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

from fastapi import FastAPI
from fastapi_versioning import VersionedFastAPI

from bit2_api.left_adapters.api.routes import scraper_router


def create_app() -> VersionedFastAPI:
    """
    Instantiate the app and its api
    """
    fast_api_app = FastAPI()

    fast_api_app.include_router(
        scraper_router.router,
        prefix="/api",
        tags=["Game Results"],
    )

    fast_api_versioned_app = VersionedFastAPI(
        fast_api_app,
        enable_latest=True,
        version_format="{major}",
        prefix_format="/v{major}",
    )

    return fast_api_versioned_app
