from fastapi import Request

from app.middleware.request_context import get_request_id


async def get_request_id_header(request: Request) -> str:
    return request.headers.get("X-Request-ID") or get_request_id()
