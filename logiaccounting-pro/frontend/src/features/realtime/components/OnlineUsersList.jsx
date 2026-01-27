/**
 * Online Users List
 * Shows list of currently online users
 */

import { usePresence } from '../hooks/usePresence';
import UserAvatar from './UserAvatar';
import PresenceIndicator from './PresenceIndicator';

const OnlineUsersList = ({ maxDisplay = 5, compact = false }) => {
  const { onlineUsers, onlineCount } = usePresence();

  const displayUsers = onlineUsers.slice(0, maxDisplay);
  const remainingCount = Math.max(0, onlineCount - maxDisplay);

  if (compact) {
    return (
      <div className="flex items-center">
        <div className="flex -space-x-2">
          {displayUsers.map((user) => (
            <UserAvatar
              key={user.user_id}
              name={user.user_name}
              status={user.status}
              size="sm"
              className="ring-2 ring-white"
            />
          ))}
          {remainingCount > 0 && (
            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center
              justify-center text-xs font-medium text-gray-600 ring-2 ring-white">
              +{remainingCount}
            </div>
          )}
        </div>
        <span className="ml-2 text-sm text-gray-500">
          {onlineCount} online
        </span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 dark:bg-gray-800 dark:border-gray-700">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-900 dark:text-white">Team Online</h3>
        <span className="text-xs text-gray-500 dark:text-gray-400">{onlineCount} members</span>
      </div>

      <div className="space-y-2">
        {onlineUsers.map((user) => (
          <div
            key={user.user_id}
            className="flex items-center justify-between py-1"
          >
            <div className="flex items-center">
              <UserAvatar
                name={user.user_name}
                status={user.status}
                size="sm"
              />
              <div className="ml-2">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {user.user_name}
                </p>
                {user.current_page && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[150px]">
                    {user.current_page}
                  </p>
                )}
              </div>
            </div>
            <PresenceIndicator status={user.status} size="sm" />
          </div>
        ))}

        {onlineUsers.length === 0 && (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
            No one else online
          </p>
        )}
      </div>
    </div>
  );
};

export default OnlineUsersList;
