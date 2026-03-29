from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config.db import Base, engine
from app.controllers.contacts import contact_router
from app.controllers.users import user_router
from app.controllers.auth import auth_router
from app.errors.handlers import register_error_handlers
from contextlib import asynccontextmanager
from app.schemas.schemas import ValidationErrorResponse
from app.config.settings import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path in {'/swagger', '/openapi.json'}:
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com;"
            )
        else:
            response.headers['Content-Security-Policy'] = "default-src 'none'"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Strict-Transport-Security'] = (
            'max-age=31536000; includeSubDomains'
        )
        return response


limiter = Limiter(key_func=get_remote_address, default_limits=['200/day', '50/hour'])


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        yield


def create_app():
    app = FastAPI(
        title=settings.APP_NAME,
        version='v1',
        docs_url='/swagger',
        lifespan=lifespan,
        responses={422: {'model': ValidationErrorResponse}},
    )
    _register_router(app)

    app.state.limiter = limiter

    origins = ['http://localhost:8080']
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(SlowAPIMiddleware)

    register_error_handlers(app)

    return app


def _register_router(app):
    app.include_router(user_router)  # registrar as blueprints
    app.include_router(contact_router)
    app.include_router(auth_router)
