import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { translations, languages, defaultLanguage, getNestedValue } from '../i18n';

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => {
    // Check localStorage first
    const saved = localStorage.getItem('language');
    if (saved && translations[saved]) {
      return saved;
    }
    // Check browser language
    const browserLang = navigator.language.split('-')[0];
    if (translations[browserLang]) {
      return browserLang;
    }
    return defaultLanguage;
  });

  useEffect(() => {
    localStorage.setItem('language', language);
    document.documentElement.lang = language;
  }, [language]);

  // Translate function - t('common.save') -> 'Save' or 'Guardar'
  const t = useCallback((key, params = {}) => {
    let translated = getNestedValue(translations[language], key);

    // Replace parameters like {name} with actual values
    if (typeof translated === 'string' && Object.keys(params).length > 0) {
      Object.entries(params).forEach(([param, value]) => {
        translated = translated.replace(new RegExp(`{${param}}`, 'g'), value);
      });
    }

    return translated;
  }, [language]);

  // Change language
  const changeLanguage = useCallback((newLang) => {
    if (translations[newLang]) {
      setLanguage(newLang);
    }
  }, []);

  // Get current language info
  const currentLanguage = languages.find(l => l.code === language) || languages[0];

  return (
    <LanguageContext.Provider value={{
      language,
      languages,
      currentLanguage,
      changeLanguage,
      t
    }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}

export default LanguageContext;
