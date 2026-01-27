import { useEffect, useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export function useKeyboardShortcuts({ onCommandPalette, onShowShortcuts, onCloseModal }) {
  const navigate = useNavigate();
  const [pendingKey, setPendingKey] = useState(null);

  const handleKeyDown = useCallback((e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
      if (e.key === 'Escape') e.target.blur();
      return;
    }

    const ctrl = e.ctrlKey || e.metaKey;
    const key = e.key.toLowerCase();

    if (ctrl && key === 'k') {
      e.preventDefault();
      onCommandPalette?.();
      return;
    }

    if (ctrl && key === '/') {
      e.preventDefault();
      onShowShortcuts?.();
      return;
    }

    if (key === 'escape') {
      onCloseModal?.();
      return;
    }

    if (pendingKey === 'g') {
      setPendingKey(null);
      const routes = {
        d: '/dashboard',
        i: '/inventory',
        p: '/projects',
        t: '/transactions',
        y: '/payments',
        r: '/reports',
        s: '/settings'
      };
      if (routes[key]) navigate(routes[key]);
      return;
    }

    if (key === 'g') {
      setPendingKey('g');
      setTimeout(() => setPendingKey(null), 1000);
    }
  }, [navigate, pendingKey, onCommandPalette, onShowShortcuts, onCloseModal]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return { pendingKey };
}
