import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useCalls, useAgents, useInitiateCall } from '@/hooks/use-api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { PageLoader } from '@/components/ui/Spinner';
import { Phone, PhoneOutgoing, Eye } from 'lucide-react';
import { formatDate, formatDuration } from '@/lib/utils';
import { AxiosError } from 'axios';
import toast from 'react-hot-toast';

export default function CallsPage() {
  const [page, setPage] = useState(1);
  const { data: calls, isLoading } = useCalls(page);
  const { data: agents } = useAgents();
  const initiate = useInitiateCall();

  const [showDialer, setShowDialer] = useState(false);
  const [dialAgentId, setDialAgentId] = useState('');
  const [dialPhone, setDialPhone] = useState('');

  if (isLoading) return <PageLoader />;

  const list = calls || [];
  const agentList = agents || [];

  const handleCall = async () => {
    if (!dialAgentId || !dialPhone) {
      toast.error('Select an agent and enter a phone number');
      return;
    }
    try {
      await initiate.mutateAsync({ agent_id: dialAgentId, to_number: dialPhone });
      setShowDialer(false);
      setDialPhone('');
    } catch (err: unknown) {
      const message = err instanceof AxiosError ? err.response?.data?.detail : 'Failed to initiate call';
      toast.error(message || 'Failed to initiate call');
    }
  };

  const statusColor = (s: string) => {
    switch (s) {
      case 'completed': return 'success';
      case 'in-progress': return 'warning';
      case 'failed': return 'destructive';
      default: return 'outline';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Calls</h1>
          <p className="text-gray-500">Monitor and manage voice calls</p>
        </div>
        <Button onClick={() => setShowDialer(!showDialer)}>
          <PhoneOutgoing size={18} className="mr-2" /> New Call
        </Button>
      </div>

      {/* Dialer */}
      {showDialer && (
        <Card>
          <CardHeader><CardTitle>Initiate Outbound Call</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Agent</label>
              <select
                className="w-full h-10 rounded-md border border-gray-300 px-3 text-sm"
                value={dialAgentId}
                onChange={(e) => setDialAgentId(e.target.value)}
              >
                <option value="">Select agent...</option>
                {agentList.map((a: any) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Phone Number</label>
              <Input
                type="tel"
                value={dialPhone}
                onChange={(e) => setDialPhone(e.target.value)}
                placeholder="+1234567890"
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCall} disabled={initiate.isPending}>
                <Phone size={16} className="mr-2" />
                {initiate.isPending ? 'Calling…' : 'Call'}
              </Button>
              <Button variant="outline" onClick={() => setShowDialer(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Call list */}
      <Card>
        <CardContent className="p-0">
          {list.length === 0 ? (
            <div className="p-12 text-center">
              <Phone size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">No calls yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 text-left text-gray-500">
                    <th className="p-3 font-medium">Phone</th>
                    <th className="p-3 font-medium">Direction</th>
                    <th className="p-3 font-medium">Status</th>
                    <th className="p-3 font-medium">Duration</th>
                    <th className="p-3 font-medium">Date</th>
                    <th className="p-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((call: any) => (
                    <tr key={call.id} className="border-b last:border-0 hover:bg-gray-50">
                      <td className="p-3 font-mono text-xs">{call.from_number || call.to_number || '—'}</td>
                      <td className="p-3">
                        <Badge variant={call.direction === 'inbound' ? 'default' : 'outline'}>
                          {call.direction}
                        </Badge>
                      </td>
                      <td className="p-3">
                        <Badge variant={statusColor(call.status)}>{call.status}</Badge>
                      </td>
                      <td className="p-3">
                        {call.duration_seconds ? formatDuration(call.duration_seconds) : '—'}
                      </td>
                      <td className="p-3 text-gray-500">{call.created_at ? formatDate(call.created_at) : '—'}</td>
                      <td className="p-3">
                        <Link to={`/calls/${call.id}`}>
                          <Button variant="ghost" size="sm">
                            <Eye size={14} className="mr-1" /> View
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {list.length >= 20 && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            Previous
          </Button>
          <span className="flex items-center px-3 text-sm text-gray-500">Page {page}</span>
          <Button variant="outline" size="sm" onClick={() => setPage(page + 1)}>
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
