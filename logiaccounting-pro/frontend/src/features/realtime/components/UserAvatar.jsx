/**
 * User Avatar with Presence
 */

import PresenceIndicator from './PresenceIndicator';

const UserAvatar = ({
  name,
  imageUrl,
  status = 'offline',
  size = 'md',
  showPresence = true,
  className = '',
}) => {
  const sizeClasses = {
    xs: 'w-6 h-6 text-xs',
    sm: 'w-8 h-8 text-sm',
    md: 'w-10 h-10 text-base',
    lg: 'w-12 h-12 text-lg',
    xl: 'w-16 h-16 text-xl',
  };

  const presenceSizes = {
    xs: 'xs',
    sm: 'xs',
    md: 'sm',
    lg: 'md',
    xl: 'lg',
  };

  const presencePositions = {
    xs: 'bottom-0 right-0',
    sm: 'bottom-0 right-0',
    md: '-bottom-0.5 -right-0.5',
    lg: '-bottom-0.5 -right-0.5',
    xl: 'bottom-0 right-0',
  };

  const getInitials = (name) => {
    if (!name) return '?';
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const sizeClass = sizeClasses[size] || sizeClasses.md;

  return (
    <div className={`relative inline-flex ${className}`}>
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={name}
          className={`${sizeClass} rounded-full object-cover`}
        />
      ) : (
        <div
          className={`${sizeClass} rounded-full bg-blue-500 text-white
            flex items-center justify-center font-medium`}
        >
          {getInitials(name)}
        </div>
      )}

      {showPresence && (
        <span className={`absolute ${presencePositions[size]} ring-2 ring-white rounded-full`}>
          <PresenceIndicator status={status} size={presenceSizes[size]} />
        </span>
      )}
    </div>
  );
};

export default UserAvatar;
