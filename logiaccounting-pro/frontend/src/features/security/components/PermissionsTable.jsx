import { useState, useEffect } from 'react';
import { Check, X, Minus, RefreshCw, AlertCircle, Search, ChevronDown, ChevronRight } from 'lucide-react';
import { securityAPI } from '../services/securityAPI';

export default function PermissionsTable({ roleId, editable = false, onPermissionChange }) {
  const [permissions, setPermissions] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedCategories, setExpandedCategories] = useState({});
  const [selectedRole, setSelectedRole] = useState(roleId || null);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (roleId) {
      setSelectedRole(roleId);
    }
  }, [roleId]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      const [permissionsRes, rolesRes] = await Promise.all([
        securityAPI.rbac.getPermissions(),
        securityAPI.rbac.getRoles()
      ]);
      setPermissions(permissionsRes.data.permissions || []);
      setRoles(rolesRes.data.roles || []);

      const categories = {};
      (permissionsRes.data.permissions || []).forEach((p) => {
        const category = p.category || 'General';
        categories[category] = true;
      });
      setExpandedCategories(categories);
    } catch (err) {
      setError('Failed to load permissions');
      console.error('Failed to load permissions:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleCategory = (category) => {
    setExpandedCategories((prev) => ({
      ...prev,
      [category]: !prev[category]
    }));
  };

  const getPermissionsByCategory = () => {
    const filtered = permissions.filter((p) =>
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.description?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const grouped = {};
    filtered.forEach((permission) => {
      const category = permission.category || 'General';
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push(permission);
    });
    return grouped;
  };

  const hasPermission = (role, permissionCode) => {
    if (!role.permissions) return false;
    return role.permissions.includes(permissionCode) || role.permissions.includes('*');
  };

  const handlePermissionToggle = async (role, permissionCode, currentValue) => {
    if (!editable || !onPermissionChange) return;

    try {
      await onPermissionChange(role.id, permissionCode, !currentValue);
      setRoles((prev) =>
        prev.map((r) => {
          if (r.id === role.id) {
            const newPermissions = currentValue
              ? r.permissions.filter((p) => p !== permissionCode)
              : [...r.permissions, permissionCode];
            return { ...r, permissions: newPermissions };
          }
          return r;
        })
      );
    } catch (err) {
      console.error('Failed to update permission:', err);
    }
  };

  const renderPermissionCell = (role, permissionCode) => {
    const hasIt = hasPermission(role, permissionCode);
    const isWildcard = role.permissions?.includes('*');

    if (isWildcard) {
      return (
        <div className="flex justify-center">
          <span className="px-2 py-0.5 text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded">
            All
          </span>
        </div>
      );
    }

    if (editable && selectedRole === role.id) {
      return (
        <button
          onClick={() => handlePermissionToggle(role, permissionCode, hasIt)}
          className={`w-8 h-8 rounded flex items-center justify-center transition-colors ${
            hasIt
              ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 hover:bg-green-200'
              : 'bg-gray-100 dark:bg-gray-700 text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
          }`}
        >
          {hasIt ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
        </button>
      );
    }

    return (
      <div className="flex justify-center">
        {hasIt ? (
          <Check className="w-5 h-5 text-green-500" />
        ) : (
          <Minus className="w-5 h-5 text-gray-300 dark:text-gray-600" />
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600 dark:text-gray-400">Loading permissions...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2 text-red-700 dark:text-red-400">
        <AlertCircle className="w-5 h-5" />
        <span>{error}</span>
        <button
          onClick={loadData}
          className="ml-auto px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  const groupedPermissions = getPermissionsByCategory();
  const displayRoles = selectedRole
    ? roles.filter((r) => r.id === selectedRole)
    : roles;

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-4 items-center">
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search permissions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>
        </div>
        {!roleId && (
          <select
            value={selectedRole || ''}
            onChange={(e) => setSelectedRole(e.target.value || null)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
          >
            <option value="">All Roles</option>
            {roles.map((role) => (
              <option key={role.id} value={role.id}>{role.name}</option>
            ))}
          </select>
        )}
      </div>

      <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider min-w-[250px]">
                  Permission
                </th>
                {displayRoles.map((role) => (
                  <th
                    key={role.id}
                    className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider min-w-[100px]"
                  >
                    <div className="flex flex-col items-center">
                      <span>{role.name}</span>
                      {role.user_count !== undefined && (
                        <span className="text-xs font-normal text-gray-400">
                          {role.user_count} user{role.user_count !== 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {Object.entries(groupedPermissions).map(([category, categoryPermissions]) => (
                <CategoryGroup
                  key={category}
                  category={category}
                  permissions={categoryPermissions}
                  roles={displayRoles}
                  expanded={expandedCategories[category]}
                  onToggle={() => toggleCategory(category)}
                  renderPermissionCell={renderPermissionCell}
                />
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {Object.keys(groupedPermissions).length === 0 && (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          No permissions found matching your search
        </div>
      )}

      <div className="mt-4 flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
        <div className="flex items-center gap-1">
          <Check className="w-4 h-4 text-green-500" />
          <span>Granted</span>
        </div>
        <div className="flex items-center gap-1">
          <Minus className="w-4 h-4 text-gray-300" />
          <span>Not granted</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="px-2 py-0.5 text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded">
            All
          </span>
          <span>Full access</span>
        </div>
      </div>
    </div>
  );
}

function CategoryGroup({ category, permissions, roles, expanded, onToggle, renderPermissionCell }) {
  return (
    <>
      <tr
        className="bg-gray-100 dark:bg-gray-800 cursor-pointer hover:bg-gray-150 dark:hover:bg-gray-750"
        onClick={onToggle}
      >
        <td colSpan={roles.length + 1} className="px-4 py-2">
          <div className="flex items-center gap-2 font-medium text-gray-700 dark:text-gray-300">
            {expanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
            {category}
            <span className="text-xs font-normal text-gray-500">
              ({permissions.length} permission{permissions.length !== 1 ? 's' : ''})
            </span>
          </div>
        </td>
      </tr>
      {expanded &&
        permissions.map((permission) => (
          <tr key={permission.code} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
            <td className="px-4 py-3">
              <div className="pl-6">
                <p className="font-medium text-gray-900 dark:text-white text-sm">
                  {permission.name}
                </p>
                {permission.description && (
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {permission.description}
                  </p>
                )}
                <code className="text-xs text-gray-400 dark:text-gray-500">
                  {permission.code}
                </code>
              </div>
            </td>
            {roles.map((role) => (
              <td key={role.id} className="px-4 py-3">
                {renderPermissionCell(role, permission.code)}
              </td>
            ))}
          </tr>
        ))}
    </>
  );
}
