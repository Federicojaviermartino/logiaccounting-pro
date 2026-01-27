"""
Internationalization configuration settings.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum


class TextDirection(str, Enum):
    """Text direction enum."""
    LTR = "ltr"
    RTL = "rtl"


class SupportedLanguage(BaseModel):
    """Supported language configuration."""
    code: str
    name: str
    native_name: str
    direction: TextDirection = TextDirection.LTR
    fallback: Optional[str] = None


class I18nConfig:
    """
    Internationalization configuration.
    """

    DEFAULT_LANGUAGE: str = "en"
    DEFAULT_CURRENCY: str = "USD"
    DEFAULT_TIMEZONE: str = "UTC"
    DEFAULT_DATE_FORMAT: str = "YYYY-MM-DD"
    DEFAULT_TIME_FORMAT: str = "24h"

    SUPPORTED_LANGUAGES: List[SupportedLanguage] = [
        SupportedLanguage(
            code="en",
            name="English",
            native_name="English",
            direction=TextDirection.LTR
        ),
        SupportedLanguage(
            code="es",
            name="Spanish",
            native_name="Español",
            direction=TextDirection.LTR,
            fallback="en"
        ),
        SupportedLanguage(
            code="de",
            name="German",
            native_name="Deutsch",
            direction=TextDirection.LTR,
            fallback="en"
        ),
        SupportedLanguage(
            code="fr",
            name="French",
            native_name="Français",
            direction=TextDirection.LTR,
            fallback="en"
        ),
        SupportedLanguage(
            code="it",
            name="Italian",
            native_name="Italiano",
            direction=TextDirection.LTR,
            fallback="en"
        ),
        SupportedLanguage(
            code="pt",
            name="Portuguese",
            native_name="Português",
            direction=TextDirection.LTR,
            fallback="es"
        ),
        SupportedLanguage(
            code="nl",
            name="Dutch",
            native_name="Nederlands",
            direction=TextDirection.LTR,
            fallback="de"
        ),
        SupportedLanguage(
            code="pl",
            name="Polish",
            native_name="Polski",
            direction=TextDirection.LTR,
            fallback="en"
        ),
        SupportedLanguage(
            code="ja",
            name="Japanese",
            native_name="日本語",
            direction=TextDirection.LTR,
            fallback="en"
        ),
        SupportedLanguage(
            code="zh",
            name="Chinese (Simplified)",
            native_name="简体中文",
            direction=TextDirection.LTR,
            fallback="en"
        ),
        SupportedLanguage(
            code="ar",
            name="Arabic",
            native_name="العربية",
            direction=TextDirection.RTL,
            fallback="en"
        ),
        SupportedLanguage(
            code="he",
            name="Hebrew",
            native_name="עברית",
            direction=TextDirection.RTL,
            fallback="en"
        ),
    ]

    SUPPORTED_CURRENCIES: List[str] = [
        "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD",
        "CNY", "HKD", "SGD", "INR", "MXN", "BRL", "SEK", "NOK",
        "DKK", "PLN", "CZK", "HUF", "RON", "BGN", "TRY", "ZAR"
    ]

    NAMESPACES: List[str] = [
        "common",
        "auth",
        "dashboard",
        "invoices",
        "clients",
        "projects",
        "transactions",
        "reports",
        "settings",
        "errors",
        "emails",
        "notifications"
    ]

    LOCALE_DETECTION_PRIORITY: List[str] = [
        "user_preference",
        "tenant_default",
        "header",
        "cookie",
        "query",
        "geoip",
        "default"
    ]

    TRANSLATION_CACHE_TTL: int = 3600
    EXCHANGE_RATE_CACHE_TTL: int = 3600

    LOCALES_DIR: str = "app/locales"

    @classmethod
    def get_language(cls, code: str) -> Optional[SupportedLanguage]:
        """Get language by code."""
        for lang in cls.SUPPORTED_LANGUAGES:
            if lang.code == code:
                return lang
        return None

    @classmethod
    def get_language_codes(cls) -> List[str]:
        """Get list of supported language codes."""
        return [lang.code for lang in cls.SUPPORTED_LANGUAGES]

    @classmethod
    def is_language_supported(cls, code: str) -> bool:
        """Check if language is supported."""
        return code in cls.get_language_codes()

    @classmethod
    def is_currency_supported(cls, code: str) -> bool:
        """Check if currency is supported."""
        return code.upper() in cls.SUPPORTED_CURRENCIES

    @classmethod
    def get_rtl_languages(cls) -> List[str]:
        """Get list of RTL language codes."""
        return [
            lang.code for lang in cls.SUPPORTED_LANGUAGES
            if lang.direction == TextDirection.RTL
        ]
