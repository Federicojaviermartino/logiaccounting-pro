/**
 * Language Selector Component
 */
import React from 'react';
import { useLocale } from '../LocaleContext';
import { SUPPORTED_LANGUAGES } from '../config';

export function LanguageSelector({
  showNativeName = true,
  showFlag = true,
  className = '',
  onChange,
}) {
  const { language, setLanguage } = useLocale();

  const handleChange = (e) => {
    const newLang = e.target.value;
    setLanguage(newLang);
    onChange?.(newLang);
  };

  return (
    <select
      value={language}
      onChange={handleChange}
      className={`language-selector ${className}`}
      aria-label="Select language"
    >
      {SUPPORTED_LANGUAGES.map((lang) => (
        <option key={lang.code} value={lang.code}>
          {showFlag && `${getFlagEmoji(lang.flag)} `}
          {showNativeName ? lang.nativeName : lang.name}
        </option>
      ))}
    </select>
  );
}

/**
 * Language Selector as Button Group
 */
export function LanguageSelectorButtons({
  languages = SUPPORTED_LANGUAGES.slice(0, 4),
  showNativeName = false,
  showFlag = true,
  className = '',
  onChange,
}) {
  const { language, setLanguage } = useLocale();

  const handleClick = (langCode) => {
    setLanguage(langCode);
    onChange?.(langCode);
  };

  return (
    <div className={`language-selector-buttons ${className}`} role="group" aria-label="Select language">
      {languages.map((lang) => (
        <button
          key={lang.code}
          onClick={() => handleClick(lang.code)}
          className={`language-btn ${language === lang.code ? 'active' : ''}`}
          aria-pressed={language === lang.code}
        >
          {showFlag && <span className="flag">{getFlagEmoji(lang.flag)}</span>}
          {showNativeName ? lang.nativeName : lang.code.toUpperCase()}
        </button>
      ))}
    </div>
  );
}

/**
 * Get flag emoji from country code
 */
function getFlagEmoji(countryCode) {
  if (!countryCode) return '';
  const codePoints = countryCode
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
}

export default LanguageSelector;
