import { useState, useEffect } from 'react';

export default function ToastContainer() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    const handleShowToast = (event) => {
      const notification = event.detail;
      const toast = {
        id: notification.id,
        event: notification.event,
        message: notification.event?.replace(/\./g, ' ').replace(/_/g, ' ')
      };

      setToasts(prev => [...prev, toast]);

      // Auto remove after 5 seconds
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== toast.id));
      }, 5000);
    };

    window.addEventListener('show-toast', handleShowToast);
    return () => window.removeEventListener('show-toast', handleShowToast);
  }, []);

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const getEventIcon = (event) => {
    const icons = {
      'transaction.created': '$',
      'payment.due_soon': '!',
      'payment.overdue': '!',
      'inventory.low_stock': '*',
      'approval.required': '+',
      'budget.threshold_reached': '$',
      'anomaly.detected': '!'
    };
    return icons[event] || '!';
  };

  return (
    <div className="toast-container">
      {toasts.map(toast => (
        <div key={toast.id} className="toast">
          <span className="toast-icon">{getEventIcon(toast.event)}</span>
          <span className="toast-message">{toast.message}</span>
          <button className="toast-close" onClick={() => removeToast(toast.id)}>x</button>
        </div>
      ))}
    </div>
  );
}
