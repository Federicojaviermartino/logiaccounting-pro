/**
 * Connection Status
 * Shows WebSocket connection status
 */

import { useRealtime } from '../context/RealtimeContext';

const ConnectionStatus = ({ showLabel = true }) => {
  const { isConnected, connectionError } = useRealtime();

  if (connectionError) {
    return (
      <div className="flex items-center text-red-500">
        <span className="w-2 h-2 bg-red-500 rounded-full mr-2" />
        {showLabel && <span className="text-xs">Connection Error</span>}
      </div>
    );
  }

  if (isConnected) {
    return (
      <div className="flex items-center text-green-500">
        <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse" />
        {showLabel && <span className="text-xs">Connected</span>}
      </div>
    );
  }

  return (
    <div className="flex items-center text-yellow-500">
      <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2" />
      {showLabel && <span className="text-xs">Connecting...</span>}
    </div>
  );
};

export default ConnectionStatus;
