import React, { useState, useMemo } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import {
  AlertCircle, CheckCircle, Clock, TrendingUp, Wifi, WifiOff,
  RefreshCw, AlertTriangle
} from 'lucide-react';
import { useAnalyticsStream } from '../hooks/useAnalyticsStream';
import DashboardCard from './DashboardCard';

/**
 * Live Analytics Dashboard with real-time WebSocket updates.
 * Updates every 30 seconds automatically.
 */
function AnalyticsDashboardLive({ companyId = 'default' }) {
  const { metrics, alerts, predictions, connected, error, requestUpdate, ping } = useAnalyticsStream(companyId);
  const [dismissedAlerts, setDismissedAlerts] = useState(new Set());

  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value || 0);
  };

  // Filter active alerts
  const activeAlerts = useMemo(() => {
    return (alerts || []).filter(alert => !dismissedAlerts.has(alert.id));
  }, [alerts, dismissedAlerts]);

  // Chart colors
  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Live Analytics Dashboard</h1>
            <p className="text-gray-500 mt-1">Real-time metrics with 30-second auto-refresh</p>
          </div>
          
          {/* Connection Status */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              {connected ? (
                <>
                  <Wifi className="w-5 h-5 text-green-500" />
                  <span className="text-sm font-medium text-green-700">Connected</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-5 h-5 text-gray-400" />
                  <span className="text-sm font-medium text-gray-600">Disconnected</span>
                </>
              )}
            </div>
            
            <button
              onClick={requestUpdate}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh Now
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {/* Live Alerts */}
        {activeAlerts.length > 0 && (
          <div className="mb-6 space-y-2">
            {activeAlerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-lg flex items-start justify-between ${
                  alert.severity === 'critical'
                    ? 'bg-red-50 border border-red-200'
                    : alert.severity === 'warning'
                    ? 'bg-yellow-50 border border-yellow-200'
                    : 'bg-blue-50 border border-blue-200'
                }`}
              >
                <div className="flex items-start gap-3">
                  {alert.severity === 'critical' ? (
                    <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-yellow-500 mt-0.5" />
                  )}
                  <div>
                    <h3 className="font-medium text-gray-900">{alert.alert_type}</h3>
                    <p className="text-sm text-gray-600">{alert.message}</p>
                  </div>
                </div>
                <button
                  onClick={() => setDismissedAlerts(new Set([...dismissedAlerts, alert.id]))}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Summary Cards */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <DashboardCard
              title="Total Calls"
              value={metrics.calls_summary?.total_calls || 0}
              subtitle="All time"
              variant="blue"
              icon={<Clock className="w-6 h-6" />}
            />
            <DashboardCard
              title="Avg Duration"
              value={`${(metrics.calls_summary?.avg_duration_seconds || 0).toFixed(1)}s`}
              subtitle="Per call"
              variant="green"
              icon={<TrendingUp className="w-6 h-6" />}
            />
            <DashboardCard
              title="Success Rate"
              value={`${((metrics.calls_summary?.success_rate || 0) * 100).toFixed(1)}%`}
              subtitle="Completed calls"
              variant="purple"
              icon={<CheckCircle className="w-6 h-6" />}
            />
            <DashboardCard
              title="Total Cost"
              value={formatCurrency(metrics.calls_summary?.total_ai_cost || 0)}
              subtitle="AI services"
              variant="amber"
              icon={<TrendingUp className="w-6 h-6" />}
            />
          </div>
        )}

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Calls by Agent */}
          {metrics?.by_agent && metrics.by_agent.length > 0 && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Calls by Agent</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={metrics.by_agent}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="agent_id" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="call_count" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Cost Breakdown */}
          {metrics?.costs && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Cost Breakdown</h2>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'OpenAI', value: metrics.costs.openai_cost || 0 },
                      { name: 'ElevenLabs', value: metrics.costs.elevenlabs_cost || 0 },
                      { name: 'Twilio', value: metrics.costs.twilio_cost || 0 }
                    ]}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${formatCurrency(value)}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {COLORS.map((color, index) => (
                      <Cell key={`cell-${index}`} fill={color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Calls by Phone */}
        {metrics?.by_phone && metrics.by_phone.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Calls by Phone Number</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Phone Number</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Calls</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Success Rate</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Avg Duration</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Cost</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {metrics.by_phone.map((phone) => (
                    <tr key={phone.phone_number} className="hover:bg-gray-50">
                      <td className="px-6 py-3 text-sm text-gray-900 font-medium">{phone.phone_number}</td>
                      <td className="px-6 py-3 text-sm text-gray-600">{phone.call_count}</td>
                      <td className="px-6 py-3 text-sm text-gray-600">
                        {((phone.success_rate || 0) * 100).toFixed(1)}%
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-600">
                        {(phone.avg_duration_seconds || 0).toFixed(1)}s
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-600">
                        {formatCurrency(phone.total_ai_cost)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* System Health */}
        {metrics?.health && (
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">System Health</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="border-l-4 border-blue-500 pl-4">
                <p className="text-sm text-gray-600">Uptime</p>
                <p className="text-lg font-semibold text-gray-900">
                  {((metrics.health.uptime_percentage || 0) * 100).toFixed(2)}%
                </p>
              </div>
              <div className="border-l-4 border-green-500 pl-4">
                <p className="text-sm text-gray-600">Error Rate</p>
                <p className="text-lg font-semibold text-gray-900">
                  {((metrics.health.error_rate || 0) * 100).toFixed(2)}%
                </p>
              </div>
              <div className="border-l-4 border-purple-500 pl-4">
                <p className="text-sm text-gray-600">Active Agents</p>
                <p className="text-lg font-semibold text-gray-900">
                  {metrics.health.active_agents || 0}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {!metrics && connected && (
          <div className="bg-white p-12 rounded-lg shadow text-center">
            <RefreshCw className="w-8 h-8 text-gray-400 mx-auto mb-4 animate-spin" />
            <p className="text-gray-600">Loading live metrics...</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default AnalyticsDashboardLive;
