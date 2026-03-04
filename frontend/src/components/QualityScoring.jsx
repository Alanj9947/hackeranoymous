import React, { useState, useEffect } from 'react';
import {
  Star, TrendingUp, BarChart3, AlertCircle,
  CheckCircle, Zap, Loader
} from 'lucide-react';

/**
 * Quality Scoring Dashboard - Monitor call quality metrics.
 */
function QualityScoring({ agentId = null, companyId = 'default' }) {
  const [metrics, setMetrics] = useState(null);
  const [trend, setTrend] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [days, setDays] = useState(7);
  const [callData, setCallData] = useState({
    duration_seconds: 240,
    success: true,
    sentiment_score: 0.8,
    transcript_length: 800
  });
  const [scoring, setScoring] = useState(false);
  const [lastScore, setLastScore] = useState(null);

  // Load agent metrics
  useEffect(() => {
    if (agentId) {
      loadMetrics();
    }
  }, [agentId, days]);

  const loadMetrics = async () => {
    setLoading(true);
    setError(null);

    try {
      const [metricsRes, trendRes] = await Promise.all([
        fetch(`/api/v1/quality/agent/${agentId}/metrics?days=${days}`),
        fetch(`/api/v1/quality/agent/${agentId}/trend?days=${days}`)
      ]);

      if (!metricsRes.ok || !trendRes.ok) {
        throw new Error('Failed to load quality metrics');
      }

      const metricsData = await metricsRes.json();
      const trendData = await trendRes.json();

      setMetrics(metricsData);
      setTrend(trendData.trend);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const scoreCall = async (e) => {
    e.preventDefault();
    setScoring(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/quality/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          call_id: `call_${Date.now()}`,
          ...callData
        })
      });

      if (!response.ok) {
        throw new Error('Failed to score call');
      }

      const score = await response.json();
      setLastScore(score);
    } catch (err) {
      setError(err.message);
    } finally {
      setScoring(false);
    }
  };

  const getQualityColor = (level) => {
    switch (level) {
      case 'excellent':
        return { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700', badge: 'bg-green-100 text-green-800' };
      case 'good':
        return { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', badge: 'bg-blue-100 text-blue-800' };
      case 'fair':
        return { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-700', badge: 'bg-yellow-100 text-yellow-800' };
      case 'poor':
        return { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', badge: 'bg-red-100 text-red-800' };
      default:
        return { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-700', badge: 'bg-gray-100 text-gray-800' };
    }
  };

  const ScoreCard = ({ title, score, max, reason }) => (
    <div className="bg-white rounded-lg shadow p-4">
      <p className="text-sm font-medium text-gray-600 mb-2">{title}</p>
      <div className="mb-2">
        <div className="text-2xl font-bold text-gray-900">{score}</div>
        <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
          <div
            className="bg-blue-600 h-2 rounded-full"
            style={{ width: `${(score / max) * 100}%` }}
          ></div>
        </div>
      </div>
      <p className="text-xs text-gray-500">{reason}</p>
    </div>
  );

  if (!agentId && !lastScore) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Call Quality Scoring</h1>

          {/* Score a Call */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Form */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Score a Call</h2>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                  {error}
                </div>
              )}

              <form onSubmit={scoreCall} className="space-y-4">
                {/* Duration */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Call Duration (seconds)
                  </label>
                  <input
                    type="number"
                    value={callData.duration_seconds}
                    onChange={(e) => setCallData(prev => ({
                      ...prev,
                      duration_seconds: parseInt(e.target.value)
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Optimal: 180-300 seconds (3-5 min)</p>
                </div>

                {/* Success */}
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={callData.success}
                      onChange={(e) => setCallData(prev => ({
                        ...prev,
                        success: e.target.checked
                      }))}
                      className="w-4 h-4 text-blue-600"
                    />
                    <span className="ml-2 text-sm text-gray-700">Call Successful</span>
                  </label>
                </div>

                {/* Sentiment */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Sentiment Score (0-1)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={callData.sentiment_score}
                    onChange={(e) => setCallData(prev => ({
                      ...prev,
                      sentiment_score: parseFloat(e.target.value)
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">0 = very negative, 1 = very positive</p>
                </div>

                {/* Transcript Length */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Transcript Word Count
                  </label>
                  <input
                    type="number"
                    value={callData.transcript_length}
                    onChange={(e) => setCallData(prev => ({
                      ...prev,
                      transcript_length: parseInt(e.target.value)
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Optimal: ~150 words per minute</p>
                </div>

                {/* Submit */}
                <button
                  type="submit"
                  disabled={scoring}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                  {scoring ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin" />
                      Scoring...
                    </>
                  ) : (
                    <>
                      <Star className="w-4 h-4" />
                      Score Call
                    </>
                  )}
                </button>
              </form>
            </div>

            {/* Last Score Display */}
            {lastScore && (
              <div className={`${getQualityColor(lastScore.quality_level).bg} border ${getQualityColor(lastScore.quality_level).border} rounded-lg p-6`}>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-semibold text-gray-900">Score Result</h2>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getQualityColor(lastScore.quality_level).badge}`}>
                    {lastScore.quality_level.toUpperCase()}
                  </span>
                </div>

                <div className="mb-6">
                  <div className="text-4xl font-bold text-gray-900 mb-2">
                    {lastScore.overall_score}
                    <span className="text-lg text-gray-600">/100</span>
                  </div>
                  <div className="w-full bg-gray-300 rounded-full h-3">
                    <div
                      className="bg-blue-600 h-3 rounded-full transition-all"
                      style={{ width: `${lastScore.overall_score}%` }}
                    ></div>
                  </div>
                </div>

                {/* Component Scores */}
                <div className="space-y-3">
                  {Object.entries(lastScore.component_scores).map(([key, data]) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700 capitalize">{key}</span>
                      <span className="text-sm font-bold text-gray-900">{data.score}/100</span>
                    </div>
                  ))}
                </div>

                {/* Recommendations */}
                {lastScore.recommendations.length > 0 && (
                  <div className="mt-6 pt-6 border-t border-gray-300">
                    <p className="text-sm font-medium text-gray-900 mb-3">Recommendations:</p>
                    <ul className="space-y-2">
                      {lastScore.recommendations.map((rec, i) => (
                        <li key={i} className="text-sm text-gray-700">
                          • {rec.text}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Agent Metrics View
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Quality Metrics</h1>
          <p className="text-gray-500 mt-1">Agent: {agentId}</p>
        </div>

        {/* Period Selector */}
        <div className="mb-6 flex gap-2">
          {[7, 14, 30].map(d => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                days === d
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              {d} Days
            </button>
          ))}
        </div>

        {/* Summary Cards */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-sm text-gray-600 mb-2">Average Score</p>
              <p className="text-3xl font-bold text-gray-900">
                {metrics.metrics.average_quality_score || 0}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-sm text-gray-600 mb-2">Calls Analyzed</p>
              <p className="text-3xl font-bold text-gray-900">
                {metrics.metrics.calls_analyzed || 0}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-sm text-gray-600 mb-2">Excellent Calls</p>
              <p className="text-3xl font-bold text-green-600">
                {metrics.metrics.excellent_calls || 0}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-sm text-gray-600 mb-2">Quality Trend</p>
              <p className={`text-3xl font-bold ${
                metrics.metrics.quality_trend === 'improving' ? 'text-green-600' :
                metrics.metrics.quality_trend === 'declining' ? 'text-red-600' :
                'text-gray-600'
              }`}>
                {metrics.metrics.quality_trend === 'improving' ? '↑' : '→'}
              </p>
            </div>
          </div>
        )}

        {/* Quality Distribution */}
        {metrics && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quality Distribution</h2>
            <div className="grid grid-cols-4 gap-4">
              {[
                { label: 'Excellent', count: metrics.metrics.excellent_calls, color: 'bg-green-500' },
                { label: 'Good', count: metrics.metrics.good_calls, color: 'bg-blue-500' },
                { label: 'Fair', count: metrics.metrics.fair_calls, color: 'bg-yellow-500' },
                { label: 'Poor', count: metrics.metrics.poor_calls, color: 'bg-red-500' }
              ].map(item => (
                <div key={item.label} className="text-center">
                  <div className={`${item.color} h-24 rounded-lg mb-2 flex items-center justify-center`}>
                    <span className="text-white font-bold text-lg">{item.count}</span>
                  </div>
                  <p className="text-sm font-medium text-gray-700">{item.label}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Trend Chart Placeholder */}
        {trend.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quality Trend</h2>
            <div className="h-64 flex items-center justify-center text-gray-500">
              {/* Chart would render here */}
              Trend visualization ({trend.length} data points)
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default QualityScoring;
