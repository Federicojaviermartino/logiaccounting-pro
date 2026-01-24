/**
 * Update Available - Notification for PWA updates
 */

import React, { useState, useEffect } from 'react';
import { RefreshCw, X } from 'lucide-react';
import { swManager } from '../../pwa/serviceWorker';

export default function UpdateAvailable() {
  const [showUpdate, setShowUpdate] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    swManager.onUpdateAvailable = () => {
      setShowUpdate(true);
    };

    if (swManager.updateAvailable) {
      setShowUpdate(true);
    }
  }, []);

  const handleUpdate = () => {
    setIsUpdating(true);
    swManager.applyUpdate();
  };

  if (!showUpdate) return null;

  return (
    <div className="update-banner">
      <div className="update-content">
        <RefreshCw className={`update-icon ${isUpdating ? 'spinning' : ''}`} />
        <span className="update-text">
          {isUpdating ? 'Updating...' : 'A new version is available'}
        </span>
      </div>

      <div className="update-actions">
        {!isUpdating && (
          <>
            <button className="update-btn" onClick={handleUpdate}>
              Update Now
            </button>
            <button className="dismiss-btn" onClick={() => setShowUpdate(false)}>
              <X className="w-4 h-4" />
            </button>
          </>
        )}
      </div>

      <style jsx>{`
        .update-banner {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          background: linear-gradient(135deg, var(--primary), var(--primary-dark));
          color: white;
          z-index: 1000;
          animation: slideDown 0.3s ease-out;
        }

        @keyframes slideDown {
          from { transform: translateY(-100%); }
          to { transform: translateY(0); }
        }

        .update-content { display: flex; align-items: center; gap: 12px; }
        .update-icon { width: 20px; height: 20px; }
        .update-icon.spinning { animation: spin 1s linear infinite; }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .update-text { font-size: 14px; font-weight: 500; }
        .update-actions { display: flex; align-items: center; gap: 8px; }

        .update-btn {
          padding: 8px 16px;
          background: white;
          color: var(--primary);
          border-radius: 8px;
          font-size: 13px;
          font-weight: 600;
        }

        .dismiss-btn {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          opacity: 0.8;
        }
      `}</style>
    </div>
  );
}
