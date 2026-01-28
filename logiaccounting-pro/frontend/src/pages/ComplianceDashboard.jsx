/**
 * Compliance Dashboard - Phase 15
 * Enterprise Compliance Framework (SOX, GDPR, SOC 2, PCI-DSS)
 */

import { useState, useEffect } from 'react';
import { complianceAPI, soxAPI, gdprAPI, soc2API } from '../services/auditApi';
import toast from '../utils/toast';

export default function ComplianceDashboard() {
  const [frameworks, setFrameworks] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [summary, setSummary] = useState(null);
  const [selectedFramework, setSelectedFramework] = useState(null);
  const [frameworkDetails, setFrameworkDetails] = useState(null);
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [activeTab, setActiveTab] = useState('overview'); // overview, frameworks, violations

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const [frameworksRes, summaryRes, violationsRes] = await Promise.all([
        complianceAPI.getFrameworks(),
        complianceAPI.getSummary(),
        complianceAPI.getViolations({ limit: 50 })
      ]);

      setFrameworks(frameworksRes.data.frameworks || []);
      setSummary(summaryRes.data.summary || {});
      setViolations(violationsRes.data.violations || []);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadFrameworkDetails = async (frameworkId) => {
    setSelectedFramework(frameworkId);
    try {
      const res = await complianceAPI.getFrameworkStatus(frameworkId);
      setFrameworkDetails(res.data);
    } catch (err) {
      console.error('Failed to load framework details:', err);
      toast.error('Failed to load framework: ' + (err.response?.data?.detail || err.message));
    }
  };

  const runComplianceCheck = async (frameworkId) => {
    setRunning(true);
    try {
      const res = await complianceAPI.runCheck(frameworkId);
      setFrameworkDetails(res.data);
      toast.success(`Compliance check completed! Score: ${res.data.summary?.overall_score?.toFixed(1)}%`);
      // Refresh dashboard
      loadDashboard();
    } catch (err) {
      toast.error('Compliance check failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setRunning(false);
    }
  };

  const downloadReport = async (frameworkId, format) => {
    try {
      const res = await complianceAPI.generateReport(frameworkId, format, true);
      if (format === 'json') {
        console.log('Report:', res.data.report);
        toast.success('Report generated! Check console for details.');
      } else {
        const blob = res.data;
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `compliance_${frameworkId}.${format}`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      toast.error('Report generation failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const getStatusBadge = (status) => {
    const colors = {
      passed: 'badge-success',
      failed: 'badge-danger',
      warning: 'badge-warning',
      not_applicable: 'badge-gray',
      pending: 'badge-info',
      error: 'badge-danger',
      compliant: 'badge-success',
      non_compliant: 'badge-danger',
      partial: 'badge-warning'
    };
    return <span className={`badge ${colors[status] || 'badge-gray'}`}>{status?.replace('_', ' ')}</span>;
  };

  const getSeverityBadge = (severity) => {
    const colors = {
      low: 'badge-info',
      medium: 'badge-warning',
      high: 'badge-danger',
      critical: 'badge-danger'
    };
    return <span className={`badge ${colors[severity] || 'badge-gray'}`}>{severity}</span>;
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-success';
    if (score >= 60) return 'text-warning';
    return 'text-danger';
  };

  const frameworkInfo = {
    sox: { name: 'SOX', fullName: 'Sarbanes-Oxley Act', region: 'US', icon: '📊' },
    gdpr: { name: 'GDPR', fullName: 'General Data Protection Regulation', region: 'EU', icon: '🔒' },
    soc2: { name: 'SOC 2', fullName: 'SOC 2 Type II', region: 'Global', icon: '🛡️' },
    pci: { name: 'PCI-DSS', fullName: 'Payment Card Industry Data Security Standard', region: 'Global', icon: '💳' },
    hipaa: { name: 'HIPAA', fullName: 'Health Insurance Portability and Accountability Act', region: 'US', icon: '🏥' }
  };

  if (loading) {
    return <div className="text-center p-8">Loading compliance dashboard...</div>;
  }

  return (
    <>
      <div className="info-banner mb-6">
        Enterprise Compliance Framework - SOX, GDPR, SOC 2, PCI-DSS compliance monitoring (Phase 15)
      </div>

      {/* Tabs */}
      <div className="tabs mb-6">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${activeTab === 'frameworks' ? 'active' : ''}`}
          onClick={() => setActiveTab('frameworks')}
        >
          Frameworks
        </button>
        <button
          className={`tab ${activeTab === 'violations' ? 'active' : ''}`}
          onClick={() => setActiveTab('violations')}
        >
          Violations ({violations.length})
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <>
          {/* Summary Stats */}
          {summary && (
            <div className="stats-grid mb-6">
              <div className="stat-card">
                <div className="stat-icon">#</div>
                <div className="stat-content">
                  <div className="stat-value">{summary.total_frameworks || 0}</div>
                  <div className="stat-label">Frameworks</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">%</div>
                <div className="stat-content">
                  <div className={`stat-value ${getScoreColor(summary.overall_score || 0)}`}>
                    {(summary.overall_score || 0).toFixed(1)}%
                  </div>
                  <div className="stat-label">Overall Score</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon text-success">+</div>
                <div className="stat-content">
                  <div className="stat-value text-success">{summary.passed_controls || 0}</div>
                  <div className="stat-label">Passed Controls</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon text-danger">-</div>
                <div className="stat-content">
                  <div className="stat-value text-danger">{summary.failed_controls || 0}</div>
                  <div className="stat-label">Failed Controls</div>
                </div>
              </div>
            </div>
          )}

          {/* Framework Cards */}
          <div className="section">
            <h3 className="section-title">Compliance Frameworks</h3>
            <div className="grid-3 gap-4">
              {frameworks.map(fw => {
                const info = frameworkInfo[fw.id] || { name: fw.name, icon: '📋' };
                return (
                  <div
                    key={fw.id}
                    className="card p-4 cursor-pointer hover:shadow-lg"
                    onClick={() => {
                      loadFrameworkDetails(fw.id);
                      setActiveTab('frameworks');
                    }}
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <span className="text-2xl">{info.icon}</span>
                      <div>
                        <h4 className="font-bold">{info.name}</h4>
                        <div className="text-xs text-muted">{info.region}</div>
                      </div>
                    </div>
                    <p className="text-sm text-muted mb-3">{info.fullName}</p>
                    {fw.status && getStatusBadge(fw.status)}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Recent Violations */}
          {violations.length > 0 && (
            <div className="section mt-6">
              <h3 className="section-title">Recent Violations</h3>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Framework</th>
                      <th>Control</th>
                      <th>Severity</th>
                      <th>Status</th>
                      <th>Detected</th>
                    </tr>
                  </thead>
                  <tbody>
                    {violations.slice(0, 5).map(v => (
                      <tr key={v.id}>
                        <td>{v.framework_id?.toUpperCase()}</td>
                        <td>{v.control_id}</td>
                        <td>{getSeverityBadge(v.severity)}</td>
                        <td>{getStatusBadge(v.status)}</td>
                        <td>{new Date(v.detected_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <button
                className="btn btn-sm btn-secondary mt-2"
                onClick={() => setActiveTab('violations')}
              >
                View All Violations
              </button>
            </div>
          )}
        </>
      )}

      {/* Frameworks Tab */}
      {activeTab === 'frameworks' && (
        <div className="section">
          <div className="flex gap-4 mb-4">
            {frameworks.map(fw => (
              <button
                key={fw.id}
                className={`btn ${selectedFramework === fw.id ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => loadFrameworkDetails(fw.id)}
              >
                {frameworkInfo[fw.id]?.icon} {frameworkInfo[fw.id]?.name || fw.name}
              </button>
            ))}
          </div>

          {frameworkDetails && (
            <div className="card p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-bold">
                    {frameworkInfo[selectedFramework]?.icon} {frameworkInfo[selectedFramework]?.fullName || selectedFramework}
                  </h3>
                  <p className="text-muted">Region: {frameworkInfo[selectedFramework]?.region}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    className="btn btn-primary"
                    onClick={() => runComplianceCheck(selectedFramework)}
                    disabled={running}
                  >
                    {running ? 'Running...' : 'Run Check'}
                  </button>
                  <button
                    className="btn btn-secondary"
                    onClick={() => downloadReport(selectedFramework, 'pdf')}
                  >
                    PDF Report
                  </button>
                  <button
                    className="btn btn-secondary"
                    onClick={() => downloadReport(selectedFramework, 'excel')}
                  >
                    Excel Report
                  </button>
                </div>
              </div>

              {/* Summary */}
              {frameworkDetails.summary && (
                <div className="grid-4 gap-4 mb-6">
                  <div className="card p-3 text-center">
                    <div className={`text-2xl font-bold ${getScoreColor(frameworkDetails.summary.overall_score)}`}>
                      {frameworkDetails.summary.overall_score?.toFixed(1)}%
                    </div>
                    <div className="text-sm text-muted">Overall Score</div>
                  </div>
                  <div className="card p-3 text-center">
                    <div className="text-2xl font-bold text-success">{frameworkDetails.summary.passed}</div>
                    <div className="text-sm text-muted">Passed</div>
                  </div>
                  <div className="card p-3 text-center">
                    <div className="text-2xl font-bold text-danger">{frameworkDetails.summary.failed}</div>
                    <div className="text-sm text-muted">Failed</div>
                  </div>
                  <div className="card p-3 text-center">
                    <div className="text-2xl font-bold text-warning">{frameworkDetails.summary.warnings}</div>
                    <div className="text-sm text-muted">Warnings</div>
                  </div>
                </div>
              )}

              {/* Controls */}
              <h4 className="font-bold mb-3">Controls ({frameworkDetails.controls?.length || 0})</h4>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Control ID</th>
                      <th>Name</th>
                      <th>Status</th>
                      <th>Score</th>
                      <th>Findings</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(frameworkDetails.controls || []).map(control => (
                      <tr key={control.control_id}>
                        <td><code>{control.control_id}</code></td>
                        <td>{control.control_name}</td>
                        <td>{getStatusBadge(control.status)}</td>
                        <td>
                          <span className={getScoreColor(control.score)}>
                            {control.score?.toFixed(0)}%
                          </span>
                        </td>
                        <td>
                          {control.findings?.length > 0 ? (
                            <details>
                              <summary className="cursor-pointer text-link">
                                {control.findings.length} finding(s)
                              </summary>
                              <ul className="mt-2 text-sm">
                                {control.findings.map((f, i) => (
                                  <li key={i} className="text-muted">{f}</li>
                                ))}
                              </ul>
                            </details>
                          ) : (
                            <span className="text-success">None</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {!frameworkDetails && (
            <div className="card p-8 text-center text-muted">
              Select a framework above to view details and run compliance checks.
            </div>
          )}
        </div>
      )}

      {/* Violations Tab */}
      {activeTab === 'violations' && (
        <div className="section">
          <h3 className="section-title">Compliance Violations</h3>

          {violations.length === 0 ? (
            <div className="card p-8 text-center text-muted">
              No compliance violations detected. Great job!
            </div>
          ) : (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Framework</th>
                    <th>Control ID</th>
                    <th>Severity</th>
                    <th>Description</th>
                    <th>Status</th>
                    <th>Detected</th>
                  </tr>
                </thead>
                <tbody>
                  {violations.map(v => (
                    <tr key={v.id}>
                      <td>
                        <span className="badge badge-info">{v.framework_id?.toUpperCase()}</span>
                      </td>
                      <td><code>{v.control_id}</code></td>
                      <td>{getSeverityBadge(v.severity)}</td>
                      <td className="text-sm">{v.description || '-'}</td>
                      <td>{getStatusBadge(v.status)}</td>
                      <td>{new Date(v.detected_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </>
  );
}
