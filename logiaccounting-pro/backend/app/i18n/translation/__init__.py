"""
Translation service module.
"""
from app.i18n.translation.service import TranslationService, t, t_sync
from app.i18n.translation.loader import TranslationLoader
from app.i18n.translation.interpolation import interpolate
from app.i18n.translation.pluralization import pluralize

__all__ = [
    "TranslationService",
    "t",
    "t_sync",
    "TranslationLoader",
    "interpolate",
    "pluralize",
]
