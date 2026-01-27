/**
 * InstallBanner - PWA install prompt UI
 */

import React from 'react';
import { Download, X, Smartphone } from 'lucide-react';
import { useInstallPrompt } from '../useInstallPrompt';

export default function InstallBanner() {
  const {
    isInstallable,
    shouldShowPrompt,
    promptInstall,
    dismissPrompt
  } = useInstallPrompt();

  if (!isInstallable || !shouldShowPrompt) return null;

  const handleInstall = async () => {
    const result = await promptInstall();
    if (result?.outcome === 'accepted') {
      // Track install
      if (window.gtag) {
        window.gtag('event', 'pwa_install', { method: 'banner' });
      }
    }
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-gradient-to-r
                    from-blue-600 to-purple-600 text-white shadow-lg
                    animate-slide-up md:bottom-4 md:left-4 md:right-auto
                    md:max-w-sm md:rounded-lg">
      <button
        onClick={dismissPrompt}
        className="absolute top-2 right-2 p-1 hover:bg-white/20 rounded-full"
        aria-label="Dismiss"
      >
        <X className="w-5 h-5" />
      </button>

      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 p-3 bg-white/20 rounded-xl">
          <Smartphone className="w-8 h-8" />
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-lg">Install LogiAccounting</h3>
          <p className="text-sm text-white/80 mt-1">
            Add to your home screen for quick access and offline support.
          </p>

          <div className="flex gap-2 mt-3">
            <button
              onClick={handleInstall}
              className="flex items-center gap-2 px-4 py-2 bg-white text-blue-600
                         rounded-lg font-medium hover:bg-blue-50 transition-colors"
            >
              <Download className="w-4 h-4" />
              Install
            </button>
            <button
              onClick={dismissPrompt}
              className="px-4 py-2 text-white/80 hover:text-white transition-colors"
            >
              Not now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
