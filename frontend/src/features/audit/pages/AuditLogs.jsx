/**
 * Audit Logs Page
 */
import { useState, useEffect } from 'react';
import { 
  Search, Filter, ChevronLeft, ChevronRight, Clock, 
  User, Activity, AlertTriangle, Eye, Download 
} from 'lucide-react';
import auditAPI from '../services/auditAPI';

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0 });
  
  const [filters, setFilters] = useState({
    search: '',
    action: '',
    severity: '',
    resourceType: '',
    startDate: '',
    endDate: ''
  });
  
  const [actions, setActions] = useState([]);
  const [resourceTypes, setResourceTypes] = useState([]);
  const [selectedLog, setSelectedLog] = useState(null);

  useEffect(() => {
    loadFilters();
    loadLogs();
  }, []);

  const loadFilters = async () => {
    try {
      const [actionsRes, typesRes] = await Promise.all([
        auditAPI.getActions(),
        auditAPI.getResourceTypes()
      ]);
      setActions(actionsRes.data);
      setResourceTypes(typesRes.data);
    } catch (err) {
      console.error('Failed to load filters:', err);
    }
  };

  const loadLogs = async (page = 1) => {
    try {
      setLoading(true);
      const response = await auditAPI.getLogs({
        page,
        pageSize: 50,
        ...filters
      });
      setLogs(response.data.items);
      setPagination({
        page: response.data.page,
        pages: response.data.pages,
        total: response.data.total
      });
    } catch (err) {
      console.error('Failed to load logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    loadLogs(1);
  };

  const getSeverityColor = (severity) => {
    const colors = {
      low: 'bg-gray-100 text-gray-700',
      medium: 'bg-yellow-100 text-yellow-700',
      high: 'bg-orange-100 text-orange-700',
      critical: 'bg-red-100 text-red-700'
    };
    return colors[severity] || colors.low;
  };

  const getActionIcon = (action) => {
    if (action.includes('login')) return <User size={14} />;
    if (action.includes('delete')) return <AlertTriangle size={14} />;
    return <Activity size={14} />;
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString();
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Audit Logs</h1>
          <p className="text-gray-500">Track all system activities and changes</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50">
          <Download size={16} />
          Export
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
              <input
                type="text"
                placeholder="Search logs..."
                value={filters.search}
                onChange={(e) => setFilters({...filters, search: e.target.value})}
                className="w-full pl-10 pr-4 py-2 border rounded-lg"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Action</label>
            <select
              value={filters.action}
              onChange={(e) => setFilters({...filters, action: e.target.value})}
              className="px-4 py-2 border rounded-lg"
            >
              <option value="">All Actions</option>
              {actions.map(action => (
                <option key={action} value={action}>{action}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
            <select
              value={filters.severity}
              onChange={(e) => setFilters({...filters, severity: e.target.value})}
              className="px-4 py-2 border rounded-lg"
            >
              <option value="">All Severities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Resource</label>
            <select
              value={filters.resourceType}
              onChange={(e) => setFilters({...filters, resourceType: e.target.value})}
              className="px-4 py-2 border rounded-lg"
            >
              <option value="">All Types</option>
              {resourceTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Filter size={16} />
          </button>
        </form>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Timestamp</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">User</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Action</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Resource</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Severity</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">IP Address</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-gray-700">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    Loading...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    No audit logs found
                  </td>
                </tr>
              ) : (
                logs.map(log => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm">
                      <div className="flex items-center gap-2">
                        <Clock size={14} className="text-gray-400" />
                        {formatDate(log.timestamp)}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <div>{log.user_name || 'System'}</div>
                      <div className="text-xs text-gray-500">{log.user_email}</div>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex items-center gap-2">
                        {getActionIcon(log.action)}
                        <span className="capitalize">{log.action}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <div>{log.resource_type}</div>
                      <div className="text-xs text-gray-500">{log.resource_name || log.resource_id}</div>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs ${getSeverityColor(log.severity)}`}>
                        {log.severity}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {log.ip_address || '-'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="p-1 hover:bg-gray-100 rounded"
                      >
                        <Eye size={16} className="text-gray-500" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-4 py-3 border-t flex justify-between items-center">
          <div className="text-sm text-gray-500">
            Showing {logs.length} of {pagination.total} entries
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => loadLogs(pagination.page - 1)}
              disabled={pagination.page <= 1}
              className="p-2 border rounded-lg disabled:opacity-50"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="px-4 py-2">
              Page {pagination.page} of {pagination.pages}
            </span>
            <button
              onClick={() => loadLogs(pagination.page + 1)}
              disabled={pagination.page >= pagination.pages}
              className="p-2 border rounded-lg disabled:opacity-50"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold">Audit Log Details</h3>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Timestamp</p>
                  <p className="font-medium">{formatDate(selectedLog.timestamp)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Action</p>
                  <p className="font-medium capitalize">{selectedLog.action}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">User</p>
                  <p className="font-medium">{selectedLog.user_email || 'System'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Severity</p>
                  <span className={`px-2 py-1 rounded-full text-xs ${getSeverityColor(selectedLog.severity)}`}>
                    {selectedLog.severity}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Resource Type</p>
                  <p className="font-medium">{selectedLog.resource_type}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Resource ID</p>
                  <p className="font-medium">{selectedLog.resource_id || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">IP Address</p>
                  <p className="font-medium">{selectedLog.ip_address || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Endpoint</p>
                  <p className="font-medium">{selectedLog.endpoint || '-'}</p>
                </div>
              </div>
              
              {selectedLog.description && (
                <div>
                  <p className="text-sm text-gray-500">Description</p>
                  <p className="mt-1">{selectedLog.description}</p>
                </div>
              )}
              
              {selectedLog.changed_fields && selectedLog.changed_fields.length > 0 && (
                <div>
                  <p className="text-sm text-gray-500">Changed Fields</p>
                  <div className="mt-1 flex flex-wrap gap-2">
                    {selectedLog.changed_fields.map(field => (
                      <span key={field} className="px-2 py-1 bg-gray-100 rounded text-sm">
                        {field}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="p-4 border-t flex justify-end">
              <button
                onClick={() => setSelectedLog(null)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
