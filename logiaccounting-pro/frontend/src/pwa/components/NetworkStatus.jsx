/**
 * NetworkStatus - Offline/Online indicator
 */

import React, { useState, useEffect } from 'react';
import { Wifi, WifiOff, RefreshCw, Cloud, CloudOff } from 'lucide-react';
import { useSync } from '../hooks/useSync';

export default function NetworkStatus() {
  const { isOnline, isSyncing, pendingCount, syncNow } = useSync();
  const [showBanner, setShowBanner] = useState(false);
  const [wasOffline, setWasOffline] = useState(false);

  useEffect(() => {
    if (!isOnline) {
      setShowBanner(true);
      setWasOffline(true);
    } else if (wasOffline) {
      // Just came back online
      setShowBanner(true);
      setTimeout(() => setShowBanner(false), 3000);
      setWasOffline(false);
    }
  }, [isOnline, wasOffline]);

  if (!showBanner && pendingCount === 0) return null;

  return (
    <>
      {/* Floating indicator */}
      {pendingCount > 0 && (
        <div className="fixed bottom-20 right-4 z-40">
          <button
            onClick={syncNow}
            disabled={!isOnline || isSyncing}
            className={`flex items-center gap-2 px-4 py-2 rounded-full shadow-lg
                       transition-all ${isOnline
                         ? 'bg-blue-600 text-white hover:bg-blue-700'
                         : 'bg-gray-500 text-white cursor-not-allowed'}`}
          >
            {isSyncing ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : isOnline ? (
              <Cloud className="w-4 h-4" />
            ) : (
              <CloudOff className="w-4 h-4" />
            )}
            <span className="text-sm font-medium">
              {pendingCount} pending
            </span>
          </button>
        </div>
      )}

      {/* Offline banner */}
      {showBanner && (
        <div
          className={`fixed top-0 left-0 right-0 z-50 px-4 py-2 text-center text-sm
                     transition-all duration-300 ${isOnline
                       ? 'bg-green-500 text-white'
                       : 'bg-yellow-500 text-yellow-900'}`}
        >
          <div className="flex items-center justify-center gap-2">
            {isOnline ? (
              <>
                <Wifi className="w-4 h-4" />
                <span>Back online</span>
                {pendingCount > 0 && (
                  <span>- Syncing {pendingCount} changes...</span>
                )}
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4" />
                <span>You're offline. Changes will sync when connected.</span>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
