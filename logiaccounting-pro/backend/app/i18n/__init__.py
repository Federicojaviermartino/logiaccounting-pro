"""
Internationalization and Localization module for LogiAccounting Pro.

This module provides comprehensive i18n/l10n support including:
- Multi-language translations with interpolation and pluralization
- Multi-currency support with real-time exchange rates
- Regional tax calculations (EU VAT, US Sales Tax, UK VAT, GST)
- Date/time/number formatting per locale
- Address formatting by country
- RTL language support
"""

from app.i18n.config import I18nConfig
from app.i18n.core.context import get_locale, set_locale, LocaleContextManager
from app.i18n.core.locale import LocaleContext, LOCALE_PRESETS
from app.i18n.translation.service import t, t_sync, TranslationService
from app.i18n.currency.formatter import format_currency
from app.i18n.datetime.formatter import format_date, format_time, format_datetime

__all__ = [
    "I18nConfig",
    "get_locale",
    "set_locale",
    "LocaleContextManager",
    "LocaleContext",
    "LOCALE_PRESETS",
    "t",
    "t_sync",
    "TranslationService",
    "format_currency",
    "format_date",
    "format_time",
    "format_datetime",
]
