/**
 * Internationalization Module for LogiAccounting Pro
 *
 * This module provides comprehensive i18n support including:
 * - Multi-language translations
 * - Currency formatting
 * - Date/time formatting
 * - Number formatting
 * - RTL (Right-to-Left) support
 */

// Configuration
export {
  SUPPORTED_LANGUAGES,
  SUPPORTED_CURRENCIES,
  DEFAULT_LANGUAGE,
  LOCALE_PRESETS,
  getLanguageDirection,
  isRTL,
} from './config';

// Context and hooks
export {
  LocaleProvider,
  useLocale,
  useTranslation,
} from './LocaleContext';

// Formatting hooks
export {
  useNumberFormat,
  useCurrencyFormat,
  useDateFormat,
  useFormatters,
} from './hooks/useFormatters';

// Components
export {
  LanguageSelector,
  LanguageSelectorButtons,
} from './components/LanguageSelector';

export {
  FormattedNumber,
  FormattedCurrency,
  FormattedAccounting,
  FormattedPercent,
  FormattedDate,
  FormattedTime,
  FormattedDateTime,
  RelativeTime,
} from './components/FormattedNumber';

export {
  RTLProvider,
  RTLFlip,
  Bidi,
  useRTLStyles,
} from './components/RTLProvider';

// Translations
import en from './translations/en';
import es from './translations/es';
import de from './translations/de';
import fr from './translations/fr';

export const translations = {
  en,
  es,
  de,
  fr,
};

export const languages = [
  { code: 'en', name: 'English', nativeName: 'English', flag: 'US' },
  { code: 'es', name: 'Spanish', nativeName: 'Español', flag: 'ES' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', flag: 'DE' },
  { code: 'fr', name: 'French', nativeName: 'Français', flag: 'FR' },
];

export const defaultLanguage = 'en';

/**
 * Get a nested translation value by key path
 * @param {object} obj - Translation object
 * @param {string} path - Dot-separated path (e.g., 'common.save')
 * @returns {string} - Translated string or key if not found
 */
export function getNestedValue(obj, path) {
  const keys = path.split('.');
  let result = obj;

  for (const key of keys) {
    if (result && typeof result === 'object' && key in result) {
      result = result[key];
    } else {
      return path;
    }
  }

  return result;
}
