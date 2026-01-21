/**
 * Presence Indicator
 * Shows user online status dot
 */

const statusColors = {
  online: 'bg-green-500',
  away: 'bg-yellow-500',
  busy: 'bg-red-500',
  offline: 'bg-gray-400',
};

const PresenceIndicator = ({
  status = 'offline',
  size = 'sm',
  showPulse = true,
  className = '',
}) => {
  const sizeClasses = {
    xs: 'w-2 h-2',
    sm: 'w-2.5 h-2.5',
    md: 'w-3 h-3',
    lg: 'w-4 h-4',
  };

  const colorClass = statusColors[status] || statusColors.offline;
  const sizeClass = sizeClasses[size] || sizeClasses.sm;

  return (
    <span className={`relative inline-flex ${className}`}>
      <span className={`${sizeClass} ${colorClass} rounded-full`} />
      {showPulse && status === 'online' && (
        <span
          className={`absolute inset-0 ${sizeClass} ${colorClass} rounded-full animate-ping opacity-75`}
          style={{ animationDuration: '2s' }}
        />
      )}
    </span>
  );
};

export default PresenceIndicator;
