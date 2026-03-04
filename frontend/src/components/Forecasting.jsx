import React, { useState, useEffect } from 'react';
import {
  TrendingUp, TrendingDown, AlertTriangle, Loader, BarChart3,
  Activity, DollarSign, Users, AlertCircle, Eye, EyeOff
} from 'lucide-react';

/**
 * Forecasting Component - ML-powered predictions and anomaly detection.
 */
function Forecasting({ companyId = 'default' }) {
  const [activeTab, setActiveTab] = useState('forecast'); // forecast, anomalies, scenario, trends
  const [metric, setMetric] = useState('call_volume');
  const [horizonDays, setHorizonDays] = useState(30);
  const [forecastModel, setForecastModel] = useState('exponential_smoothing');
  const [forecasting, setForecasting] = useState(false);
  const [forecast, setForecast] = useState(null);
  const [error, setError] = useState(null);

  const [anomalies, setAnomalies] = useState([]);
  const [anomaliesLoading, setAnomaliesLoading] = useState(false);
  const [anomalyThreshold, setAnomalyThreshold] = useState(2.0);

  const [scenarioAdjustment, setScenarioAdjustment] = useState(10);
  const [scenarioForecast, setScenarioForecast] = useState(null);
  const [scenarioLoading, setScenarioLoading] = useState(false);

  const [trends, setTrends] = useState({});
  const [trendsLoading, setTrendsLoading] = useState(false);

  const [modelComparison, setModelComparison] = useState({});
  const [comparingModels, setComparingModels] = useState(false);

  const metrics = [
    { value: 'call_volume', label: 'Call Volume', icon: Activity },
    { value: 'call_duration', label: 'Call Duration', icon: Activity },
    { value: 'cost', label: 'Cost', icon: DollarSign },
    { value: 'agent_availability', label: 'Agent Availability', icon: Users },
    { value: 'customer_satisfaction', label: 'Customer Satisfaction', icon: Activity },
    { value: 'error_rate', label: 'Error Rate', icon: AlertTriangle }
  ];

  const models = [
    { value: 'exponential_smoothing', label: 'Exponential Smoothing' },
    { value: 'moving_average', label: 'Moving Average' },
    { value: 'linear_regression', label: 'Linear Regression' },
    { value: 'seasonal', label: 'Seasonal' },
    { value: 'arima', label: 'ARIMA' }
  ];

  // Load forecast on metric/horizon change
  useEffect(() => {
    if (activeTab === 'forecast') {
      generateForecast();
    }
  }, [metric, horizonDays, forecastModel, activeTab]);

  // Load trends
  useEffect(() => {
    if (activeTab === 'trends') {
      loadTrends();
    }
  }, [activeTab]);

  const generateForecast = async () => {
    setForecasting(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/v1/forecasting/forecast/${metric}?horizon_days=${horizonDays}&model=${forecastModel}`
      );

      if (!response.ok) throw new Error('Failed to generate forecast');

      const data = await response.json();
      setForecast(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setForecasting(false);
    }
  };

  const loadAnomalies = async () => {
    setAnomaliesLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/v1/forecasting/anomalies/${metric}?threshold=${anomalyThreshold}`
      );

      if (!response.ok) throw new Error('Failed to load anomalies');

      const data = await response.json();
      setAnomalies(data.anomalies);
    } catch (err) {
      setError(err.message);
    } finally {
      setAnomaliesLoading(false);
    }
  };

  const generateScenario = async () => {
    setScenarioLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/v1/forecasting/scenario?metric=${metric}&adjustment_percent=${scenarioAdjustment}&horizon_days=${horizonDays}`
      );

      if (!response.ok) throw new Error('Failed to generate scenario');

      const data = await response.json();
      setScenarioForecast(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setScenarioLoading(false);
    }
  };

  const loadTrends = async () => {
    setTrendsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/forecasting/trends');
      if (!response.ok) throw new Error('Failed to load trends');

      const data = await response.json();
      setTrends(data.trends);
    } catch (err) {
      setError(err.message);
    } finally {
      setTrendsLoading(false);
    }
  };

  const compareModels = async () => {
    setComparingModels(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/v1/forecasting/model-comparison/${metric}?horizon_days=${horizonDays}`
      );

      if (!response.ok) throw new Error('Failed to compare models');

      const data = await response.json();
      setModelComparison(data.models);
    } catch (err) {
      setError(err.message);
    } finally {
      setComparingModels(false);
    }
  };

  const getTrendIcon = (trend) => {
    if (trend === 'increasing') return <TrendingUp className="w-5 h-5 text-green-600" />;
    if (trend === 'decreasing') return <TrendingDown className="w-5 h-5 text-red-600" />;
    return <Activity className="w-5 h-5 text-gray-600" />;
  };

  const getTrendColor = (trend) => {
    if (trend === 'increasing') return 'text-green-600';
    if (trend === 'decreasing') return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">ML Forecasting</h1>
          <p className="text-gray-500 mt-1">Predictive analytics and anomaly detection</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-4 mb-6 overflow-x-auto">
          <button
            onClick={() => setActiveTab('forecast')}
            className={`px-6 py-3 rounded-lg font-medium whitespace-nowrap ${
              activeTab === 'forecast'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            <TrendingUp className="w-4 h-4 inline mr-2" />
            Forecast
          </button>
          <button
            onClick={() => { setActiveTab('anomalies'); loadAnomalies(); }}
            className={`px-6 py-3 rounded-lg font-medium whitespace-nowrap ${
              activeTab === 'anomalies'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            <AlertTriangle className="w-4 h-4 inline mr-2" />
            Anomalies
          </button>
          <button
            onClick={() => setActiveTab('scenario')}
            className={`px-6 py-3 rounded-lg font-medium whitespace-nowrap ${
              activeTab === 'scenario'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            <Eye className="w-4 h-4 inline mr-2" />
            What-If
          </button>
          <button
            onClick={() => setActiveTab('trends')}
            className={`px-6 py-3 rounded-lg font-medium whitespace-nowrap ${
              activeTab === 'trends'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            <BarChart3 className="w-4 h-4 inline mr-2" />
            Trends
          </button>
        </div>

        {/* Forecast Tab */}
        {activeTab === 'forecast' && (
          <div className="space-y-6">
            {/* Controls */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Metric
                  </label>
                  <select
                    value={metric}
                    onChange={(e) => setMetric(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    {metrics.map((m) => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Model
                  </label>
                  <select
                    value={forecastModel}
                    onChange={(e) => setForecastModel(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    {models.map((m) => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Horizon (days)
                  </label>
                  <input
                    type="number"
                    value={horizonDays}
                    onChange={(e) => setHorizonDays(Math.min(90, parseInt(e.target.value) || 30))}
                    min="1"
                    max="90"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Actions
                  </label>
                  <button
                    onClick={compareModels}
                    disabled={comparingModels}
                    className="w-full px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 text-sm"
                  >
                    {comparingModels ? 'Comparing...' : 'Compare Models'}
                  </button>
                </div>
              </div>
            </div>

            {/* Forecast Results */}
            {forecasting ? (
              <div className="text-center py-12">
                <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
              </div>
            ) : forecast ? (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Summary Cards */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-sm font-semibold text-gray-600 mb-4">Summary</h3>
                  <div className="space-y-3">
                    <div>
                      <p className="text-xs text-gray-600">Trend</p>
                      <div className="flex items-center gap-2 mt-1">
                        {getTrendIcon(forecast.trend)}
                        <span className={`font-semibold ${getTrendColor(forecast.trend)}`}>
                          {forecast.trend.toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Model Accuracy</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">
                        {Math.round(forecast.accuracy * 100)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Data Points</p>
                      <p className="text-lg font-semibold text-gray-900 mt-1">
                        {forecast.metadata.data_points}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Latest Predictions */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-sm font-semibold text-gray-600 mb-4">Predictions (Next 7 Days)</h3>
                  <div className="space-y-2">
                    {forecast.predictions.slice(0, 7).map((pred, idx) => (
                      <div key={idx} className="flex items-center justify-between text-sm">
                        <span className="text-gray-700">Day {idx + 1}</span>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-gray-900">
                            {pred.value.toFixed(2)}
                          </span>
                          {forecast.confidence_intervals[idx] && (
                            <span className="text-xs text-gray-500">
                              ±{(forecast.confidence_intervals[idx].upper - forecast.confidence_intervals[idx].lower).toFixed(2)}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Model Comparison */}
                {Object.keys(modelComparison).length > 0 && (
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-sm font-semibold text-gray-600 mb-4">Model Comparison</h3>
                    <div className="space-y-3">
                      {Object.entries(modelComparison).map(([model, data]) => (
                        <div key={model} className="p-3 bg-gray-50 rounded-lg">
                          <p className="text-xs font-medium text-gray-700 mb-1">
                            {model.replace(/_/g, ' ').toUpperCase()}
                          </p>
                          <p className="text-lg font-bold text-blue-600">
                            {Math.round(data.accuracy * 100)}% accuracy
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                Load a forecast to see predictions
              </div>
            )}
          </div>
        )}

        {/* Anomalies Tab */}
        {activeTab === 'anomalies' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Threshold (Std Dev)
                  </label>
                  <input
                    type="number"
                    value={anomalyThreshold}
                    onChange={(e) => setAnomalyThreshold(parseFloat(e.target.value) || 2.0)}
                    min="1"
                    max="5"
                    step="0.5"
                    className="w-32 px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
            </div>

            {anomaliesLoading ? (
              <div className="text-center py-12">
                <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
              </div>
            ) : anomalies.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                No anomalies detected
              </div>
            ) : (
              <div className="space-y-4">
                {anomalies.map((anomaly, idx) => (
                  <div key={idx} className="bg-red-50 border border-red-200 rounded-lg p-6">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold text-red-900 flex items-center gap-2">
                          <AlertTriangle className="w-5 h-5" />
                          Anomaly Detected
                        </h3>
                        <div className="mt-3 space-y-1 text-sm text-red-800">
                          <p>Time: {new Date(anomaly.timestamp).toLocaleString()}</p>
                          <p>Value: {anomaly.value.toFixed(2)}</p>
                          <p>Z-Score: {anomaly.z_score.toFixed(2)}</p>
                          <p>Deviation: {anomaly.deviation_percent.toFixed(1)}%</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* What-If Scenario Tab */}
        {activeTab === 'scenario' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">What-If Scenario</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Metric
                  </label>
                  <select
                    value={metric}
                    onChange={(e) => setMetric(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    {metrics.map((m) => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Adjustment (%)
                  </label>
                  <input
                    type="number"
                    value={scenarioAdjustment}
                    onChange={(e) => setScenarioAdjustment(parseInt(e.target.value) || 10)}
                    min="-100"
                    max="100"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Action
                  </label>
                  <button
                    onClick={generateScenario}
                    disabled={scenarioLoading}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                  >
                    {scenarioLoading ? 'Generating...' : 'Generate'}
                  </button>
                </div>
              </div>
            </div>

            {scenarioForecast && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Scenario: {scenarioAdjustment > 0 ? '+' : ''}{scenarioAdjustment}%
                </h3>
                <div className="space-y-3">
                  {scenarioForecast.predictions.slice(0, 14).map((pred, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-gray-700 font-medium">
                        {new Date(pred.timestamp).toLocaleDateString()}
                      </span>
                      <div className="text-right">
                        <p className="font-bold text-gray-900">{pred.value.toFixed(2)}</p>
                        <p className="text-xs text-gray-500">
                          Range: {scenarioForecast.confidence_intervals[idx].lower.toFixed(2)} - {scenarioForecast.confidence_intervals[idx].upper.toFixed(2)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Trends Tab */}
        {activeTab === 'trends' && (
          <div>
            {trendsLoading ? (
              <div className="text-center py-12">
                <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
              </div>
            ) : Object.keys(trends).length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                No trends available
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {Object.entries(trends).map(([metricKey, trendData]) => (
                  <div key={metricKey} className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-sm font-semibold text-gray-600 mb-4 uppercase">
                      {metricKey.replace(/_/g, ' ')}
                    </h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-700">Trend</span>
                        <div className="flex items-center gap-2">
                          {getTrendIcon(trendData.trend)}
                          <span className={`font-semibold ${getTrendColor(trendData.trend)}`}>
                            {trendData.trend}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-700">Accuracy</span>
                        <span className="font-bold text-blue-600">
                          {Math.round(trendData.accuracy * 100)}%
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-700">Avg Value</span>
                        <span className="font-semibold text-gray-900">
                          {trendData.avg_value?.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Forecasting;
