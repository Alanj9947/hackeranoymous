import { Link } from 'react-router-dom';
import { useAgents, useDeleteAgent } from '@/hooks/use-api';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { PageLoader } from '@/components/ui/Spinner';
import { Plus, Trash2, Edit, Bot } from 'lucide-react';
import { formatDate } from '@/lib/utils';

export default function AgentsPage() {
  const { data: agents, isLoading } = useAgents();
  const deleteAgent = useDeleteAgent();

  if (isLoading) return <PageLoader />;

  const list = agents || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Voice Agents</h1>
          <p className="text-gray-500">Manage your AI voice agents</p>
        </div>
        <Link to="/agents/new">
          <Button>
            <Plus size={18} className="mr-2" /> New Agent
          </Button>
        </Link>
      </div>

      {list.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Bot size={48} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold mb-2">No agents yet</h3>
            <p className="text-gray-500 mb-4">Create your first voice agent to get started.</p>
            <Link to="/agents/new">
              <Button>Create Agent</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {list.map((agent: any) => (
            <Card key={agent.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100 text-primary-600">
                      <Bot size={20} />
                    </div>
                    <div>
                      <h3 className="font-semibold">{agent.name}</h3>
                      <p className="text-xs text-gray-400">{agent.language || 'en-US'}</p>
                    </div>
                  </div>
                  <Badge variant={agent.status === 'active' ? 'success' : 'outline'}>
                    {agent.status === 'active' ? 'Active' : 'Inactive'}
                  </Badge>
                </div>

                <p className="text-sm text-gray-500 mb-4 line-clamp-2">
                  {agent.description || 'No description provided'}
                </p>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">
                    {agent.created_at && formatDate(agent.created_at)}
                  </span>
                  <div className="flex items-center gap-1">
                    <Link to={`/agents/${agent.id}`}>
                      <Button variant="ghost" size="icon">
                        <Edit size={16} />
                      </Button>
                    </Link>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => {
                        if (confirm('Delete this agent?')) deleteAgent.mutate(agent.id);
                      }}
                    >
                      <Trash2 size={16} className="text-red-500" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
