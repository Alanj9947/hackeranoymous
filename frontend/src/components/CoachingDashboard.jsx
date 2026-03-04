import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import {
  Award,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  ThumbsUp,
} from 'lucide-react';

/**
 * CoachingDashboard - Agent coaching insights and recommendations
 */
const CoachingDashboard = ({ apiClient, companyId, agentId = null }) => {
  const [agentInsights, setAgentInsights] = useState(null);
  const [teamReport, setTeamReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [view, setView] = useState('team'); // 'team' or 'agent'

  useEffect(() => {
    loadCoachingData();
  }, [agentId]);

  const loadCoachingData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load team report
      const teamRes = await apiClient.get('/api/v1/coaching/team-report');
      setTeamReport(teamRes.data);

      // Load agent insights if specified
      if (agentId) {
        const agentRes = await apiClient.get(
          `/api/v1/coaching/agents/${agentId}/insights`
        );
        setAgentInsights(agentRes.data);
        setView('agent');
      }
    } catch (err) {
      console.error('Error loading coaching data:', err);
      setError('Failed to load coaching data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-4 w-1/3"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-100 rounded"></div>
            <div className="h-4 bg-gray-100 rounded"></div>
            <div className="h-96 bg-gray-100 rounded mt-4"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6 border border-red-200">
        <div className="flex items-center text-red-600">
          <AlertCircle className="w-5 h-5 mr-2" />
          {error}
        </div>
      </div>
    );
  }

  // Agent View
  if (view === 'agent' && agentInsights) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">
                {agentInsights.agent_name}
              </h2>
              <p className="text-gray-600 mt-1">
                Coaching Insights - Last 30 Days
              </p>
            </div>
            <button
              onClick={() => setView('team')}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Back to Team
            </button>
          </div>
        </div>

        {/* Scores */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <ScoreCard
            title="Success Score"
            score={agentInsights.scores.success_score}
            color="blue"
          />
          <ScoreCard
            title="Efficiency Score"
            score={agentInsights.scores.efficiency_score}
            color="green"
          />
          <ScoreCard
            title="Quality Score"
            score={agentInsights.scores.quality_score}
            color="purple"
          />
          <ScoreCard
            title="Overall Score"
            score={agentInsights.scores.overall_score}
            color="amber"
            highlight
          />
        </div>

        {/* Performance Level Badge */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Award className="w-6 h-6 mr-3 text-amber-600" />
            <div>
              <div className="text-sm text-gray-600">Performance Level</div>
              <div className="text-2xl font-bold capitalize">
                {agentInsights.performance_level.replace('_', ' ')}
              </div>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 bg-white rounded-lg shadow p-6">
          <div>
            <div className="text-sm text-gray-600">Success Rate</div>
            <div className="text-2xl font-bold text-blue-600">
              {(agentInsights.success_rate * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">
              {agentInsights.successful_calls}/{agentInsights.total_calls}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Avg Duration</div>
            <div className="text-2xl font-bold text-green-600">
              {Math.round(agentInsights.average_call_duration_seconds / 60)}m
            </div>
            <div className="text-xs text-gray-500">
              {agentInsights.average_call_duration_seconds.toFixed(0)}s
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Cost per Call</div>
            <div className="text-2xl font-bold text-amber-600">
              ${agentInsights.cost_per_call.toFixed(4)}
            </div>
            <div className="text-xs text-gray-500">
              ${agentInsights.total_cost.toFixed(2)} total
            </div>
          </div>
        </div>

        {/* Insights */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <CheckCircle className="w-5 h-5 mr-2 text-blue-600" />
            Key Insights
          </h3>
          <ul className="space-y-2">
            {agentInsights.insights.map((insight, idx) => (
              <li key={idx} className="flex items-start">
                <span className="text-blue-600 mr-3 mt-1">•</span>
                <span className="text-gray-700">{insight}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Recommendations */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <ThumbsUp className="w-5 h-5 mr-2 text-green-600" />
            Coaching Recommendations
          </h3>
          <div className="space-y-4">
            {agentInsights.recommendations.map((rec, idx) => (
              <div
                key={idx}
                className={`border-l-4 p-4 rounded ${
                  rec.priority === 'high'
                    ? 'border-red-500 bg-red-50'
                    : rec.priority === 'medium'
                    ? 'border-amber-500 bg-amber-50'
                    : 'border-blue-500 bg-blue-50'
                }`}
              >
                <div className="font-semibold capitalize">
                  {rec.priority} Priority - {rec.category.replace('_', ' ')}
                </div>
                <div className="text-sm text-gray-700 mt-2">
                  {rec.recommendation}
                </div>
                <ul className="mt-3 ml-4 space-y-1">
                  {rec.action_items.map((item, i) => (
                    <li key={i} className="text-sm text-gray-700">
                      • {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Team View
  if (teamReport) {
    const radarData = teamReport.report
      .slice(0, 5)
      .map((agent) => ({
        name: agent.agent_name.split(' ')[0], // First name only for brevity
        score: agent.overall_score,
      }));

    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-2xl font-bold">Team Coaching Report</h2>
          <p className="text-gray-600 mt-1">Last 30 days - {teamReport.agent_count} agents</p>
        </div>

        {/* Team Averages */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 rounded-lg shadow p-6">
            <div className="text-sm text-gray-600">Team Avg Success</div>
            <div className="text-3xl font-bold text-blue-600">
              {(teamReport.team_average_success_rate * 100).toFixed(1)}%
            </div>
          </div>
          <div className="bg-green-50 rounded-lg shadow p-6">
            <div className="text-sm text-gray-600">Team Avg Score</div>
            <div className="text-3xl font-bold text-green-600">
              {teamReport.team_average_score}
            </div>
          </div>
          <div className="bg-purple-50 rounded-lg shadow p-6">
            <div className="text-sm text-gray-600">Total Agents</div>
            <div className="text-3xl font-bold text-purple-600">
              {teamReport.agent_count}
            </div>
          </div>
        </div>

        {/* Top Performer & Needs Attention */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {teamReport.top_performer && (
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
              <h3 className="font-semibold mb-3 flex items-center">
                <Award className="w-5 h-5 mr-2 text-green-600" />
                Top Performer
              </h3>
              <div className="font-semibold text-lg">
                {teamReport.top_performer.agent_name}
              </div>
              <div className="text-sm text-gray-600 mt-2">
                Score: <span className="font-bold text-green-600">
                  {teamReport.top_performer.overall_score}
                </span>
              </div>
              <div className="text-sm text-gray-600">
                Success Rate: <span className="font-bold">
                  {(teamReport.top_performer.success_rate * 100).toFixed(1)}%
                </span>
              </div>
              <button
                onClick={() => setView('agent')}
                className="mt-3 text-sm text-blue-600 hover:text-blue-700 font-semibold"
              >
                View Details →
              </button>
            </div>
          )}

          {teamReport.needs_attention && (
            <div className="bg-white rounded-lg shadow p-6 border-l-4 border-amber-500">
              <h3 className="font-semibold mb-3 flex items-center">
                <AlertCircle className="w-5 h-5 mr-2 text-amber-600" />
                Needs Coaching
              </h3>
              <div className="font-semibold text-lg">
                {teamReport.needs_attention.agent_name}
              </div>
              <div className="text-sm text-gray-600 mt-2">
                Score: <span className="font-bold text-amber-600">
                  {teamReport.needs_attention.overall_score}
                </span>
              </div>
              <div className="text-sm text-gray-600">
                Success Rate: <span className="font-bold">
                  {(teamReport.needs_attention.success_rate * 100).toFixed(1)}%
                </span>
              </div>
              <button
                onClick={() => setView('agent')}
                className="mt-3 text-sm text-blue-600 hover:text-blue-700 font-semibold"
              >
                Provide Coaching →
              </button>
            </div>
          )}
        </div>

        {/* Team Rankings Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Agent Scores (Top 10)</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              data={teamReport.report.slice(0, 10).map((agent) => ({
                name: agent.agent_name,
                score: agent.overall_score,
              }))}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Bar dataKey="score" fill="#3b82f6" name="Overall Score" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* All Agents Table */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">All Agents</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b">
                <tr>
                  <th className="text-left py-2 px-2">Agent</th>
                  <th className="text-right py-2 px-2">Calls</th>
                  <th className="text-right py-2 px-2">Success</th>
                  <th className="text-right py-2 px-2">Avg Duration</th>
                  <th className="text-right py-2 px-2">Score</th>
                  <th className="text-right py-2 px-2">Level</th>
                </tr>
              </thead>
              <tbody>
                {teamReport.report.map((agent) => (
                  <tr
                    key={agent.agent_id}
                    className="border-b hover:bg-gray-50 cursor-pointer"
                    onClick={() => {
                      setAgentInsights({
                        agent_id: agent.agent_id,
                        agent_name: agent.agent_name,
                      });
                      setView('agent');
                    }}
                  >
                    <td className="py-2 px-2 font-medium">
                      {agent.agent_name}
                    </td>
                    <td className="py-2 px-2 text-right">
                      {agent.total_calls}
                    </td>
                    <td className="py-2 px-2 text-right">
                      {(agent.success_rate * 100).toFixed(1)}%
                    </td>
                    <td className="py-2 px-2 text-right">
                      {Math.round(agent.avg_duration / 60)}m
                    </td>
                    <td className="py-2 px-2 text-right font-semibold">
                      {agent.overall_score}
                    </td>
                    <td className="py-2 px-2 text-right capitalize">
                      <span
                        className={`px-2 py-1 rounded text-xs font-semibold ${
                          agent.performance_level === 'exceptional'
                            ? 'bg-green-100 text-green-800'
                            : agent.performance_level === 'excellent'
                            ? 'bg-blue-100 text-blue-800'
                            : agent.performance_level === 'good'
                            ? 'bg-cyan-100 text-cyan-800'
                            : agent.performance_level === 'fair'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {agent.performance_level}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

/**
 * ScoreCard - Individual score display
 */
const ScoreCard = ({ title, score, color = 'blue', highlight = false }) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-200',
    amber: 'bg-amber-50 text-amber-600 border-amber-200',
  };

  return (
    <div
      className={`rounded-lg p-4 border ${colorClasses[color]} ${
        highlight ? 'shadow-lg ring-2 ring-offset-2' : 'shadow'
      }`}
    >
      <div className="text-sm text-gray-600 font-medium">{title}</div>
      <div className="text-3xl font-bold mt-2">{score}</div>
      <div className="text-xs text-gray-500 mt-1">out of 100</div>
    </div>
  );
};

export default CoachingDashboard;
