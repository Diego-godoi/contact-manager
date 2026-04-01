from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.errors.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidCredentialsError,
    NotFoundError,
)


def register_error_handlers(app: FastAPI):

    @app.exception_handler(RateLimitExceeded)
    async def handle_rate_limit(request: Request, exc: RateLimitExceeded):
        return _rate_limit_exceeded_handler(request, exc)

    @app.exception_handler(NotFoundError)
    async def handle_not_found(request: Request, exc: NotFoundError):
        return JSONResponse(status_code=exc.status_code, content={'error': exc.detail})

    @app.exception_handler(ConflictError)
    async def handle_conflict(request: Request, exc: ConflictError):
        return JSONResponse(status_code=exc.status_code, content={'error': exc.detail})

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError):
        formatted_errors = []

        for error in exc.errors():
            field = str(error['loc'][-1])
            error_type = error['type']
            ctx = error.get('ctx', {})

            if error_type == 'string_too_short':
                min_len = ctx.get('min_length', 1)
                message = (
                    f"The field '{field}' must be at least {min_len} characters long"
                    if min_len > 1
                    else f"The field '{field}' cannot be empty"
                )

            elif field == 'email' and (
                error_type == 'value_error' or 'email' in error_type
            ):
                message = 'Invalid email format'

            elif error_type == 'string_pattern_mismatch':
                message = f"The field '{field}' contains invalid characters"

            else:
                message = error['msg'].capitalize()

            formatted_errors.append({field: message})

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={'error': formatted_errors},
        )

    @app.exception_handler(InvalidCredentialsError)
    async def handle_invalid_credentials(
        request: Request, exc: InvalidCredentialsError
    ):
        return JSONResponse(status_code=exc.status_code, content={'error': exc.detail})

    @app.exception_handler(ForbiddenError)
    async def handle_forbidden(request: Request, exc: ForbiddenError):
        return JSONResponse(status_code=exc.status_code, content={'error': exc.detail})

    @app.exception_handler(Exception)
    async def handle_exception(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={'error': 'Internal Error Server'})
