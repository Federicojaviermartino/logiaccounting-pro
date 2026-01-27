/**
 * useInstallPrompt - Hook for PWA install prompt
 */

import { useState, useEffect, useCallback } from 'react';

export function useInstallPrompt() {
  const [installPrompt, setInstallPrompt] = useState(null);
  const [isInstalled, setIsInstalled] = useState(false);
  const [isInstallable, setIsInstallable] = useState(false);
  const [installOutcome, setInstallOutcome] = useState(null);

  useEffect(() => {
    // Check if already installed
    const checkInstalled = () => {
      if (window.matchMedia('(display-mode: standalone)').matches) {
        setIsInstalled(true);
        return true;
      }
      if (window.navigator.standalone === true) {
        setIsInstalled(true);
        return true;
      }
      return false;
    };

    if (checkInstalled()) return;

    // Listen for beforeinstallprompt
    const handleBeforeInstall = (event) => {
      event.preventDefault();
      setInstallPrompt(event);
      setIsInstallable(true);
    };

    // Listen for appinstalled
    const handleAppInstalled = () => {
      setIsInstalled(true);
      setIsInstallable(false);
      setInstallPrompt(null);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstall);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const promptInstall = useCallback(async () => {
    if (!installPrompt) {
      console.log('No install prompt available');
      return null;
    }

    try {
      installPrompt.prompt();
      const result = await installPrompt.userChoice;
      setInstallOutcome(result.outcome);

      if (result.outcome === 'accepted') {
        setIsInstallable(false);
        setInstallPrompt(null);
      }

      return result;
    } catch (error) {
      console.error('Install prompt error:', error);
      return null;
    }
  }, [installPrompt]);

  const dismissPrompt = useCallback(() => {
    setIsInstallable(false);
    // Store dismissal in localStorage
    localStorage.setItem('pwa-install-dismissed', Date.now().toString());
  }, []);

  const shouldShowPrompt = useCallback(() => {
    if (isInstalled || !isInstallable) return false;

    const dismissed = localStorage.getItem('pwa-install-dismissed');
    if (dismissed) {
      const dismissedTime = parseInt(dismissed, 10);
      const daysSinceDismissed = (Date.now() - dismissedTime) / (1000 * 60 * 60 * 24);
      // Don't show again for 7 days after dismissal
      if (daysSinceDismissed < 7) return false;
    }

    return true;
  }, [isInstalled, isInstallable]);

  return {
    isInstallable,
    isInstalled,
    installOutcome,
    promptInstall,
    dismissPrompt,
    shouldShowPrompt: shouldShowPrompt(),
  };
}

export default useInstallPrompt;
