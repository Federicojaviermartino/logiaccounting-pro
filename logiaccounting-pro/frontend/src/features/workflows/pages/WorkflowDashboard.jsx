import React, { useState, useEffect } from 'react';
import { Zap, Play, CheckCircle, XCircle, Clock, TrendingUp, Activity, Settings } from 'lucide-react';
import { Link } from 'react-router-dom';
import { workflowAPI } from '../../../services/api';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

export default function WorkflowDashboard() {
  const [stats, setStats] = useState(null);
  const [activeExecutions, setActiveExecutions] = useState([]);
  const [recentExecutions, setRecentExecutions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [period, setPeriod] = useState(7);

  useEffect(() => { loadData(); }, [period]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [statsRes, activeRes, recentRes] = await Promise.all([
        workflowAPI.getDashboardStats({ days: period }),
        workflowAPI.getActiveExecutions(),
        workflowAPI.listExecutions({ limit: 10 }),
      ]);
      setStats(statsRes.data);
      setActiveExecutions(activeRes.data || []);
      setRecentExecutions(recentRes.data || []);
    } catch (error) {
      console.error('Failed to load:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const statusChartData = {
    labels: ['Successful', 'Failed'],
    datasets: [{
      data: [stats?.successful_executions || 0, stats?.failed_executions || 0],
      backgroundColor: ['#10b981', '#ef4444'],
      borderWidth: 0,
    }],
  };

  if (isLoading) return <div className="p-6">Loading...</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Workflow Dashboard</h1>
          <p className="text-gray-500">Automation overview and analytics</p>
        </div>
        <div className="flex gap-2">
          <select value={period} onChange={(e) => setPeriod(Number(e.target.value))} className="px-3 py-2 border rounded-lg">
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <Link to="/workflows/builder" className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg">
            <Zap className="w-4 h-4" /> New Workflow
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white border rounded-xl p-5">
          <div className="flex items-center justify-between">
            <Zap className="w-8 h-8 text-blue-500" />
            <span className="text-xs text-gray-400">{period}d</span>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold">{stats?.active_workflows || 0}</div>
            <div className="text-sm text-gray-500">Active Workflows</div>
          </div>
        </div>
        <div className="bg-white border rounded-xl p-5">
          <div className="flex items-center justify-between">
            <Play className="w-8 h-8 text-green-500" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold">{stats?.total_executions || 0}</div>
            <div className="text-sm text-gray-500">Total Executions</div>
          </div>
        </div>
        <div className="bg-white border rounded-xl p-5">
          <div className="flex items-center justify-between">
            <CheckCircle className="w-8 h-8 text-emerald-500" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold">{stats?.success_rate || 0}%</div>
            <div className="text-sm text-gray-500">Success Rate</div>
          </div>
        </div>
        <div className="bg-white border rounded-xl p-5">
          <div className="flex items-center justify-between">
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold">{stats?.failed_executions || 0}</div>
            <div className="text-sm text-gray-500">Failed</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="col-span-2 space-y-6">
          {/* Active Executions */}
          {activeExecutions.length > 0 && (
            <div className="bg-white border rounded-xl p-5">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-blue-500 animate-pulse" />
                Running Now
              </h2>
              <div className="space-y-3">
                {activeExecutions.map((exec) => (
                  <Link key={exec.execution_id} to={`/workflows/executions/${exec.execution_id}`} className="flex justify-between items-center p-3 bg-blue-50 rounded-lg hover:bg-blue-100">
                    <div>
                      <div className="font-medium">{exec.workflow_name}</div>
                      <div className="text-sm text-gray-500">{exec.current_step}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-blue-600">{(exec.duration_ms / 1000).toFixed(1)}s</div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Recent Executions */}
          <div className="bg-white border rounded-xl p-5">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Recent Executions</h2>
              <Link to="/workflows/executions" className="text-sm text-blue-600">View All</Link>
            </div>
            <div className="space-y-2">
              {recentExecutions.map((exec) => (
                <Link key={exec.execution_id} to={`/workflows/executions/${exec.execution_id}`} className="flex justify-between items-center p-3 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-center gap-3">
                    {exec.status === 'completed' ? <CheckCircle className="w-5 h-5 text-green-500" /> : exec.status === 'failed' ? <XCircle className="w-5 h-5 text-red-500" /> : <Clock className="w-5 h-5 text-gray-400" />}
                    <div>
                      <div className="font-medium">{exec.workflow_name}</div>
                      <div className="text-sm text-gray-500">{new Date(exec.started_at).toLocaleString()}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm ${exec.status === 'completed' ? 'text-green-600' : exec.status === 'failed' ? 'text-red-600' : 'text-gray-500'}`}>
                      {exec.duration_ms ? `${(exec.duration_ms / 1000).toFixed(2)}s` : '-'}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Status Chart */}
          <div className="bg-white border rounded-xl p-5">
            <h2 className="text-lg font-semibold mb-4">Execution Status</h2>
            <div className="h-48">
              <Doughnut data={statusChartData} options={{ maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }} />
            </div>
          </div>

          {/* Top Workflows */}
          <div className="bg-white border rounded-xl p-5">
            <h2 className="text-lg font-semibold mb-4">Top Workflows</h2>
            <div className="space-y-3">
              {stats?.top_workflows?.map((wf, i) => (
                <div key={wf.workflow_id} className="flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-gray-400">#{i + 1}</span>
                    <span className="font-medium truncate max-w-[150px]">{wf.name}</span>
                  </div>
                  <span className="text-sm text-gray-500">{wf.count} runs</span>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Links */}
          <div className="bg-white border rounded-xl p-5">
            <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
            <div className="space-y-2">
              <Link to="/workflows/builder" className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50">
                <Zap className="w-5 h-5 text-blue-500" />
                <span>Create Workflow</span>
              </Link>
              <Link to="/workflows/templates" className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50">
                <TrendingUp className="w-5 h-5 text-green-500" />
                <span>Browse Templates</span>
              </Link>
              <Link to="/workflows/dead-letter" className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50">
                <XCircle className="w-5 h-5 text-red-500" />
                <span>Dead Letter Queue</span>
              </Link>
              <Link to="/workflows/settings" className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50">
                <Settings className="w-5 h-5 text-gray-500" />
                <span>Settings</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
