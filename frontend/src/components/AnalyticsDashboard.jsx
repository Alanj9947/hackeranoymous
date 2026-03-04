/**
 * AnalyticsDashboard - Real-time analytics and insights
 * Displays call metrics, agent performance, costs, and system health
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  Calendar,
  TrendingUp,
  Users,
  Phone,
  DollarSign,
  Activity,
  Download,
  RefreshCw,
} from 'lucide-react';
import { analyticsService } from '../services/analyticsService';
import DashboardCard from './DashboardCard';
import MetricChart from './MetricChart';

export const AnalyticsDashboard = ({ agentId = null }) => {
  // State
  const [dateFrom, setDateFrom] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 7);
    return d.toISOString().split('T')[0];
  });
  const [dateTo, setDateTo] = useState(new Date().toISOString().split('T')[0]);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Data state
  const [callStats, setCallStats] = useState(null);
  const [agentMetrics, setAgentMetrics] = useState([]);
  const [phoneMetrics, setPhoneMetrics] = useState([]);
  const [callTrends, setCallTrends] = useState([]);
  const [costData, setCostData] = useState(null);
  const [healthData, setHealthData] = useState(null);

  // Load all analytics data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const from = dateFrom + 'T00:00:00Z';
      const to = dateTo + 'T23:59:59Z';

      // Fetch all data in parallel
      const [stats, agents, phones, trends, costs, health] = await Promise.all([
        analyticsService.getCallsSummary(from, to),
        analyticsService.getCallsByAgent(from, to),
        analyticsService.getCallsByPhone(from, to),
        analyticsService.getCallTrends('day', from, to),
        analyticsService.getCostsSummary(from, to),
        analyticsService.getSystemHealth(),
      ]);

      setCallStats(stats);
      setAgentMetrics(agents.agents || []);
      setPhoneMetrics(phones.phones || []);
      setCallTrends(trends.trends || []);
      setCostData(costs);
      setHealthData(health);
    } catch (err) {
      console.error('Error loading analytics:', err);
      setError(err.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  }, [dateFrom, dateTo]);

  // Load data on mount and when dates change
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      loadData();
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh, loadData]);

  // Colors for charts
  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-1">Real-time call metrics and insights</p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Date Range & Controls */}
      <div className="bg-white rounded-lg p-4 border border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              From
            </label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              To
            </label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Auto-refresh</span>
          </label>
          <button className="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg flex items-center gap-2">
            <Download size={18} />
            Export
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          <p className="font-semibold">Error loading analytics</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Summary Cards */}
      {callStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <DashboardCard
            icon={Phone}
            title="Total Calls"
            value={callStats.total_calls}
            subtitle={`${callStats.success_rate}% success rate`}
            color="blue"
          />
          <DashboardCard
            icon={TrendingUp}
            title="Avg Duration"
            value={`${callStats.avg_duration_seconds}s`}
            subtitle={`${callStats.total_duration_seconds}s total`}
            color="green"
          />
          <DashboardCard
            icon={Users}
            title="Agents Active"
            value={agentMetrics.length}
            subtitle={`${(agentMetrics.reduce((sum, a) => sum + a.total_calls, 0) / Math.max(agentMetrics.length, 1)).toFixed(0)} avg calls/agent`}
            color="purple"
          />
          <DashboardCard
            icon={DollarSign}
            title="Total Cost"
            value={`$${callStats.total_cost_usd}`}
            subtitle={`$${callStats.total_cost_usd > 0 ? (callStats.total_cost_usd / callStats.total_calls).toFixed(3) : 0}/call`}
            color="amber"
          />
        </div>
      )}

      {/* System Health */}
      {healthData && (
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Activity size={20} />
            System Health
          </h2>
          <div className="grid grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-gray-600">Uptime</p>
              <p className="text-2xl font-bold text-gray-900">{healthData.uptime_percent}%</p>
              <p className="text-xs text-gray-500 mt-1">Last 24 hours</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Error Rate</p>
              <p className="text-2xl font-bold text-gray-900">{healthData.error_rate_percent}%</p>
              <p className="text-xs text-gray-500 mt-1">{healthData.errors_last_24h} errors</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Status</p>
              <p
                className={`text-2xl font-bold mt-1 ${
                  healthData.status === 'healthy'
                    ? 'text-green-600'
                    : 'text-yellow-600'
                }`}
              >
                {healthData.status}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Call Trends */}
      {callTrends.length > 0 && (
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Call Volume Trend</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={callTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="call_count"
                stroke="#3b82f6"
                name="Calls"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Agent Performance */}
      {agentMetrics.length > 0 && (
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Agent Performance</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={agentMetrics.slice(0, 10)}
              layout="vertical"
              margin={{ left: 150 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="agent_name" type="category" width={140} />
              <Tooltip />
              <Bar dataKey="total_calls" fill="#3b82f6" name="Calls" />
              <Bar dataKey="success_rate" fill="#10b981" name="Success %" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Cost Breakdown */}
      {costData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Cost by Service</h2>
            <div className="space-y-3">
              {costData.estimated_breakdown &&
                Object.entries(costData.estimated_breakdown).map(([service, cost]) => (
                  <div key={service} className="flex justify-between items-center">
                    <span className="text-gray-600 capitalize">
                      {service.replace('_usd', '')}
                    </span>
                    <span className="font-semibold text-gray-900">${cost}</span>
                  </div>
                ))}
            </div>
            <div className="border-t border-gray-200 mt-4 pt-4">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-gray-900">Total</span>
                <span className="text-xl font-bold text-gray-900">
                  ${costData.total_cost_usd}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Cost Metrics</h2>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-600">Cost per Call</p>
                <p className="text-2xl font-bold text-gray-900">
                  ${costData.cost_per_call}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Calls Analyzed</p>
                <p className="text-2xl font-bold text-gray-900">
                  {costData.completed_calls}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Phone Numbers Performance */}
      {phoneMetrics.length > 0 && (
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Phone Numbers</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-gray-600 font-semibold">
                    Phone
                  </th>
                  <th className="text-right py-3 px-4 text-gray-600 font-semibold">
                    Calls
                  </th>
                  <th className="text-right py-3 px-4 text-gray-600 font-semibold">
                    Success Rate
                  </th>
                  <th className="text-right py-3 px-4 text-gray-600 font-semibold">
                    Avg Duration
                  </th>
                </tr>
              </thead>
              <tbody>
                {phoneMetrics.slice(0, 10).map((phone) => (
                  <tr key={phone.phone_number_id} className="border-b border-gray-100">
                    <td className="py-3 px-4 text-gray-900">{phone.phone_number}</td>
                    <td className="py-3 px-4 text-right text-gray-900">
                      {phone.total_calls}
                    </td>
                    <td className="py-3 px-4 text-right text-gray-900">
                      {phone.success_rate}%
                    </td>
                    <td className="py-3 px-4 text-right text-gray-600">
                      {phone.avg_duration_seconds}s
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 flex items-center gap-3">
            <div className="animate-spin">
              <RefreshCw size={24} className="text-blue-600" />
            </div>
            <p className="text-gray-900">Loading analytics...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;
