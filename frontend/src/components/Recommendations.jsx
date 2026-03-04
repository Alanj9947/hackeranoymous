import React, { useState, useEffect } from 'react';
import {
  Lightbulb, ThumbsUp, ThumbsDown, AlertCircle, Loader,
  TrendingUp, Zap, Target, CheckCircle
} from 'lucide-react';

/**
 * Recommendations Component - AI-driven agent optimization recommendations.
 */
function Recommendations({ agentId, companyId = 'default' }) {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [impactScore, setImpactScore] = useState(null);
  const [filter, setFilter] = useState('all'); // all, pending, accepted, rejected
  const [expandedId, setExpandedId] = useState(null);

  const [metricsForm, setMetricsForm] = useState({
    accuracy: 85,
    avg_handle_time: 300,
    customer_satisfaction: 4.0,
    team_avg_handle_time: 280
  });
  const [analyzing, setAnalyzing] = useState(false);

  const priorityColors = {
    low: 'bg-blue-50 border-blue-200 text-blue-900',
    medium: 'bg-yellow-50 border-yellow-200 text-yellow-900',
    high: 'bg-orange-50 border-orange-200 text-orange-900',
    critical: 'bg-red-50 border-red-200 text-red-900'
  };

  const priorityBadgeColors = {
    low: 'bg-blue-100 text-blue-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-orange-100 text-orange-800',
    critical: 'bg-red-100 text-red-800'
  };

  // Load recommendations on mount
  useEffect(() => {
    if (agentId) {
      loadRecommendations();
      loadImpactScore();
    }
  }, [agentId]);

  const loadRecommendations = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/v1/recommendations/agent/${agentId}`
      );

      if (!response.ok) throw new Error('Failed to load recommendations');

      const data = await response.json();
      setRecommendations(data.recommendations);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadImpactScore = async () => {
    try {
      const response = await fetch(
        `/api/v1/recommendations/agent/${agentId}/impact`
      );

      if (!response.ok) throw new Error('Failed to load impact');

      const data = await response.json();
      setImpactScore(data);
    } catch (err) {
      // Optional
    }
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    setAnalyzing(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/v1/recommendations/analyze-agent/${agentId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(metricsForm)
        }
      );

      if (!response.ok) throw new Error('Failed to analyze');

      const data = await response.json();
      setRecommendations(data.recommendations);
      loadImpactScore();
    } catch (err) {
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleAccept = async (recId) => {
    try {
      const response = await fetch(
        `/api/v1/recommendations/${recId}/accept`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ agent_id: agentId })
        }
      );

      if (!response.ok) throw new Error('Failed to accept');

      loadRecommendations();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleReject = async (recId) => {
    try {
      const response = await fetch(
        `/api/v1/recommendations/${recId}/reject`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ agent_id: agentId })
        }
      );

      if (!response.ok) throw new Error('Failed to reject');

      loadRecommendations();
    } catch (err) {
      setError(err.message);
    }
  };

  const filteredRecs = recommendations.filter((rec) => {
    if (filter === 'all') return true;
    return rec.status === filter;
  });

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Recommendations</h1>
          <p className="text-gray-500 mt-1">AI-driven optimization suggestions for {agentId}</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {/* Impact Score Card */}
        {impactScore && (
          <div className="mb-8 bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Productivity Impact</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div>
                <p className="text-sm text-gray-600 mb-2">Current Productivity</p>
                <p className="text-3xl font-bold text-blue-600">
                  {impactScore.current_productivity.toFixed(0)}%
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-2">Potential Productivity</p>
                <p className="text-3xl font-bold text-green-600">
                  {impactScore.potential_productivity.toFixed(0)}%
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-2">Improvement Potential</p>
                <p className="text-3xl font-bold text-purple-600">
                  +{impactScore.improvement_potential.toFixed(0)}%
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-2">Estimated ROI</p>
                <p className="text-3xl font-bold text-orange-600">
                  {impactScore.estimated_roi.toFixed(0)}x
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Metrics Input Form */}
        <div className="mb-8 bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">Agent Metrics</h2>
          <form onSubmit={handleAnalyze} className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Accuracy (%)
              </label>
              <input
                type="number"
                value={metricsForm.accuracy}
                onChange={(e) => setMetricsForm(prev => ({
                  ...prev,
                  accuracy: parseFloat(e.target.value)
                }))}
                min="0"
                max="100"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Handle Time (sec)
              </label>
              <input
                type="number"
                value={metricsForm.avg_handle_time}
                onChange={(e) => setMetricsForm(prev => ({
                  ...prev,
                  avg_handle_time: parseInt(e.target.value)
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Satisfaction (0-5)
              </label>
              <input
                type="number"
                value={metricsForm.customer_satisfaction}
                onChange={(e) => setMetricsForm(prev => ({
                  ...prev,
                  customer_satisfaction: parseFloat(e.target.value)
                }))}
                min="0"
                max="5"
                step="0.1"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div className="flex items-end">
              <button
                type="submit"
                disabled={analyzing}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
              >
                {analyzing ? 'Analyzing...' : 'Analyze'}
              </button>
            </div>
          </form>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6">
          {['all', 'pending', 'accepted', 'rejected'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg font-medium capitalize ${
                filter === status
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 border'
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        {/* Recommendations List */}
        {loading ? (
          <div className="text-center py-12">
            <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
          </div>
        ) : filteredRecs.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No recommendations available
          </div>
        ) : (
          <div className="space-y-4">
            {filteredRecs.map((rec) => (
              <div
                key={rec.id}
                className={`border-2 rounded-lg p-6 cursor-pointer transition-colors ${priorityColors[rec.priority]}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Lightbulb className="w-5 h-5" />
                      <h3 className="text-lg font-semibold">{rec.title}</h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-bold ${priorityBadgeColors[rec.priority]}`}>
                        {rec.priority.toUpperCase()}
                      </span>
                    </div>

                    <p className="text-sm mb-4">{rec.description}</p>

                    {/* Expanded Details */}
                    {expandedId === rec.id && (
                      <div className="mt-4 space-y-3 text-sm">
                        <div>
                          <p className="font-semibold mb-1">Estimated Benefits:</p>
                          <ul className="list-disc list-inside space-y-1">
                            {Object.entries(rec.estimated_benefit || {}).map(([key, value]) => (
                              <li key={key} className="text-sm">
                                {key.replace(/_/g, ' ')}: <span className="font-semibold">{value}</span>
                              </li>
                            ))}
                          </ul>
                        </div>

                        {rec.action_items && rec.action_items.length > 0 && (
                          <div>
                            <p className="font-semibold mb-1">Action Items:</p>
                            <ul className="list-disc list-inside space-y-1">
                              {rec.action_items.map((item, idx) => (
                                <li key={idx} className="text-sm">{item}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Stats */}
                  <div className="ml-4 text-center">
                    <div className="text-2xl font-bold text-current">
                      {rec.impact_score.toFixed(0)}
                    </div>
                    <p className="text-xs opacity-75">Impact</p>
                  </div>
                </div>

                {/* Actions */}
                <div className="mt-4 flex gap-2">
                  <button
                    onClick={() => setExpandedId(expandedId === rec.id ? null : rec.id)}
                    className="flex-1 px-3 py-2 bg-gray-200 rounded-lg hover:bg-gray-300 text-sm font-medium"
                  >
                    {expandedId === rec.id ? 'Hide Details' : 'Show Details'}
                  </button>

                  {rec.status === 'pending' && (
                    <>
                      <button
                        onClick={() => handleAccept(rec.id)}
                        className="flex-1 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium flex items-center justify-center gap-1"
                      >
                        <CheckCircle className="w-4 h-4" />
                        Accept
                      </button>
                      <button
                        onClick={() => handleReject(rec.id)}
                        className="flex-1 px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium"
                      >
                        Reject
                      </button>
                    </>
                  )}

                  {rec.status === 'accepted' && (
                    <div className="flex-1 px-3 py-2 bg-green-100 text-green-800 rounded-lg text-sm font-medium text-center">
                      ✓ Accepted
                    </div>
                  )}

                  {rec.status === 'rejected' && (
                    <div className="flex-1 px-3 py-2 bg-red-100 text-red-800 rounded-lg text-sm font-medium text-center">
                      ✗ Rejected
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Recommendations;
