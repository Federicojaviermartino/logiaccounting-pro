import { usePWA } from '../hooks/usePWA';

export default function OfflineIndicator() {
  const { isOnline } = usePWA();

  if (isOnline) return null;

  return (
    <div className="offline-indicator">
      <span className="offline-icon">📡</span>
      <span>You are offline</span>
    </div>
  );
}
