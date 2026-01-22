"""
Translation service with interpolation and pluralization.
"""
import re
import logging
from typing import Any, Dict, Optional, Union, List

from app.i18n.config import I18nConfig
from app.i18n.core.context import get_locale
from app.i18n.translation.loader import TranslationLoader
from app.i18n.translation.interpolation import interpolate
from app.i18n.translation.pluralization import pluralize

logger = logging.getLogger(__name__)


class TranslationService:
    """
    Translation service providing message lookup, interpolation, and pluralization.

    Usage:
        # Simple translation
        t('common.hello')  # "Hello"

        # With interpolation
        t('common.greeting', name='John')  # "Hello, John!"

        # With pluralization
        t('items.count', count=5)  # "5 items"

        # With namespace
        t('invoices:status.paid')  # From invoices namespace
    """

    INTERPOLATION_PATTERN = re.compile(r'\{\{(\w+)\}\}')
    KEY_SEPARATOR = "."
    NAMESPACE_SEPARATOR = ":"

    @classmethod
    async def translate(
        cls,
        key: str,
        language: Optional[str] = None,
        namespace: Optional[str] = None,
        default: Optional[str] = None,
        count: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Translate a message key.

        Args:
            key: Message key (e.g., 'common.hello' or 'invoices:status.paid')
            language: Language code (uses context if not provided)
            namespace: Namespace (extracted from key if not provided)
            default: Default value if key not found
            count: Count for pluralization
            **kwargs: Variables for interpolation

        Returns:
            Translated string
        """
        if not language:
            locale = get_locale()
            language = locale.language

        if cls.NAMESPACE_SEPARATOR in key:
            namespace, key = key.split(cls.NAMESPACE_SEPARATOR, 1)
        elif not namespace:
            namespace = "common"

        translations = await TranslationLoader.load(language, namespace)

        message = cls._get_nested(translations, key)

        if message is None:
            lang_config = I18nConfig.get_language(language)
            if lang_config and lang_config.fallback:
                fallback_translations = await TranslationLoader.load(
                    lang_config.fallback, namespace
                )
                message = cls._get_nested(fallback_translations, key)

            if message is None:
                logger.warning(f"Translation not found: {namespace}:{key} [{language}]")
                return default if default is not None else key

        if count is not None and isinstance(message, dict):
            message = pluralize(message, count, language)
        elif isinstance(message, dict):
            message = message.get("other", message.get("one", str(message)))

        if kwargs:
            message = interpolate(message, kwargs)

        return message

    @classmethod
    def translate_sync(
        cls,
        key: str,
        language: Optional[str] = None,
        namespace: Optional[str] = None,
        default: Optional[str] = None,
        count: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Synchronous translation (uses cached translations only).

        Use this in contexts where async is not available.
        """
        if not language:
            locale = get_locale()
            language = locale.language

        if cls.NAMESPACE_SEPARATOR in key:
            namespace, key = key.split(cls.NAMESPACE_SEPARATOR, 1)
        elif not namespace:
            namespace = "common"

        translations = TranslationLoader.get_cached(language, namespace)
        message = cls._get_nested(translations, key)

        if message is None:
            return default if default is not None else key

        if count is not None and isinstance(message, dict):
            message = pluralize(message, count, language)
        elif isinstance(message, dict):
            message = message.get("other", message.get("one", str(message)))

        if kwargs:
            message = interpolate(message, kwargs)

        return message

    @classmethod
    def _get_nested(
        cls,
        data: Dict[str, Any],
        key: str
    ) -> Optional[Union[str, Dict]]:
        """Get nested value from dictionary using dot notation."""
        keys = key.split(cls.KEY_SEPARATOR)
        value = data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None

        return value

    @classmethod
    async def has_translation(
        cls,
        key: str,
        language: Optional[str] = None,
        namespace: Optional[str] = None
    ) -> bool:
        """Check if a translation exists."""
        if not language:
            locale = get_locale()
            language = locale.language

        if cls.NAMESPACE_SEPARATOR in key:
            namespace, key = key.split(cls.NAMESPACE_SEPARATOR, 1)
        elif not namespace:
            namespace = "common"

        translations = await TranslationLoader.load(language, namespace)
        return cls._get_nested(translations, key) is not None

    @classmethod
    async def get_all_keys(
        cls,
        language: str,
        namespace: str
    ) -> List[str]:
        """Get all translation keys for a namespace."""
        translations = await TranslationLoader.load(language, namespace)
        return cls._flatten_keys(translations)

    @classmethod
    def _flatten_keys(
        cls,
        data: Dict[str, Any],
        prefix: str = ""
    ) -> List[str]:
        """Flatten nested dictionary to list of dot-notation keys."""
        keys = []
        for key, value in data.items():
            full_key = f"{prefix}{cls.KEY_SEPARATOR}{key}" if prefix else key
            if isinstance(value, dict) and not cls._is_plural_object(value):
                keys.extend(cls._flatten_keys(value, full_key))
            else:
                keys.append(full_key)
        return keys

    @classmethod
    def _is_plural_object(cls, obj: Dict) -> bool:
        """Check if object is a plural forms object."""
        plural_keys = {"zero", "one", "two", "few", "many", "other"}
        return bool(set(obj.keys()) & plural_keys)


async def t(
    key: str,
    language: Optional[str] = None,
    **kwargs
) -> str:
    """
    Shorthand for translation.

    Usage:
        message = await t('common.hello')
        message = await t('common.greeting', name='John')
        message = await t('items.count', count=5)
    """
    return await TranslationService.translate(key, language, **kwargs)


def t_sync(
    key: str,
    language: Optional[str] = None,
    **kwargs
) -> str:
    """
    Synchronous translation shorthand.

    Usage:
        message = t_sync('common.hello')
    """
    return TranslationService.translate_sync(key, language, **kwargs)
