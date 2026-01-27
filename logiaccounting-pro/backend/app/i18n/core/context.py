"""
Request context management for i18n.
"""
import logging
from typing import Optional
from contextvars import ContextVar

from app.i18n.core.locale import LocaleContext

logger = logging.getLogger(__name__)

_locale_context: ContextVar[Optional[LocaleContext]] = ContextVar(
    'locale_context',
    default=None
)


def get_locale() -> LocaleContext:
    """
    Get current locale context.

    Returns default locale if none is set.
    """
    locale = _locale_context.get()
    if locale is None:
        return LocaleContext()
    return locale


def set_locale(locale: LocaleContext) -> None:
    """Set current locale context."""
    _locale_context.set(locale)


def reset_locale() -> None:
    """Reset locale context to default."""
    _locale_context.set(None)


class LocaleContextManager:
    """
    Context manager for temporary locale switching.

    Usage:
        with LocaleContextManager(spanish_locale):
            # Code here uses Spanish locale
            translated = t('hello')
    """

    def __init__(self, locale: LocaleContext):
        self.locale = locale
        self.previous_locale: Optional[LocaleContext] = None

    def __enter__(self) -> LocaleContext:
        self.previous_locale = _locale_context.get()
        set_locale(self.locale)
        return self.locale

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.previous_locale:
            set_locale(self.previous_locale)
        else:
            reset_locale()
        return False


class LocaleDetector:
    """
    Detect locale from various sources.
    """

    @staticmethod
    async def detect_from_user(user_id: str) -> Optional[LocaleContext]:
        """Detect locale from user preferences."""
        from app.i18n.core.locale import LocaleContext

        try:
            from app.models import users
            user = users.get(user_id)
            if user and hasattr(user, 'preferences'):
                prefs = user.preferences or {}
                if prefs.get('language'):
                    locale = LocaleContext(
                        language=prefs.get('language', 'en'),
                        currency=prefs.get('currency', 'USD'),
                        timezone=prefs.get('timezone', 'UTC'),
                        date_format=prefs.get('date_format', 'YYYY-MM-DD'),
                        time_format=prefs.get('time_format', '24h'),
                        detection_source="user_preference"
                    )
                    return locale
        except Exception as e:
            logger.error(f"Error detecting locale from user: {e}")

        return None

    @staticmethod
    async def detect_from_tenant(tenant_id: str) -> Optional[LocaleContext]:
        """Detect locale from tenant settings."""
        from app.i18n.core.locale import LocaleContext

        try:
            from app.models import tenants
            tenant = tenants.get(tenant_id)
            if tenant and hasattr(tenant, 'settings'):
                settings = tenant.settings or {}
                if settings.get('default_language'):
                    locale = LocaleContext(
                        language=settings.get('default_language', 'en'),
                        currency=settings.get('default_currency', 'USD'),
                        timezone=settings.get('default_timezone', 'UTC'),
                        detection_source="tenant_default"
                    )
                    return locale
        except Exception as e:
            logger.error(f"Error detecting locale from tenant: {e}")

        return None

    @staticmethod
    def detect_from_header(accept_language: str) -> Optional[LocaleContext]:
        """
        Detect locale from Accept-Language header.

        Example header: "es-ES,es;q=0.9,en;q=0.8"
        """
        from app.i18n.config import I18nConfig
        from app.i18n.core.locale import get_locale_for_language

        if not accept_language:
            return None

        languages = []
        for part in accept_language.split(","):
            part = part.strip()
            if ";q=" in part:
                lang, quality = part.split(";q=")
                languages.append((lang.strip(), float(quality)))
            else:
                languages.append((part, 1.0))

        languages.sort(key=lambda x: x[1], reverse=True)

        for lang_code, _ in languages:
            if "-" in lang_code:
                base_lang = lang_code.split("-")[0]
            else:
                base_lang = lang_code

            if I18nConfig.is_language_supported(base_lang):
                locale = get_locale_for_language(base_lang)
                locale.detection_source = "header"
                return locale

        return None

    @staticmethod
    def detect_from_cookie(cookies: dict) -> Optional[LocaleContext]:
        """Detect locale from cookie."""
        from app.i18n.core.locale import get_locale_for_language
        from app.i18n.config import I18nConfig

        lang = cookies.get("locale") or cookies.get("lang")
        if lang and I18nConfig.is_language_supported(lang):
            locale = get_locale_for_language(lang)
            locale.detection_source = "cookie"
            return locale

        return None

    @staticmethod
    def detect_from_query(query_params: dict) -> Optional[LocaleContext]:
        """Detect locale from query parameter."""
        from app.i18n.core.locale import get_locale_for_language
        from app.i18n.config import I18nConfig

        lang = query_params.get("lang") or query_params.get("locale")
        if lang and I18nConfig.is_language_supported(lang):
            locale = get_locale_for_language(lang)
            locale.detection_source = "query"
            return locale

        return None

    @staticmethod
    async def detect_from_geoip(ip_address: str) -> Optional[LocaleContext]:
        """Detect locale from IP address using GeoIP."""
        return None
