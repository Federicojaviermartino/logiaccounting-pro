/**
 * i18n Configuration
 * Internationalization setup with react-i18next
 */

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import * as RNLocalize from 'react-native-localize';

import en from './locales/en';
import es from './locales/es';

const resources = {
  en: { translation: en },
  es: { translation: es },
};

// Get device language
const getDeviceLanguage = (): string => {
  const locales = RNLocalize.getLocales();
  if (locales.length > 0) {
    const { languageCode } = locales[0];
    if (Object.keys(resources).includes(languageCode)) {
      return languageCode;
    }
  }
  return 'en';
};

i18n.use(initReactI18next).init({
  resources,
  lng: getDeviceLanguage(),
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
  react: {
    useSuspense: false,
  },
});

export const changeLanguage = (lang: string) => {
  i18n.changeLanguage(lang);
};

export const getCurrentLanguage = () => {
  return i18n.language;
};

export const getSupportedLanguages = () => {
  return [
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Español' },
  ];
};

export default i18n;
