import { useState, useEffect } from 'react';

const TYPE_CONFIG = {
  success: { icon: '\u2713', bg: '#10b981', label: 'Success' },
  error:   { icon: '\u2717', bg: '#ef4444', label: 'Error' },
  warning: { icon: '\u26A0', bg: '#f59e0b', label: 'Warning' },
  info:    { icon: '\u2139', bg: '#3b82f6', label: 'Info' },
};

export default function ToastContainer() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    const handleShowToast = (event) => {
      const { id, type, message, event: eventName } = event.detail;
      const toast = {
        id: id || `t-${Date.now()}`,
        type: type || 'info',
        message: message || eventName?.replace(/[._]/g, ' ') || '',
      };

      setToasts((prev) => [...prev, toast]);

      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== toast.id));
      }, 5000);
    };

    window.addEventListener('show-toast', handleShowToast);
    return () => window.removeEventListener('show-toast', handleShowToast);
  }, []);

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  if (toasts.length === 0) return null;

  return (
    <div style={{
      position: 'fixed', top: 16, right: 16, zIndex: 99999,
      display: 'flex', flexDirection: 'column', gap: 8,
      maxWidth: 400, pointerEvents: 'none',
    }}>
      {toasts.map((toast) => {
        const cfg = TYPE_CONFIG[toast.type] || TYPE_CONFIG.info;
        return (
          <div
            key={toast.id}
            role="alert"
            aria-live="assertive"
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '12px 16px', borderRadius: 8,
              background: '#ffffff', border: `1px solid ${cfg.bg}`,
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              pointerEvents: 'auto',
              animation: 'toast-slide-in 0.25s ease-out',
            }}
          >
            <span style={{
              width: 28, height: 28, borderRadius: '50%',
              background: cfg.bg, color: '#fff',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 14, fontWeight: 700, flexShrink: 0,
            }}>
              {cfg.icon}
            </span>
            <span style={{ flex: 1, fontSize: 14, color: '#1e293b' }}>
              {toast.message}
            </span>
            <button
              onClick={() => removeToast(toast.id)}
              aria-label="Dismiss notification"
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: '#94a3b8', fontSize: 18, padding: 4, lineHeight: 1,
              }}
            >
              &times;
            </button>
          </div>
        );
      })}
      <style>{`
        @keyframes toast-slide-in {
          from { transform: translateX(100%); opacity: 0; }
          to   { transform: translateX(0);    opacity: 1; }
        }
      `}</style>
    </div>
  );
}
