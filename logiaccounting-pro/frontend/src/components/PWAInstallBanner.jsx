import { useState } from 'react';
import { usePWA } from '../hooks/usePWA';

export default function PWAInstallBanner() {
  const { canInstall, installApp, updateAvailable, updateApp } = usePWA();
  const [dismissed, setDismissed] = useState(false);

  // Show update banner
  if (updateAvailable) {
    return (
      <div className="pwa-banner pwa-update">
        <div className="pwa-banner-content">
          <span className="pwa-icon">🔄</span>
          <div className="pwa-text">
            <strong>Update Available</strong>
            <p>A new version is ready. Refresh to update.</p>
          </div>
        </div>
        <div className="pwa-actions">
          <button className="pwa-btn pwa-btn-primary" onClick={updateApp}>
            Update Now
          </button>
        </div>
      </div>
    );
  }

  // Show install banner
  if (canInstall && !dismissed) {
    return (
      <div className="pwa-banner pwa-install">
        <div className="pwa-banner-content">
          <span className="pwa-icon">📱</span>
          <div className="pwa-text">
            <strong>Install LogiAccounting</strong>
            <p>Add to your home screen for quick access</p>
          </div>
        </div>
        <div className="pwa-actions">
          <button className="pwa-btn pwa-btn-secondary" onClick={() => setDismissed(true)}>
            Not Now
          </button>
          <button className="pwa-btn pwa-btn-primary" onClick={installApp}>
            Install
          </button>
        </div>
      </div>
    );
  }

  return null;
}
