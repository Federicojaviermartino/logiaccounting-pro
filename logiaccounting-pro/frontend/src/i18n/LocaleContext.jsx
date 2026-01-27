/**
 * Locale Context Provider for React applications
 */
import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, LOCALE_PRESETS, isRTL } from './config';

const LocaleContext = createContext(null);

const STORAGE_KEY = 'logiaccounting_locale';

/**
 * Get initial locale from storage or browser
 */
function getInitialLocale() {
  if (typeof window === 'undefined') {
    return DEFAULT_LANGUAGE;
  }

  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    try {
      const parsed = JSON.parse(stored);
      if (parsed.language && SUPPORTED_LANGUAGES.some(l => l.code === parsed.language)) {
        return parsed.language;
      }
    } catch (e) {
      // Ignore parse errors
    }
  }

  const browserLang = navigator.language?.split('-')[0];
  if (browserLang && SUPPORTED_LANGUAGES.some(l => l.code === browserLang)) {
    return browserLang;
  }

  return DEFAULT_LANGUAGE;
}

/**
 * Get initial locale settings
 */
function getInitialSettings() {
  if (typeof window === 'undefined') {
    return LOCALE_PRESETS['en-US'];
  }

  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch (e) {
      // Ignore parse errors
    }
  }

  const language = getInitialLocale();
  const preset = Object.values(LOCALE_PRESETS).find(p => p.language === language);
  return preset || LOCALE_PRESETS['en-US'];
}

/**
 * LocaleProvider component
 */
export function LocaleProvider({ children, initialLocale }) {
  const [settings, setSettings] = useState(() => {
    if (initialLocale) {
      const preset = Object.values(LOCALE_PRESETS).find(p => p.language === initialLocale);
      return preset || { ...LOCALE_PRESETS['en-US'], language: initialLocale };
    }
    return getInitialSettings();
  });

  const [translations, setTranslations] = useState({});
  const [loading, setLoading] = useState(true);

  // Load translations for current language
  const loadTranslations = useCallback(async (language) => {
    setLoading(true);
    try {
      const module = await import(`./translations/${language}.js`);
      setTranslations(module.default || module);
    } catch (error) {
      console.warn(`Failed to load translations for ${language}, falling back to English`);
      try {
        const fallback = await import('./translations/en.js');
        setTranslations(fallback.default || fallback);
      } catch (e) {
        console.error('Failed to load fallback translations');
        setTranslations({});
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // Load translations on language change
  useEffect(() => {
    loadTranslations(settings.language);
  }, [settings.language, loadTranslations]);

  // Update document direction for RTL support
  useEffect(() => {
    if (typeof document !== 'undefined') {
      const direction = isRTL(settings.language) ? 'rtl' : 'ltr';
      document.documentElement.dir = direction;
      document.documentElement.lang = settings.language;
    }
  }, [settings.language]);

  // Persist settings
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    }
  }, [settings]);

  // Change language
  const setLanguage = useCallback((language) => {
    const preset = Object.values(LOCALE_PRESETS).find(p => p.language === language);
    setSettings(prev => ({
      ...prev,
      language,
      ...(preset ? {
        dateFormat: preset.dateFormat,
        timeFormat: preset.timeFormat,
        numberFormat: preset.numberFormat,
      } : {}),
    }));
  }, []);

  // Change currency
  const setCurrency = useCallback((currency) => {
    setSettings(prev => ({ ...prev, currency }));
  }, []);

  // Change region
  const setRegion = useCallback((region) => {
    setSettings(prev => ({ ...prev, region }));
  }, []);

  // Change timezone
  const setTimezone = useCallback((timezone) => {
    setSettings(prev => ({ ...prev, timezone }));
  }, []);

  // Update settings
  const updateSettings = useCallback((newSettings) => {
    setSettings(prev => ({ ...prev, ...newSettings }));
  }, []);

  // Get translation
  const t = useCallback((key, params = {}) => {
    const keys = key.split('.');
    let value = translations;

    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        return key;
      }
    }

    if (typeof value !== 'string') {
      return key;
    }

    // Handle interpolation
    return value.replace(/\{\{(\w+)\}\}/g, (match, name) => {
      return params[name] !== undefined ? String(params[name]) : match;
    });
  }, [translations]);

  // Get plural translation
  const tn = useCallback((key, count, params = {}) => {
    const keys = key.split('.');
    let value = translations;

    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        return key;
      }
    }

    if (typeof value === 'object') {
      let form = 'other';
      if (count === 0 && value.zero) form = 'zero';
      else if (count === 1 && value.one) form = 'one';
      else if (count === 2 && value.two) form = 'two';

      const text = value[form] || value.other || key;
      return text.replace(/\{\{count\}\}/g, String(count))
        .replace(/\{\{(\w+)\}\}/g, (match, name) => {
          return params[name] !== undefined ? String(params[name]) : match;
        });
    }

    return key;
  }, [translations]);

  const value = useMemo(() => ({
    ...settings,
    translations,
    loading,
    direction: isRTL(settings.language) ? 'rtl' : 'ltr',
    isRTL: isRTL(settings.language),
    t,
    tn,
    setLanguage,
    setCurrency,
    setRegion,
    setTimezone,
    updateSettings,
  }), [settings, translations, loading, t, tn, setLanguage, setCurrency, setRegion, setTimezone, updateSettings]);

  return (
    <LocaleContext.Provider value={value}>
      {children}
    </LocaleContext.Provider>
  );
}

/**
 * Hook to access locale context
 */
export function useLocale() {
  const context = useContext(LocaleContext);
  if (!context) {
    throw new Error('useLocale must be used within a LocaleProvider');
  }
  return context;
}

/**
 * Hook to access translation function
 */
export function useTranslation() {
  const { t, tn, loading } = useLocale();
  return { t, tn, loading };
}

export default LocaleContext;
