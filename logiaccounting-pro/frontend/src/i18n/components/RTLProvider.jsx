/**
 * RTL (Right-to-Left) Support Provider
 */
import React, { useEffect } from 'react';
import { useLocale } from '../LocaleContext';

/**
 * RTL Provider Component
 * Wraps content and provides RTL-aware styling
 */
export function RTLProvider({ children, className = '' }) {
  const { isRTL, direction, language } = useLocale();

  useEffect(() => {
    // Update CSS custom property for direction-aware styling
    document.documentElement.style.setProperty('--text-direction', direction);
    document.documentElement.style.setProperty('--start-direction', isRTL ? 'right' : 'left');
    document.documentElement.style.setProperty('--end-direction', isRTL ? 'left' : 'right');
  }, [direction, isRTL]);

  return (
    <div
      className={`rtl-provider ${isRTL ? 'rtl' : 'ltr'} ${className}`}
      dir={direction}
      lang={language}
    >
      {children}
    </div>
  );
}

/**
 * RTL-aware margin/padding helper
 */
export function useRTLStyles() {
  const { isRTL } = useLocale();

  return {
    marginStart: isRTL ? 'marginRight' : 'marginLeft',
    marginEnd: isRTL ? 'marginLeft' : 'marginRight',
    paddingStart: isRTL ? 'paddingRight' : 'paddingLeft',
    paddingEnd: isRTL ? 'paddingLeft' : 'paddingRight',
    start: isRTL ? 'right' : 'left',
    end: isRTL ? 'left' : 'right',
    transformX: (value) => isRTL ? -value : value,
  };
}

/**
 * Component that flips its children in RTL mode
 */
export function RTLFlip({ children, flip = true }) {
  const { isRTL } = useLocale();

  if (!flip || !isRTL) {
    return children;
  }

  return (
    <span style={{ transform: 'scaleX(-1)', display: 'inline-block' }}>
      {children}
    </span>
  );
}

/**
 * Bidirectional text wrapper
 */
export function Bidi({ children, direction = 'auto' }) {
  return (
    <span dir={direction} style={{ unicodeBidi: 'isolate' }}>
      {children}
    </span>
  );
}

export default RTLProvider;
