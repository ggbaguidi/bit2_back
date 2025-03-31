"""
Application entry point
"""

import logging
import time
from fnmatch import fnmatch

from fastapi import Request, Response
from starlette.concurrency import iterate_in_threadpool
from starlette.requests import Message

from bit2_api.utils_main.configure_injections import configure_injections
from bit2_api.utils_main.create_app import create_app

logger = logging.getLogger(__name__)

configure_injections()
app = create_app()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests and associated response

    Request bodies and response contents are streams.
    Accessing them consumes them and make them unavailable for the next call,
    so they need to be re-injected in the request or response after reading them.
    """

    # Helper functions to get the request body and re-insert it into the request
    async def set_body(request: Request, body: bytes):
        async def receive() -> Message:
            return {"type": "http.request", "body": body}

        request._receive = receive  # pylint: disable=protected-access

    async def get_body(request: Request) -> bytes:
        body = await request.body()
        await set_body(request, body)
        return body

    def crop(log):
        if len(log) > 100:
            return log[:100] + "[...]"
        return log

    do_not_log_request = ["/"]
    if any(fnmatch(request.url.path, p) for p in do_not_log_request):
        return await call_next(request)

    do_not_log_payload = ["/*/login"]
    if any(fnmatch(request.url.path, p) for p in do_not_log_payload):
        request_body = "REDACTED"
    else:
        request_body = await get_body(request)

    log_payload = {
        "request.body": request_body if len(request_body) > 0 else None,
        "request.path": request.url.path,
        "request.method": request.method,
    }
    start_time = time.time()
    response: Response = await call_next(request)
    process_time_in_ms = int((time.time() - start_time) * 1000)

    # read response content and re-inject it into the response
    response_content = [chunk async for chunk in response.body_iterator]
    response.body_iterator = iterate_in_threadpool(iter(response_content))
    response_as_str = (b"".join(response_content)).decode("utf-8")

    # Get canonical route name, or None if no route matches the path.
    # https://stackoverflow.com/questions/72217828/fastapi-how-to-get-raw-url-path-from-request
    route_path = (
        request.scope["root_path"] + request.scope["route"].path
        if "route" in request.scope
        else None
    )

    log_payload.update(
        {
            "response.status_code": response.status_code,
            "response.body": crop(response_as_str),
            "request.duration": process_time_in_ms,
            "request.route_path": route_path,
        }
    )
    log_message = f"{request.method} {request.url.path} {response.status_code}"
    logger.info(log_message, extra=log_payload)

    return response
