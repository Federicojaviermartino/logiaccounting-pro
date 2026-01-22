"""
Locale detection and management.
"""
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from app.i18n.config import I18nConfig, TextDirection

logger = logging.getLogger(__name__)


@dataclass
class NumberFormat:
    """Number formatting options."""
    decimal_separator: str = "."
    thousands_separator: str = ","
    decimal_places: int = 2


@dataclass
class LocaleContext:
    """
    Locale context containing all localization settings.
    """
    language: str = "en"
    direction: TextDirection = TextDirection.LTR
    region: str = "US"
    country_code: str = "US"
    currency: str = "USD"
    currency_symbol: str = "$"
    currency_position: str = "before"
    timezone: str = "UTC"
    date_format: str = "YYYY-MM-DD"
    time_format: str = "24h"
    first_day_of_week: int = 0
    number_format: NumberFormat = field(default_factory=NumberFormat)
    tax_region: Optional[str] = None
    detection_source: str = "default"

    def __post_init__(self):
        """Validate and set derived values."""
        lang_config = I18nConfig.get_language(self.language)
        if lang_config:
            self.direction = lang_config.direction

    @property
    def locale_code(self) -> str:
        """Get full locale code (e.g., 'en-US')."""
        return f"{self.language}-{self.region}"

    @property
    def is_rtl(self) -> bool:
        """Check if locale uses RTL text direction."""
        return self.direction == TextDirection.RTL

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "language": self.language,
            "direction": self.direction.value,
            "region": self.region,
            "country_code": self.country_code,
            "currency": self.currency,
            "currency_symbol": self.currency_symbol,
            "currency_position": self.currency_position,
            "timezone": self.timezone,
            "date_format": self.date_format,
            "time_format": self.time_format,
            "first_day_of_week": self.first_day_of_week,
            "number_format": {
                "decimal_separator": self.number_format.decimal_separator,
                "thousands_separator": self.number_format.thousands_separator,
                "decimal_places": self.number_format.decimal_places,
            },
            "tax_region": self.tax_region,
            "locale_code": self.locale_code,
            "is_rtl": self.is_rtl,
        }


LOCALE_PRESETS: Dict[str, LocaleContext] = {
    "en-US": LocaleContext(
        language="en",
        region="US",
        country_code="US",
        currency="USD",
        currency_symbol="$",
        currency_position="before",
        timezone="America/New_York",
        date_format="MM/DD/YYYY",
        time_format="12h",
        first_day_of_week=0,
        number_format=NumberFormat(decimal_separator=".", thousands_separator=","),
        tax_region="US"
    ),
    "en-GB": LocaleContext(
        language="en",
        region="GB",
        country_code="GB",
        currency="GBP",
        currency_symbol="£",
        currency_position="before",
        timezone="Europe/London",
        date_format="DD/MM/YYYY",
        time_format="24h",
        first_day_of_week=1,
        number_format=NumberFormat(decimal_separator=".", thousands_separator=","),
        tax_region="UK"
    ),
    "es-ES": LocaleContext(
        language="es",
        region="ES",
        country_code="ES",
        currency="EUR",
        currency_symbol="€",
        currency_position="after",
        timezone="Europe/Madrid",
        date_format="DD/MM/YYYY",
        time_format="24h",
        first_day_of_week=1,
        number_format=NumberFormat(decimal_separator=",", thousands_separator="."),
        tax_region="EU-ES"
    ),
    "de-DE": LocaleContext(
        language="de",
        region="DE",
        country_code="DE",
        currency="EUR",
        currency_symbol="€",
        currency_position="after",
        timezone="Europe/Berlin",
        date_format="DD.MM.YYYY",
        time_format="24h",
        first_day_of_week=1,
        number_format=NumberFormat(decimal_separator=",", thousands_separator="."),
        tax_region="EU-DE"
    ),
    "fr-FR": LocaleContext(
        language="fr",
        region="FR",
        country_code="FR",
        currency="EUR",
        currency_symbol="€",
        currency_position="after",
        timezone="Europe/Paris",
        date_format="DD/MM/YYYY",
        time_format="24h",
        first_day_of_week=1,
        number_format=NumberFormat(decimal_separator=",", thousands_separator=" "),
        tax_region="EU-FR"
    ),
    "it-IT": LocaleContext(
        language="it",
        region="IT",
        country_code="IT",
        currency="EUR",
        currency_symbol="€",
        currency_position="after",
        timezone="Europe/Rome",
        date_format="DD/MM/YYYY",
        time_format="24h",
        first_day_of_week=1,
        number_format=NumberFormat(decimal_separator=",", thousands_separator="."),
        tax_region="EU-IT"
    ),
    "pt-PT": LocaleContext(
        language="pt",
        region="PT",
        country_code="PT",
        currency="EUR",
        currency_symbol="€",
        currency_position="after",
        timezone="Europe/Lisbon",
        date_format="DD/MM/YYYY",
        time_format="24h",
        first_day_of_week=1,
        number_format=NumberFormat(decimal_separator=",", thousands_separator=" "),
        tax_region="EU-PT"
    ),
    "ja-JP": LocaleContext(
        language="ja",
        region="JP",
        country_code="JP",
        currency="JPY",
        currency_symbol="¥",
        currency_position="before",
        timezone="Asia/Tokyo",
        date_format="YYYY/MM/DD",
        time_format="24h",
        first_day_of_week=0,
        number_format=NumberFormat(decimal_separator=".", thousands_separator=",", decimal_places=0),
        tax_region="JP"
    ),
    "ar-SA": LocaleContext(
        language="ar",
        region="SA",
        country_code="SA",
        currency="SAR",
        currency_symbol="﷼",
        currency_position="after",
        timezone="Asia/Riyadh",
        date_format="DD/MM/YYYY",
        time_format="12h",
        first_day_of_week=0,
        number_format=NumberFormat(decimal_separator="٫", thousands_separator="٬"),
        tax_region="SA"
    ),
}


def get_locale_preset(locale_code: str) -> Optional[LocaleContext]:
    """Get preset locale configuration."""
    return LOCALE_PRESETS.get(locale_code)


def get_locale_for_language(language: str) -> LocaleContext:
    """Get default locale for a language code."""
    language_region_map = {
        "en": "US",
        "es": "ES",
        "de": "DE",
        "fr": "FR",
        "it": "IT",
        "pt": "PT",
        "nl": "NL",
        "pl": "PL",
        "ja": "JP",
        "zh": "CN",
        "ar": "SA",
        "he": "IL",
    }

    region = language_region_map.get(language, "US")
    locale_code = f"{language}-{region}"

    preset = get_locale_preset(locale_code)
    if preset:
        return preset

    return LocaleContext(language=language, region=region)
