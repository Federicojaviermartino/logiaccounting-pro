"""
Translation message catalog loader.
"""
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from app.i18n.config import I18nConfig

logger = logging.getLogger(__name__)


class TranslationLoader:
    """
    Loader for translation message catalogs.

    Supports:
    - JSON file loading
    - Memory caching
    - Namespace organization
    """

    _cache: Dict[str, Dict[str, Any]] = {}
    _loaded: bool = False

    @classmethod
    async def load_all(cls) -> None:
        """Load all translations into cache."""
        if cls._loaded:
            return

        for lang in I18nConfig.get_language_codes():
            for namespace in I18nConfig.NAMESPACES:
                await cls.load(lang, namespace)

        cls._loaded = True
        logger.info("All translations loaded")

    @classmethod
    async def load(
        cls,
        language: str,
        namespace: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Load translations for a language and namespace.

        Args:
            language: Language code
            namespace: Translation namespace
            force: Force reload even if cached
        """
        cache_key = f"{language}:{namespace}"

        if not force and cache_key in cls._cache:
            return cls._cache[cache_key]

        translations = cls._load_from_file(language, namespace)

        if translations:
            cls._cache[cache_key] = translations
            logger.debug(f"Loaded translations: {language}/{namespace}")
        else:
            lang_config = I18nConfig.get_language(language)
            if lang_config and lang_config.fallback:
                translations = await cls.load(lang_config.fallback, namespace)

        return translations or {}

    @classmethod
    def _load_from_file(
        cls,
        language: str,
        namespace: str
    ) -> Optional[Dict[str, Any]]:
        """Load translations from JSON file."""
        file_path = Path(I18nConfig.LOCALES_DIR) / language / f"{namespace}.json"

        if not file_path.exists():
            alt_path = Path("app/locales") / language / f"{namespace}.json"
            if alt_path.exists():
                file_path = alt_path
            else:
                logger.debug(f"Translation file not found: {file_path}")
                return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None

    @classmethod
    async def reload(cls, language: Optional[str] = None) -> None:
        """
        Reload translations.

        Args:
            language: Specific language to reload, or all if None
        """
        if language:
            for namespace in I18nConfig.NAMESPACES:
                cache_key = f"{language}:{namespace}"
                cls._cache.pop(cache_key, None)
                await cls.load(language, namespace, force=True)
        else:
            cls._cache.clear()
            cls._loaded = False
            await cls.load_all()

        logger.info(f"Translations reloaded: {language or 'all'}")

    @classmethod
    def get_cached(
        cls,
        language: str,
        namespace: str
    ) -> Dict[str, Any]:
        """Get translations from memory cache (sync)."""
        cache_key = f"{language}:{namespace}"
        return cls._cache.get(cache_key, {})

    @classmethod
    async def get_all_for_language(
        cls,
        language: str
    ) -> Dict[str, Dict[str, Any]]:
        """Get all translations for a language."""
        result = {}
        for namespace in I18nConfig.NAMESPACES:
            result[namespace] = await cls.load(language, namespace)
        return result
