/**
 * Editing Indicator
 * Shows who is currently viewing/editing a document
 */

import { useRoom } from '../hooks/useRoom';
import UserAvatar from './UserAvatar';
import { useAuth } from '../../../contexts/AuthContext';

const EditingIndicator = ({ entityType, entityId }) => {
  const { user } = useAuth();
  const { roomUsers, userCount } = useRoom(entityType, entityId);

  const otherUsers = roomUsers.filter(u => u.user_id !== user?.id);

  if (otherUsers.length === 0) {
    return null;
  }

  return (
    <div className="flex items-center bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800
      rounded-lg px-3 py-2 text-sm">
      <div className="flex -space-x-2 mr-2">
        {otherUsers.slice(0, 3).map((u) => (
          <UserAvatar
            key={u.user_id}
            name={u.user_name}
            status="online"
            size="xs"
            showPresence={false}
            className="ring-2 ring-white dark:ring-gray-800"
          />
        ))}
      </div>

      <span className="text-yellow-800 dark:text-yellow-200">
        {otherUsers.length === 1 ? (
          <>{otherUsers[0].user_name} is viewing</>
        ) : otherUsers.length === 2 ? (
          <>{otherUsers[0].user_name} and {otherUsers[1].user_name} are viewing</>
        ) : (
          <>{otherUsers[0].user_name} and {otherUsers.length - 1} others are viewing</>
        )}
      </span>
    </div>
  );
};

export default EditingIndicator;
