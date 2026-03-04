import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { AlertTriangle, TrendingUp } from 'lucide-react';

/**
 * PredictionChart - Display forecasts and predictions
 */
const PredictionChart = ({
  apiClient,
  companyId,
  type = 'call-volume', // 'call-volume', 'costs', 'anomalies'
  daysAhead = 7,
  agentId = null,
}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadPredictions();
  }, [type, daysAhead, agentId]);

  const loadPredictions = async () => {
    try {
      setLoading(true);
      setError(null);

      let response;

      if (type === 'call-volume') {
        response = await apiClient.get(
          `/api/v1/predictions/call-volume?days_ahead=${daysAhead}`
        );
      } else if (type === 'costs') {
        response = await apiClient.get(
          `/api/v1/predictions/costs?days_ahead=${daysAhead}`
        );
      } else if (type === 'anomalies') {
        response = await apiClient.get('/api/v1/predictions/anomalies');
      } else if (type === 'agent-performance' && agentId) {
        response = await apiClient.get(
          `/api/v1/predictions/agent-performance/${agentId}`
        );
      }

      setData(response.data);
    } catch (err) {
      console.error(`Error loading ${type} predictions:`, err);
      setError(`Failed to load ${type} predictions`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4 w-1/3"></div>
          <div className="h-96 bg-gray-100 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6 border border-red-200">
        <div className="flex items-center text-red-600">
          <AlertTriangle className="w-5 h-5 mr-2" />
          {error}
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  // Call Volume Forecast
  if (type === 'call-volume' && data.forecast) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
            Call Volume Forecast
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Next {daysAhead} days (Confidence: {(data.confidence * 100).toFixed(0)}%)
          </p>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-50 p-3 rounded">
            <div className="text-sm text-gray-600">Avg Daily Calls</div>
            <div className="text-2xl font-bold text-blue-600">
              {data.average_daily_calls}
            </div>
          </div>
          <div className="bg-green-50 p-3 rounded">
            <div className="text-sm text-gray-600">Trend</div>
            <div className="text-2xl font-bold text-green-600">
              {data.trend_per_day > 0 ? '+' : ''}
              {data.trend_per_day.toFixed(1)}
            </div>
          </div>
          <div className="bg-purple-50 p-3 rounded">
            <div className="text-sm text-gray-600">Days Forecast</div>
            <div className="text-2xl font-bold text-purple-600">
              {data.forecast_days}
            </div>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={data.forecast}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip formatter={(value) => value} />
            <Legend />
            <Line
              type="monotone"
              dataKey="predicted_calls"
              stroke="#3b82f6"
              name="Predicted Calls"
              strokeWidth={2}
              dot={{ fill: '#3b82f6', r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // Cost Forecast
  if (type === 'costs' && data.forecast) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-amber-600" />
            Cost Forecast
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Next {daysAhead} days (Confidence: {(data.confidence * 100).toFixed(0)}%)
          </p>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-amber-50 p-3 rounded">
            <div className="text-sm text-gray-600">Avg Daily Cost</div>
            <div className="text-2xl font-bold text-amber-600">
              ${data.average_daily_cost.toFixed(2)}
            </div>
          </div>
          <div className="bg-orange-50 p-3 rounded">
            <div className="text-sm text-gray-600">Monthly Projection</div>
            <div className="text-2xl font-bold text-orange-600">
              ${data.monthly_projection.toFixed(2)}
            </div>
          </div>
          <div className="bg-red-50 p-3 rounded">
            <div className="text-sm text-gray-600">Cost per Call</div>
            <div className="text-2xl font-bold text-red-600">
              ${data.average_cost_per_call.toFixed(4)}
            </div>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={data.forecast}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
            <Legend />
            <Bar
              dataKey="predicted_daily_cost"
              fill="#f59e0b"
              name="Predicted Daily Cost"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // Anomalies
  if (type === 'anomalies' && data.anomalies) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2 text-red-600" />
            Detected Anomalies ({data.anomaly_count})
          </h3>
        </div>

        {data.anomalies.length === 0 ? (
          <div className="text-gray-600 text-center py-8">
            No anomalies detected - system operating normally
          </div>
        ) : (
          <div className="space-y-3">
            {data.anomalies.map((anomaly, idx) => (
              <div
                key={idx}
                className={`p-3 rounded border-l-4 ${
                  anomaly.severity === 'critical'
                    ? 'bg-red-50 border-red-500'
                    : anomaly.severity === 'warning'
                    ? 'bg-amber-50 border-amber-500'
                    : 'bg-blue-50 border-blue-500'
                }`}
              >
                <div className="font-semibold text-sm capitalize">
                  {anomaly.type.replace('_', ' ')}
                </div>
                <div className="text-sm text-gray-700 mt-1">
                  {anomaly.message}
                </div>
                {anomaly.percent_change && (
                  <div className="text-xs text-gray-600 mt-1">
                    Change: {anomaly.percent_change > 0 ? '+' : ''}
                    {anomaly.percent_change.toFixed(1)}%
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Agent Performance
  if (type === 'agent-performance' && data.agent_id) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold">Agent Performance Analysis</h3>
          <p className="text-sm text-gray-600 mt-1">Last 30 days metrics</p>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-blue-50 p-4 rounded">
            <div className="text-sm text-gray-600">Success Rate</div>
            <div className="text-3xl font-bold text-blue-600">
              {(data.success_rate * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {data.successful_calls}/{data.total_calls} calls
            </div>
          </div>
          <div className="bg-green-50 p-4 rounded">
            <div className="text-sm text-gray-600">Avg Duration</div>
            <div className="text-3xl font-bold text-green-600">
              {Math.round(data.average_duration_seconds / 60)}m
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {data.average_duration_seconds.toFixed(0)}s per call
            </div>
          </div>
          <div className="bg-purple-50 p-4 rounded">
            <div className="text-sm text-gray-600">Total Cost</div>
            <div className="text-3xl font-bold text-purple-600">
              ${data.total_cost.toFixed(2)}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              ${data.cost_per_call.toFixed(4)}/call
            </div>
          </div>
          <div className="bg-amber-50 p-4 rounded">
            <div className="text-sm text-gray-600">Trend</div>
            <div className="text-3xl font-bold text-amber-600 capitalize">
              {data.trend}
            </div>
          </div>
        </div>

        <div className="bg-gray-50 p-4 rounded border-l-4 border-blue-500">
          <div className="font-semibold text-sm mb-2">Recommendation</div>
          <div className="text-sm text-gray-700">{data.recommendation}</div>
        </div>

        {data.confidence && (
          <div className="mt-4 text-xs text-gray-500">
            Confidence: {(data.confidence * 100).toFixed(0)}%
          </div>
        )}
      </div>
    );
  }

  return null;
};

export default PredictionChart;
