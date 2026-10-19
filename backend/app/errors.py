import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.logging_setup import request_id_var

logger = logging.getLogger("scamradar.errors")


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


HTTP_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    413: "payload_too_large",
    415: "unsupported_media_type",
    422: "validation_error",
    429: "rate_limited",
}


def error_response(request: Request, status_code: int, code: str, message: str, headers=None) -> JSONResponse:
    request_id = request_id_var.get()
    body = {"error": {"code": code, "message": message, "request_id": request_id}}
    return JSONResponse(status_code=status_code, content=body, headers=headers)


async def handle_app_error(request: Request, exc: AppError):
    return error_response(request, exc.status_code, exc.code, exc.message)


async def handle_http_error(request: Request, exc: StarletteHTTPException):
    code = HTTP_CODES.get(exc.status_code, "http_error")
    message = code
    if exc.detail:
        message = str(exc.detail)
    return error_response(request, exc.status_code, code, message, exc.headers)


async def handle_validation_error(request: Request, exc: RequestValidationError):
    parts = []
    for item in exc.errors():
        names = []
        for piece in item.get("loc", []):
            if piece != "body":
                names.append(str(piece))
        location = ".".join(names)
        parts.append(location + ": " + str(item.get("msg", "invalid")))
    message = "Invalid request"
    if parts:
        message = "; ".join(parts)
    return error_response(request, 422, "validation_error", message[:500])


async def handle_unexpected_error(request: Request, exc: Exception):
    logger.exception("unhandled error", extra={"path": request.url.path})
    return error_response(request, 500, "internal_error", "Something went wrong on the server")


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
