/**
 * i18n Configuration for LogiAccounting Pro
 */

export const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', nativeName: 'English', direction: 'ltr', flag: 'US' },
  { code: 'es', name: 'Spanish', nativeName: 'Español', direction: 'ltr', flag: 'ES' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', direction: 'ltr', flag: 'DE' },
  { code: 'fr', name: 'French', nativeName: 'Français', direction: 'ltr', flag: 'FR' },
  { code: 'it', name: 'Italian', nativeName: 'Italiano', direction: 'ltr', flag: 'IT' },
  { code: 'pt', name: 'Portuguese', nativeName: 'Português', direction: 'ltr', flag: 'PT' },
  { code: 'nl', name: 'Dutch', nativeName: 'Nederlands', direction: 'ltr', flag: 'NL' },
  { code: 'pl', name: 'Polish', nativeName: 'Polski', direction: 'ltr', flag: 'PL' },
  { code: 'ja', name: 'Japanese', nativeName: '日本語', direction: 'ltr', flag: 'JP' },
  { code: 'zh', name: 'Chinese', nativeName: '中文', direction: 'ltr', flag: 'CN' },
  { code: 'ar', name: 'Arabic', nativeName: 'العربية', direction: 'rtl', flag: 'SA' },
];

export const DEFAULT_LANGUAGE = 'en';

export const SUPPORTED_CURRENCIES = [
  { code: 'USD', name: 'US Dollar', symbol: '$', position: 'before' },
  { code: 'EUR', name: 'Euro', symbol: '€', position: 'after' },
  { code: 'GBP', name: 'British Pound', symbol: '£', position: 'before' },
  { code: 'JPY', name: 'Japanese Yen', symbol: '¥', position: 'before', decimals: 0 },
  { code: 'CHF', name: 'Swiss Franc', symbol: 'CHF', position: 'before' },
  { code: 'CAD', name: 'Canadian Dollar', symbol: '$', position: 'before' },
  { code: 'AUD', name: 'Australian Dollar', symbol: '$', position: 'before' },
  { code: 'CNY', name: 'Chinese Yuan', symbol: '¥', position: 'before' },
  { code: 'INR', name: 'Indian Rupee', symbol: '₹', position: 'before' },
  { code: 'MXN', name: 'Mexican Peso', symbol: '$', position: 'before' },
  { code: 'BRL', name: 'Brazilian Real', symbol: 'R$', position: 'before' },
  { code: 'ARS', name: 'Argentine Peso', symbol: '$', position: 'before' },
];

export const LOCALE_PRESETS = {
  'en-US': {
    language: 'en',
    region: 'US',
    currency: 'USD',
    dateFormat: 'MM/DD/YYYY',
    timeFormat: '12h',
    numberFormat: { decimal: '.', thousands: ',' },
  },
  'en-GB': {
    language: 'en',
    region: 'GB',
    currency: 'GBP',
    dateFormat: 'DD/MM/YYYY',
    timeFormat: '24h',
    numberFormat: { decimal: '.', thousands: ',' },
  },
  'es-ES': {
    language: 'es',
    region: 'ES',
    currency: 'EUR',
    dateFormat: 'DD/MM/YYYY',
    timeFormat: '24h',
    numberFormat: { decimal: ',', thousands: '.' },
  },
  'es-AR': {
    language: 'es',
    region: 'AR',
    currency: 'ARS',
    dateFormat: 'DD/MM/YYYY',
    timeFormat: '24h',
    numberFormat: { decimal: ',', thousands: '.' },
  },
  'de-DE': {
    language: 'de',
    region: 'DE',
    currency: 'EUR',
    dateFormat: 'DD.MM.YYYY',
    timeFormat: '24h',
    numberFormat: { decimal: ',', thousands: '.' },
  },
  'fr-FR': {
    language: 'fr',
    region: 'FR',
    currency: 'EUR',
    dateFormat: 'DD/MM/YYYY',
    timeFormat: '24h',
    numberFormat: { decimal: ',', thousands: ' ' },
  },
  'ja-JP': {
    language: 'ja',
    region: 'JP',
    currency: 'JPY',
    dateFormat: 'YYYY/MM/DD',
    timeFormat: '24h',
    numberFormat: { decimal: '.', thousands: ',' },
  },
  'ar-SA': {
    language: 'ar',
    region: 'SA',
    currency: 'SAR',
    dateFormat: 'DD/MM/YYYY',
    timeFormat: '12h',
    numberFormat: { decimal: '.', thousands: ',' },
  },
};

export const getLanguageDirection = (languageCode) => {
  const language = SUPPORTED_LANGUAGES.find(l => l.code === languageCode);
  return language?.direction || 'ltr';
};

export const isRTL = (languageCode) => {
  return getLanguageDirection(languageCode) === 'rtl';
};
