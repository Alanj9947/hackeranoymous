import React, { useState, useEffect } from 'react';
import {
  MessageSquare, TrendingUp, AlertCircle, Loader, BarChart3,
  Zap, Heart, Frown, Smile, Meh
} from 'lucide-react';

/**
 * NLP Analysis Component - Sentiment analysis and text insights.
 */
function NLPAnalysis({ companyId = 'default' }) {
  const [activeTab, setActiveTab] = useState('analyze'); // analyze, trends
  const [text, setText] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [trendsLoading, setTrendsLoading] = useState(false);

  const emotionIcons = {
    anger: <Frown className="w-5 h-5 text-red-600" />,
    joy: <Heart className="w-5 h-5 text-pink-600" />,
    sadness: <Frown className="w-5 h-5 text-blue-600" />,
    fear: <AlertCircle className="w-5 h-5 text-yellow-600" />,
    surprise: <Zap className="w-5 h-5 text-purple-600" />
  };

  const sentimentColors = {
    very_negative: 'text-red-700 bg-red-50',
    negative: 'text-orange-700 bg-orange-50',
    neutral: 'text-gray-700 bg-gray-50',
    positive: 'text-green-700 bg-green-50',
    very_positive: 'text-emerald-700 bg-emerald-50'
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    setAnalyzing(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/nlp/sentiment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });

      if (!response.ok) throw new Error('Analysis failed');

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const loadTrends = async () => {
    setTrendsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/nlp/sentiment-trend?days=7');
      if (!response.ok) throw new Error('Failed to load trends');

      const data = await response.json();
      setTrendData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setTrendsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'trends') {
      loadTrends();
    }
  }, [activeTab]);

  const getSentimentIcon = (sentiment) => {
    if (sentiment === 'very_positive' || sentiment === 'positive') {
      return <Smile className="w-6 h-6 text-green-600" />;
    }
    if (sentiment === 'very_negative' || sentiment === 'negative') {
      return <Frown className="w-6 h-6 text-red-600" />;
    }
    return <Meh className="w-6 h-6 text-gray-600" />;
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">NLP Analysis</h1>
          <p className="text-gray-500 mt-1">Sentiment analysis and text insights</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setActiveTab('analyze')}
            className={`px-6 py-3 rounded-lg font-medium ${
              activeTab === 'analyze'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            <MessageSquare className="w-4 h-4 inline mr-2" />
            Analyze
          </button>
          <button
            onClick={() => setActiveTab('trends')}
            className={`px-6 py-3 rounded-lg font-medium ${
              activeTab === 'trends'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            <TrendingUp className="w-4 h-4 inline mr-2" />
            Trends
          </button>
        </div>

        {/* Analyze Tab */}
        {activeTab === 'analyze' && (
          <div className="space-y-6">
            {/* Input Form */}
            <form onSubmit={handleAnalyze} className="bg-white rounded-lg shadow p-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Text to Analyze
              </label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Enter text to analyze for sentiment, intent, and entities..."
                rows="6"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="submit"
                disabled={analyzing || !text.trim()}
                className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
              >
                {analyzing ? 'Analyzing...' : 'Analyze'}
              </button>
            </form>

            {/* Results */}
            {result && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Sentiment Card */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-sm font-semibold text-gray-600 mb-4">Sentiment</h3>
                  <div className="flex items-center justify-between mb-4">
                    {getSentimentIcon(result.sentiment)}
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${sentimentColors[result.sentiment]}`}>
                      {result.sentiment.replace(/_/g, ' ').toUpperCase()}
                    </span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Score</span>
                      <span className="font-semibold text-gray-900">
                        {(result.score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Confidence</span>
                      <span className="font-semibold text-gray-900">
                        {(result.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Emotions Card */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-sm font-semibold text-gray-600 mb-4">Emotions</h3>
                  <div className="space-y-3">
                    {Object.entries(result.emotions).map(([emotion, value]) => (
                      <div key={emotion} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {emotionIcons[emotion]}
                          <span className="text-sm text-gray-700 capitalize">{emotion}</span>
                        </div>
                        <div className="flex-1 ml-3 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${value * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Entities & Keywords */}
                <div className="space-y-4">
                  {/* Entities */}
                  {result.entities.length > 0 && (
                    <div className="bg-white rounded-lg shadow p-6">
                      <h3 className="text-sm font-semibold text-gray-600 mb-3">Entities</h3>
                      <div className="space-y-2">
                        {result.entities.map((entity, idx) => (
                          <div key={idx} className="p-2 bg-purple-50 rounded">
                            <p className="text-sm font-medium text-purple-900">{entity.text}</p>
                            <p className="text-xs text-purple-700">
                              {entity.type} • {(entity.confidence * 100).toFixed(0)}%
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Keywords */}
                  {result.keywords.length > 0 && (
                    <div className="bg-white rounded-lg shadow p-6">
                      <h3 className="text-sm font-semibold text-gray-600 mb-3">Keywords</h3>
                      <div className="flex flex-wrap gap-2">
                        {result.keywords.map((keyword, idx) => (
                          <span
                            key={idx}
                            className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
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
            ) : trendData ? (
              <div className="space-y-6">
                {/* Summary */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">7-Day Summary</h2>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Average Score</p>
                      <p className="text-3xl font-bold text-blue-600">
                        {(trendData.average_score * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Trend</p>
                      <p className="text-2xl font-bold text-gray-900 capitalize">
                        {trendData.trend}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Sample Size</p>
                      <p className="text-3xl font-bold text-gray-900">
                        {trendData.sample_size}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Distribution */}
                {trendData.sentiment_distribution && (
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Sentiment Distribution
                    </h3>
                    <div className="space-y-3">
                      {Object.entries(trendData.sentiment_distribution).map(([sentiment, count]) => (
                        <div key={sentiment}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-gray-700 capitalize">
                              {sentiment.replace(/_/g, ' ')}
                            </span>
                            <span className="text-sm font-semibold text-gray-900">{count}</span>
                          </div>
                          <div className="h-2 bg-gray-200 rounded-full">
                            <div
                              className="h-2 bg-blue-600 rounded-full"
                              style={{ width: `${(count / trendData.sample_size) * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Emotions */}
                {trendData.emotion_averages && (
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                      Average Emotions
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {Object.entries(trendData.emotion_averages).map(([emotion, avg]) => (
                        <div key={emotion} className="flex items-center gap-3">
                          {emotionIcons[emotion]}
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-700 capitalize">
                              {emotion}
                            </p>
                            <div className="h-2 bg-gray-200 rounded-full mt-1">
                              <div
                                className="h-2 bg-green-600 rounded-full"
                                style={{ width: `${avg * 100}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                No sentiment data available
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default NLPAnalysis;
