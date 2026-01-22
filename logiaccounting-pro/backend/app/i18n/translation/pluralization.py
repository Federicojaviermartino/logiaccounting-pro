"""
Pluralization rules following CLDR standards.
"""
from typing import Dict


def pluralize(
    forms: Dict[str, str],
    count: int,
    language: str
) -> str:
    """
    Select the correct plural form based on count and language rules.

    CLDR plural categories:
    - zero: Used in some languages for 0
    - one: Singular (typically count == 1)
    - two: Dual (used in some languages for exactly 2)
    - few: Paucal (small numbers, varies by language)
    - many: Large numbers (varies by language)
    - other: General plural (default)

    Args:
        forms: Dictionary with plural forms
        count: The number to determine plural form
        language: Language code for rules

    Returns:
        Selected plural form string

    Example forms:
        {
            "zero": "No items",
            "one": "{{count}} item",
            "other": "{{count}} items"
        }
    """
    category = get_plural_category(count, language)

    if category in forms:
        return forms[category].replace("{{count}}", str(count))

    fallback_chain = ["other", "many", "few", "one"]
    for fallback in fallback_chain:
        if fallback in forms:
            return forms[fallback].replace("{{count}}", str(count))

    return str(count)


def get_plural_category(count: int, language: str) -> str:
    """
    Get CLDR plural category for a number and language.

    Implements rules for common languages.
    """
    rule_func = PLURAL_RULES.get(language, plural_rule_default)
    return rule_func(count)


def plural_rule_default(n: int) -> str:
    """Default plural rule (English-like)."""
    if n == 1:
        return "one"
    return "other"


def plural_rule_english(n: int) -> str:
    """English plural rule."""
    if n == 1:
        return "one"
    return "other"


def plural_rule_french(n: int) -> str:
    """French plural rule (0 and 1 are singular)."""
    if n in (0, 1):
        return "one"
    return "other"


def plural_rule_german(n: int) -> str:
    """German plural rule."""
    if n == 1:
        return "one"
    return "other"


def plural_rule_spanish(n: int) -> str:
    """Spanish plural rule."""
    if n == 1:
        return "one"
    return "other"


def plural_rule_russian(n: int) -> str:
    """
    Russian plural rule.

    - one: 1, 21, 31, ...
    - few: 2-4, 22-24, 32-34, ...
    - many: 0, 5-20, 25-30, ...
    """
    n_mod_10 = n % 10
    n_mod_100 = n % 100

    if n_mod_10 == 1 and n_mod_100 != 11:
        return "one"
    if n_mod_10 >= 2 and n_mod_10 <= 4 and (n_mod_100 < 12 or n_mod_100 > 14):
        return "few"
    return "many"


def plural_rule_polish(n: int) -> str:
    """
    Polish plural rule.

    - one: 1
    - few: 2-4, 22-24, 32-34, ...
    - many: 0, 5-21, 25-31, ...
    """
    n_mod_10 = n % 10
    n_mod_100 = n % 100

    if n == 1:
        return "one"
    if n_mod_10 >= 2 and n_mod_10 <= 4 and (n_mod_100 < 12 or n_mod_100 > 14):
        return "few"
    return "many"


def plural_rule_arabic(n: int) -> str:
    """
    Arabic plural rule.

    - zero: 0
    - one: 1
    - two: 2
    - few: 3-10, 103-110, ...
    - many: 11-99, 111-199, ...
    - other: 100-102, 200-202, ...
    """
    n_mod_100 = n % 100

    if n == 0:
        return "zero"
    if n == 1:
        return "one"
    if n == 2:
        return "two"
    if n_mod_100 >= 3 and n_mod_100 <= 10:
        return "few"
    if n_mod_100 >= 11:
        return "many"
    return "other"


def plural_rule_japanese(n: int) -> str:
    """Japanese has no plural forms."""
    return "other"


def plural_rule_chinese(n: int) -> str:
    """Chinese has no plural forms."""
    return "other"


PLURAL_RULES = {
    "en": plural_rule_english,
    "de": plural_rule_german,
    "fr": plural_rule_french,
    "es": plural_rule_spanish,
    "it": plural_rule_default,
    "pt": plural_rule_default,
    "nl": plural_rule_default,
    "pl": plural_rule_polish,
    "ru": plural_rule_russian,
    "uk": plural_rule_russian,
    "ar": plural_rule_arabic,
    "he": plural_rule_default,
    "ja": plural_rule_japanese,
    "zh": plural_rule_chinese,
    "ko": plural_rule_japanese,
}
