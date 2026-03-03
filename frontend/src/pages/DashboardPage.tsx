import { useAgents, useCalls, useExtractions } from '@/hooks/use-api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { PageLoader } from '@/components/ui/Spinner';
import { Bot, Phone, Database, TrendingUp, Clock } from 'lucide-react';
import { formatDate } from '@/lib/utils';

export default function DashboardPage() {
  const agents = useAgents();
  const calls = useCalls();
  const extractions = useExtractions();

  if (agents.isLoading) return <PageLoader />;

  const agentList = agents.data || [];
  const callList = calls.data || [];
  const extractionList = extractions.data || [];

  const stats = [
    { label: 'Total Agents', value: agentList.length, icon: Bot, color: 'text-blue-600 bg-blue-100' },
    { label: 'Total Calls', value: callList.length, icon: Phone, color: 'text-green-600 bg-green-100' },
    { label: 'Extractions', value: extractionList.length, icon: Database, color: 'text-purple-600 bg-purple-100' },
    { label: 'Active Agents', value: agentList.filter((a: any) => a.status === 'active').length, icon: TrendingUp, color: 'text-orange-600 bg-orange-100' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-gray-500">Overview of your voice agent platform</p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{stat.label}</p>
                  <p className="text-3xl font-bold mt-1">{stat.value}</p>
                </div>
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <stat.icon size={22} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent calls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Phone size={18} /> Recent Calls
          </CardTitle>
        </CardHeader>
        <CardContent>
          {callList.length === 0 ? (
            <p className="text-gray-500 text-sm py-4">No calls yet. Create an agent and make your first call.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-2 font-medium">Agent</th>
                    <th className="pb-2 font-medium">Direction</th>
                    <th className="pb-2 font-medium">Status</th>
                    <th className="pb-2 font-medium">Duration</th>
                    <th className="pb-2 font-medium">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {callList.slice(0, 5).map((call: any) => (
                    <tr key={call.id} className="border-b last:border-0">
                      <td className="py-3">{call.agent_id?.slice(0, 8)}</td>
                      <td className="py-3">
                        <Badge variant={call.direction === 'inbound' ? 'default' : 'outline'}>
                          {call.direction}
                        </Badge>
                      </td>
                      <td className="py-3">
                        <Badge variant={call.status === 'completed' ? 'success' : 'warning'}>
                          {call.status}
                        </Badge>
                      </td>
                      <td className="py-3">{call.duration_seconds ? `${call.duration_seconds}s` : '—'}</td>
                      <td className="py-3 text-gray-500">{call.created_at ? formatDate(call.created_at) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Active agents */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot size={18} /> Your Agents
          </CardTitle>
        </CardHeader>
        <CardContent>
          {agentList.length === 0 ? (
            <p className="text-gray-500 text-sm py-4">No agents created yet.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agentList.slice(0, 6).map((agent: any) => (
                <div key={agent.id} className="border rounded-lg p-4 hover:border-primary-300 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold">{agent.name}</h3>
                    <Badge variant={agent.status === 'active' ? 'success' : 'outline'}>
                      {agent.status === 'active' ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-500 truncate">{agent.description || 'No description'}</p>
                  <div className="flex items-center gap-1 mt-2 text-xs text-gray-400">
                    <Clock size={12} />
                    {agent.created_at ? formatDate(agent.created_at) : ''}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
