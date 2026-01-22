"""
Base template engine with localization support.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
from pathlib import Path
import jinja2

from app.i18n.core.context import get_locale
from app.i18n.core.locale import LocaleContext
from app.i18n.translation.service import t_sync
from app.i18n.currency.formatter import format_currency
from app.i18n.datetime.formatter import format_date, format_datetime


@dataclass
class TemplateContext:
    """Template rendering context."""
    locale: LocaleContext
    data: Dict[str, Any]
    translations: Dict[str, str]


class LocalizedTemplate(ABC):
    """Base class for localized templates."""

    @property
    @abstractmethod
    def template_name(self) -> str:
        """Template file name."""
        pass

    @abstractmethod
    def get_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build template context."""
        pass

    def render(
        self,
        data: Dict[str, Any],
        locale: Optional[LocaleContext] = None
    ) -> str:
        """Render template with data."""
        if not locale:
            locale = get_locale()

        context = self.get_context(data)
        context["locale"] = locale
        context["direction"] = locale.direction.value
        context["is_rtl"] = locale.direction.value == "rtl"

        return TemplateEngine.render(self.template_name, context)


class TemplateEngine:
    """Template rendering engine with i18n support."""

    _env: Optional[jinja2.Environment] = None
    _templates_dir: Path = Path(__file__).parent / "html"

    @classmethod
    def get_environment(cls) -> jinja2.Environment:
        """Get or create Jinja2 environment."""
        if cls._env is None:
            cls._env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(str(cls._templates_dir)),
                autoescape=jinja2.select_autoescape(["html", "xml"]),
                trim_blocks=True,
                lstrip_blocks=True,
            )

            cls._env.filters["t"] = cls._translate_filter
            cls._env.filters["currency"] = cls._currency_filter
            cls._env.filters["date"] = cls._date_filter
            cls._env.filters["datetime"] = cls._datetime_filter
            cls._env.filters["number"] = cls._number_filter

            cls._env.globals["t"] = t_sync
            cls._env.globals["format_currency"] = format_currency
            cls._env.globals["format_date"] = format_date
            cls._env.globals["format_datetime"] = format_datetime

        return cls._env

    @classmethod
    def render(cls, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template."""
        env = cls.get_environment()
        template = env.get_template(template_name)
        return template.render(**context)

    @classmethod
    def render_string(cls, template_string: str, context: Dict[str, Any]) -> str:
        """Render a template from string."""
        env = cls.get_environment()
        template = env.from_string(template_string)
        return template.render(**context)

    @staticmethod
    def _translate_filter(key: str, **kwargs) -> str:
        """Jinja2 filter for translation."""
        return t_sync(key, **kwargs)

    @staticmethod
    def _currency_filter(value: float, currency_code: Optional[str] = None) -> str:
        """Jinja2 filter for currency formatting."""
        return format_currency(value, currency_code)

    @staticmethod
    def _date_filter(value, format_type: str = "medium") -> str:
        """Jinja2 filter for date formatting."""
        return format_date(value, format_type)

    @staticmethod
    def _datetime_filter(value, format_type: str = "medium") -> str:
        """Jinja2 filter for datetime formatting."""
        return format_datetime(value, format_type)

    @staticmethod
    def _number_filter(value: float, decimals: int = 2) -> str:
        """Jinja2 filter for number formatting."""
        from app.i18n.datetime.numbers import format_number
        return format_number(value, decimals)
