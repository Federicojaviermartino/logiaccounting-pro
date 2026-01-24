/**
 * PWA Install Prompt - Handles app installation
 */

import React, { useState, useEffect } from 'react';
import { Download, X, Smartphone } from 'lucide-react';

let deferredPrompt = null;

// Capture the install prompt event globally
if (typeof window !== 'undefined') {
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    window.dispatchEvent(new CustomEvent('pwainstallready'));
  });
}

export default function InstallPrompt({ onDismiss }) {
  const [showPrompt, setShowPrompt] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);
  const [isIOS, setIsIOS] = useState(false);

  useEffect(() => {
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setIsInstalled(true);
      return;
    }

    // Check if iOS
    const isIOSDevice = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    setIsIOS(isIOSDevice);

    // Check if prompt is available
    if (deferredPrompt) {
      setShowPrompt(true);
    }

    // Listen for install ready event
    const handleInstallReady = () => {
      setShowPrompt(true);
    };

    window.addEventListener('pwainstallready', handleInstallReady);

    // Listen for app installed event
    window.addEventListener('appinstalled', () => {
      setIsInstalled(true);
      setShowPrompt(false);
      deferredPrompt = null;
    });

    return () => {
      window.removeEventListener('pwainstallready', handleInstallReady);
    };
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === 'accepted') {
      console.log('[PWA] User accepted install');
    }

    deferredPrompt = null;
    setShowPrompt(false);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('pwa_prompt_dismissed', Date.now().toString());
    if (onDismiss) onDismiss();
  };

  if (isInstalled) return null;

  const dismissedAt = localStorage.getItem('pwa_prompt_dismissed');
  if (dismissedAt && Date.now() - parseInt(dismissedAt) < 7 * 24 * 60 * 60 * 1000) {
    return null;
  }

  if (!showPrompt && !isIOS) return null;

  return (
    <div className="install-prompt">
      <div className="prompt-content">
        <div className="prompt-icon">
          <Smartphone className="w-8 h-8" />
        </div>

        <div className="prompt-text">
          <h3>Install LogiAccounting</h3>
          <p>
            {isIOS
              ? 'Tap the share button and "Add to Home Screen"'
              : 'Install our app for a better experience'}
          </p>
        </div>

        <div className="prompt-actions">
          {!isIOS && (
            <button className="install-btn" onClick={handleInstall}>
              <Download className="w-4 h-4" />
              Install
            </button>
          )}
          <button className="dismiss-btn" onClick={handleDismiss}>
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      <style jsx>{`
        .install-prompt {
          position: fixed;
          bottom: calc(90px + env(safe-area-inset-bottom));
          left: 16px;
          right: 16px;
          z-index: 200;
          animation: slideUp 0.3s ease-out;
        }

        @keyframes slideUp {
          from { transform: translateY(100%); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }

        .prompt-content {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 16px;
          background: var(--bg-primary);
          border: 1px solid var(--border-color);
          border-radius: 16px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
        }

        .prompt-icon {
          width: 48px;
          height: 48px;
          background: linear-gradient(135deg, var(--primary), var(--primary-dark));
          color: white;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .prompt-text { flex: 1; }
        .prompt-text h3 { font-size: 15px; font-weight: 600; margin: 0 0 4px; }
        .prompt-text p { font-size: 13px; color: var(--text-muted); margin: 0; }

        .prompt-actions { display: flex; align-items: center; gap: 8px; }

        .install-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 10px 16px;
          background: var(--primary);
          color: white;
          border-radius: 10px;
          font-size: 14px;
          font-weight: 500;
        }

        .dismiss-btn {
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--text-muted);
          border-radius: 8px;
        }
      `}</style>
    </div>
  );
}
