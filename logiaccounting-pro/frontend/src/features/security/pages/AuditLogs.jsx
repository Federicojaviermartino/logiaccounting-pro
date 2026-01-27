import { useState, useEffect, useCallback } from 'react';
import {
  Search,
  Filter,
  Download,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Calendar,
  User,
  Activity,
  FileText,
  AlertCircle,
  CheckCircle,
  XCircle,
  Eye
} from 'lucide-react';
import { securityAPI } from '../services/securityAPI';

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 25,
    total: 0,
    total_pages: 0
  });
  const [filters, setFilters] = useState({
    search: '',
    action: '',
    entity_type: '',
    user_id: '',
    date_from: '',
    date_to: '',
    status: ''
  });
  const [showFilters, setShowFilters] = useState(false);
  const [filterOptions, setFilterOptions] = useState({
    actions: [],
    entities: [],
    users: []
  });
  const [selectedLog, setSelectedLog] = useState(null);

  const loadLogs = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v !== '')
        )
      };
      const response = await securityAPI.audit.search(params);
      setLogs(response.data.logs || []);
      setPagination((prev) => ({
        ...prev,
        total: response.data.total || 0,
        total_pages: response.data.total_pages || 0
      }));
    } catch (error) {
      console.error('Failed to load audit logs:', error);
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.per_page, filters]);

  const loadFilterOptions = async () => {
    try {
      const [actionsRes, entitiesRes] = await Promise.all([
        securityAPI.audit.getActions(),
        securityAPI.audit.getEntities()
      ]);
      setFilterOptions({
        actions: actionsRes.data || [],
        entities: entitiesRes.data || [],
        users: []
      });
    } catch (error) {
      console.error('Failed to load filter options:', error);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  useEffect(() => {
    loadFilterOptions();
  }, []);

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const clearFilters = () => {
    setFilters({
      search: '',
      action: '',
      entity_type: '',
      user_id: '',
      date_from: '',
      date_to: '',
      status: ''
    });
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const handleExport = async (format) => {
    try {
      setExporting(true);
      const response = await securityAPI.audit.export(
        format,
        filters.date_from,
        filters.date_to
      );

      const blob = new Blob([response.data], {
        type: format === 'csv' ? 'text/csv' : 'application/json'
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `audit-logs-${new Date().toISOString().split('T')[0]}.${format}`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export audit logs:', error);
    } finally {
      setExporting(false);
    }
  };

  const getActionIcon = (action) => {
    const actionLower = action.toLowerCase();
    if (actionLower.includes('create')) return <CheckCircle className="w-4 h-4 text-green-500" />;
    if (actionLower.includes('delete')) return <XCircle className="w-4 h-4 text-red-500" />;
    if (actionLower.includes('update')) return <Activity className="w-4 h-4 text-blue-500" />;
    if (actionLower.includes('login')) return <User className="w-4 h-4 text-purple-500" />;
    return <FileText className="w-4 h-4 text-gray-500" />;
  };

  const getStatusBadge = (status) => {
    const statusClasses = {
      success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      failure: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
      warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
    };
    return (
      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusClasses[status] || statusClasses.success}`}>
        {status || 'success'}
      </span>
    );
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Audit Logs</h1>
          <p className="text-gray-600 dark:text-gray-400">View and export system activity logs</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => loadLogs()}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <div className="relative">
            <button
              onClick={() => handleExport('csv')}
              disabled={exporting}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search logs..."
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-4 py-2 border rounded-lg ${
                showFilters
                  ? 'border-blue-500 text-blue-600 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
            >
              <Filter className="w-4 h-4" />
              Filters
            </button>
          </div>

          {showFilters && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Action
                  </label>
                  <select
                    value={filters.action}
                    onChange={(e) => handleFilterChange('action', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">All Actions</option>
                    {filterOptions.actions.map((action) => (
                      <option key={action} value={action}>{action}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Entity Type
                  </label>
                  <select
                    value={filters.entity_type}
                    onChange={(e) => handleFilterChange('entity_type', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">All Entities</option>
                    {filterOptions.entities.map((entity) => (
                      <option key={entity} value={entity}>{entity}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Status
                  </label>
                  <select
                    value={filters.status}
                    onChange={(e) => handleFilterChange('status', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">All Statuses</option>
                    <option value="success">Success</option>
                    <option value="failure">Failure</option>
                    <option value="warning">Warning</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Date From
                  </label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type="date"
                      value={filters.date_from}
                      onChange={(e) => handleFilterChange('date_from', e.target.value)}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Date To
                  </label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type="date"
                      value={filters.date_to}
                      onChange={(e) => handleFilterChange('date_to', e.target.value)}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                    />
                  </div>
                </div>
                <div className="flex items-end">
                  <button
                    onClick={clearFilters}
                    className="w-full px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    Clear Filters
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  User
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Action
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Entity
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  IP Address
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center">
                    <div className="flex justify-center items-center gap-2 text-gray-500">
                      <RefreshCw className="w-5 h-5 animate-spin" />
                      Loading logs...
                    </div>
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                    <AlertCircle className="w-8 h-8 mx-auto mb-2" />
                    No audit logs found
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-white whitespace-nowrap">
                      {formatTimestamp(log.timestamp)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-gray-200 dark:bg-gray-600 rounded-full flex items-center justify-center">
                          <User className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                        </div>
                        <span>{log.user_email || log.user_id || 'System'}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex items-center gap-2">
                        {getActionIcon(log.action)}
                        <span className="text-gray-900 dark:text-white">{log.action}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      {log.entity_type}
                      {log.entity_id && (
                        <span className="text-xs text-gray-400 ml-1">#{log.entity_id}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {getStatusBadge(log.status)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 font-mono">
                      {log.ip_address || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                        title="View details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Showing {logs.length} of {pagination.total} logs
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPagination((prev) => ({ ...prev, page: prev.page - 1 }))}
              disabled={pagination.page <= 1}
              className="p-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Page {pagination.page} of {pagination.total_pages || 1}
            </span>
            <button
              onClick={() => setPagination((prev) => ({ ...prev, page: prev.page + 1 }))}
              disabled={pagination.page >= pagination.total_pages}
              className="p-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {selectedLog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Audit Log Details</h3>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-500 dark:text-gray-400 uppercase">Timestamp</label>
                  <p className="text-gray-900 dark:text-white">{formatTimestamp(selectedLog.timestamp)}</p>
                </div>
                <div>
                  <label className="text-xs text-gray-500 dark:text-gray-400 uppercase">Status</label>
                  <p>{getStatusBadge(selectedLog.status)}</p>
                </div>
                <div>
                  <label className="text-xs text-gray-500 dark:text-gray-400 uppercase">User</label>
                  <p className="text-gray-900 dark:text-white">{selectedLog.user_email || selectedLog.user_id || 'System'}</p>
                </div>
                <div>
                  <label className="text-xs text-gray-500 dark:text-gray-400 uppercase">IP Address</label>
                  <p className="text-gray-900 dark:text-white font-mono">{selectedLog.ip_address || '-'}</p>
                </div>
                <div>
                  <label className="text-xs text-gray-500 dark:text-gray-400 uppercase">Action</label>
                  <p className="text-gray-900 dark:text-white">{selectedLog.action}</p>
                </div>
                <div>
                  <label className="text-xs text-gray-500 dark:text-gray-400 uppercase">Entity</label>
                  <p className="text-gray-900 dark:text-white">
                    {selectedLog.entity_type}
                    {selectedLog.entity_id && ` #${selectedLog.entity_id}`}
                  </p>
                </div>
              </div>
              {selectedLog.details && (
                <div>
                  <label className="text-xs text-gray-500 dark:text-gray-400 uppercase">Details</label>
                  <pre className="mt-1 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-sm text-gray-900 dark:text-white overflow-x-auto">
                    {JSON.stringify(selectedLog.details, null, 2)}
                  </pre>
                </div>
              )}
              {selectedLog.user_agent && (
                <div>
                  <label className="text-xs text-gray-500 dark:text-gray-400 uppercase">User Agent</label>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{selectedLog.user_agent}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
