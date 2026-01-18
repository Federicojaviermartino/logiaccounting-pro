import en from './translations/en';
import es from './translations/es';

export const translations = {
  en,
  es
};

export const languages = [
  { code: 'en', name: 'English', flag: 'US' },
  { code: 'es', name: 'Espanol', flag: 'AR' }
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
      return path; // Return the key if translation not found
    }
  }

  return result;
}
