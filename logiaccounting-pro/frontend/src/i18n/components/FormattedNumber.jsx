/**
 * Formatted Number Components
 */
import React from 'react';
import { useNumberFormat, useCurrencyFormat, useDateFormat } from '../hooks/useFormatters';

/**
 * Formatted Number Component
 */
export function FormattedNumber({
  value,
  decimals = 2,
  useGrouping = true,
  className = '',
}) {
  const { formatNumber } = useNumberFormat();

  return (
    <span className={`formatted-number ${className}`}>
      {formatNumber(value, { decimals, useGrouping })}
    </span>
  );
}

/**
 * Formatted Currency Component
 */
export function FormattedCurrency({
  value,
  currency,
  showSymbol = true,
  showCode = false,
  className = '',
}) {
  const { formatCurrency } = useCurrencyFormat();

  return (
    <span className={`formatted-currency ${className}`}>
      {formatCurrency(value, { currency, showSymbol, showCode })}
    </span>
  );
}

/**
 * Formatted Accounting Number (negatives in parentheses)
 */
export function FormattedAccounting({
  value,
  currency,
  className = '',
}) {
  const { formatAccounting } = useCurrencyFormat();
  const isNegative = value < 0;

  return (
    <span className={`formatted-accounting ${isNegative ? 'negative' : ''} ${className}`}>
      {formatAccounting(value, { currency })}
    </span>
  );
}

/**
 * Formatted Percent Component
 */
export function FormattedPercent({
  value,
  decimals = 1,
  className = '',
}) {
  const { formatPercent } = useNumberFormat();

  return (
    <span className={`formatted-percent ${className}`}>
      {formatPercent(value, decimals)}
    </span>
  );
}

/**
 * Formatted Date Component
 */
export function FormattedDate({
  value,
  format = 'medium',
  className = '',
}) {
  const { formatDate } = useDateFormat();

  return (
    <span className={`formatted-date ${className}`}>
      {formatDate(value, format)}
    </span>
  );
}

/**
 * Formatted Time Component
 */
export function FormattedTime({
  value,
  showSeconds = false,
  className = '',
}) {
  const { formatTime } = useDateFormat();

  return (
    <span className={`formatted-time ${className}`}>
      {formatTime(value, showSeconds)}
    </span>
  );
}

/**
 * Formatted DateTime Component
 */
export function FormattedDateTime({
  value,
  dateStyle = 'medium',
  showSeconds = false,
  className = '',
}) {
  const { formatDateTime } = useDateFormat();

  return (
    <span className={`formatted-datetime ${className}`}>
      {formatDateTime(value, { dateStyle, showSeconds })}
    </span>
  );
}

/**
 * Relative Time Component
 */
export function RelativeTime({
  value,
  className = '',
}) {
  const { formatRelative } = useDateFormat();

  return (
    <span className={`relative-time ${className}`} title={value?.toString()}>
      {formatRelative(value)}
    </span>
  );
}
