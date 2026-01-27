"""
I18n middleware for FastAPI.
"""
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.i18n.config import I18nConfig
from app.i18n.core.locale import LocaleContext, get_locale_for_language
from app.i18n.core.context import (
    set_locale,
    reset_locale,
    LocaleDetector
)

logger = logging.getLogger(__name__)


class I18nMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic locale detection and context setup.

    Detection priority:
    1. User preference (from JWT/session)
    2. Tenant default
    3. Accept-Language header
    4. Cookie
    5. Query parameter
    6. GeoIP
    7. System default
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        if self._should_skip(request.url.path):
            return await call_next(request)

        try:
            locale = await self._detect_locale(request)
            set_locale(locale)
            request.state.locale = locale

            response = await call_next(request)

            response.headers["Content-Language"] = locale.language
            response.headers["X-Locale"] = locale.locale_code

            return response

        except Exception as e:
            logger.error(f"I18n middleware error: {e}")
            return await call_next(request)

        finally:
            reset_locale()

    def _should_skip(self, path: str) -> bool:
        """Check if path should skip locale detection."""
        skip_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/favicon.ico"
        ]
        return any(path.startswith(p) for p in skip_paths)

    async def _detect_locale(self, request: Request) -> LocaleContext:
        """Detect locale from request."""

        user_id = getattr(request.state, "user_id", None)
        if user_id:
            locale = await LocaleDetector.detect_from_user(user_id)
            if locale:
                logger.debug(f"Locale detected from user: {locale.language}")
                return locale

        tenant_id = getattr(request.state, "tenant_id", None)
        if tenant_id:
            locale = await LocaleDetector.detect_from_tenant(tenant_id)
            if locale:
                logger.debug(f"Locale detected from tenant: {locale.language}")
                return locale

        accept_language = request.headers.get("Accept-Language", "")
        if accept_language:
            locale = LocaleDetector.detect_from_header(accept_language)
            if locale:
                logger.debug(f"Locale detected from header: {locale.language}")
                return locale

        locale = LocaleDetector.detect_from_cookie(dict(request.cookies))
        if locale:
            logger.debug(f"Locale detected from cookie: {locale.language}")
            return locale

        locale = LocaleDetector.detect_from_query(dict(request.query_params))
        if locale:
            logger.debug(f"Locale detected from query: {locale.language}")
            return locale

        client_ip = request.client.host if request.client else None
        if client_ip:
            locale = await LocaleDetector.detect_from_geoip(client_ip)
            if locale:
                logger.debug(f"Locale detected from GeoIP: {locale.language}")
                return locale

        logger.debug("Using default locale")
        return get_locale_for_language(I18nConfig.DEFAULT_LANGUAGE)


def get_request_locale(request: Request) -> LocaleContext:
    """
    Get locale from request state.

    Usage in route handlers:
        @app.get("/items")
        async def get_items(request: Request):
            locale = get_request_locale(request)
            ...
    """
    return getattr(request.state, "locale", LocaleContext())
