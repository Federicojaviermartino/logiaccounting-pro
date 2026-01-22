/**
 * Formatting hooks for numbers, currencies, dates, and times
 */
import { useMemo, useCallback } from 'react';
import { useLocale } from '../LocaleContext';
import { SUPPORTED_CURRENCIES } from '../config';

/**
 * Hook for number formatting
 */
export function useNumberFormat() {
  const { numberFormat, language } = useLocale();

  const formatNumber = useCallback((value, options = {}) => {
    const {
      decimals = 2,
      useGrouping = true,
    } = options;

    if (value === null || value === undefined || isNaN(value)) {
      return '';
    }

    const num = Number(value);
    const isNegative = num < 0;
    const absNum = Math.abs(num);

    const fixed = absNum.toFixed(decimals);
    const [intPart, decPart] = fixed.split('.');

    let formatted = intPart;
    if (useGrouping) {
      formatted = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, numberFormat.thousands);
    }

    if (decPart && decimals > 0) {
      formatted = `${formatted}${numberFormat.decimal}${decPart}`;
    }

    return isNegative ? `-${formatted}` : formatted;
  }, [numberFormat]);

  const parseNumber = useCallback((value) => {
    if (!value) return NaN;

    let cleaned = value.toString()
      .replace(new RegExp(`\\${numberFormat.thousands}`, 'g'), '')
      .replace(numberFormat.decimal, '.');

    return parseFloat(cleaned);
  }, [numberFormat]);

  const formatPercent = useCallback((value, decimals = 1) => {
    const formatted = formatNumber(value, { decimals, useGrouping: false });
    return `${formatted}%`;
  }, [formatNumber]);

  const formatCompact = useCallback((value) => {
    const num = Number(value);
    if (isNaN(num)) return '';

    const absNum = Math.abs(num);
    const sign = num < 0 ? '-' : '';

    if (absNum >= 1e12) return `${sign}${formatNumber(absNum / 1e12, { decimals: 1 })}T`;
    if (absNum >= 1e9) return `${sign}${formatNumber(absNum / 1e9, { decimals: 1 })}B`;
    if (absNum >= 1e6) return `${sign}${formatNumber(absNum / 1e6, { decimals: 1 })}M`;
    if (absNum >= 1e3) return `${sign}${formatNumber(absNum / 1e3, { decimals: 1 })}K`;

    return formatNumber(num, { decimals: 0 });
  }, [formatNumber]);

  return {
    formatNumber,
    parseNumber,
    formatPercent,
    formatCompact,
  };
}

/**
 * Hook for currency formatting
 */
export function useCurrencyFormat() {
  const { currency: defaultCurrency, numberFormat } = useLocale();
  const { formatNumber } = useNumberFormat();

  const formatCurrency = useCallback((value, options = {}) => {
    const {
      currency = defaultCurrency,
      showSymbol = true,
      showCode = false,
    } = options;

    if (value === null || value === undefined || isNaN(value)) {
      return '';
    }

    const currencyConfig = SUPPORTED_CURRENCIES.find(c => c.code === currency) || {
      symbol: '$',
      position: 'before',
      decimals: 2,
    };

    const decimals = currencyConfig.decimals ?? 2;
    const formatted = formatNumber(value, { decimals });

    let result = formatted;
    if (showSymbol) {
      if (currencyConfig.position === 'before') {
        result = `${currencyConfig.symbol}${formatted}`;
      } else {
        result = `${formatted} ${currencyConfig.symbol}`;
      }
    }

    if (showCode) {
      result = `${result} ${currency}`;
    }

    return result;
  }, [defaultCurrency, formatNumber]);

  const formatAccounting = useCallback((value, options = {}) => {
    const isNegative = value < 0;
    const formatted = formatCurrency(Math.abs(value), options);
    return isNegative ? `(${formatted})` : formatted;
  }, [formatCurrency]);

  return {
    formatCurrency,
    formatAccounting,
  };
}

/**
 * Hook for date formatting
 */
export function useDateFormat() {
  const { dateFormat, timeFormat, language, timezone } = useLocale();

  const formatDate = useCallback((value, format = 'medium') => {
    if (!value) return '';

    const date = value instanceof Date ? value : new Date(value);
    if (isNaN(date.getTime())) return '';

    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    const shortYear = year.toString().slice(-2);

    const formats = {
      short: dateFormat.replace('YYYY', shortYear).replace('MM', month).replace('DD', day),
      medium: dateFormat.replace('YYYY', year).replace('MM', month).replace('DD', day),
      long: date.toLocaleDateString(language, { dateStyle: 'long' }),
      full: date.toLocaleDateString(language, { dateStyle: 'full' }),
      iso: date.toISOString().split('T')[0],
    };

    return formats[format] || formats.medium;
  }, [dateFormat, language]);

  const formatTime = useCallback((value, showSeconds = false) => {
    if (!value) return '';

    const date = value instanceof Date ? value : new Date(value);
    if (isNaN(date.getTime())) return '';

    const options = {
      hour: '2-digit',
      minute: '2-digit',
      ...(showSeconds && { second: '2-digit' }),
      hour12: timeFormat === '12h',
    };

    return date.toLocaleTimeString(language, options);
  }, [timeFormat, language]);

  const formatDateTime = useCallback((value, options = {}) => {
    const { dateStyle = 'medium', showSeconds = false } = options;
    const datePart = formatDate(value, dateStyle);
    const timePart = formatTime(value, showSeconds);
    return `${datePart} ${timePart}`;
  }, [formatDate, formatTime]);

  const formatRelative = useCallback((value) => {
    if (!value) return '';

    const date = value instanceof Date ? value : new Date(value);
    if (isNaN(date.getTime())) return '';

    const now = new Date();
    const diff = now - date;
    const diffSeconds = Math.floor(diff / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    const rtf = new Intl.RelativeTimeFormat(language, { numeric: 'auto' });

    if (Math.abs(diffSeconds) < 60) return rtf.format(-diffSeconds, 'second');
    if (Math.abs(diffMinutes) < 60) return rtf.format(-diffMinutes, 'minute');
    if (Math.abs(diffHours) < 24) return rtf.format(-diffHours, 'hour');
    if (Math.abs(diffDays) < 7) return rtf.format(-diffDays, 'day');
    if (Math.abs(diffDays) < 30) return rtf.format(-Math.floor(diffDays / 7), 'week');
    if (Math.abs(diffDays) < 365) return rtf.format(-Math.floor(diffDays / 30), 'month');

    return rtf.format(-Math.floor(diffDays / 365), 'year');
  }, [language]);

  return {
    formatDate,
    formatTime,
    formatDateTime,
    formatRelative,
  };
}

/**
 * Combined formatters hook
 */
export function useFormatters() {
  const numberFormatters = useNumberFormat();
  const currencyFormatters = useCurrencyFormat();
  const dateFormatters = useDateFormat();

  return {
    ...numberFormatters,
    ...currencyFormatters,
    ...dateFormatters,
  };
}
