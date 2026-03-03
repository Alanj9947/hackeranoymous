import { useParams, useNavigate } from 'react-router-dom';
import { useCall, useCallTranscript, useTriggerExtraction } from '@/hooks/use-api';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { PageLoader } from '@/components/ui/Spinner';
import { ArrowLeft, Database, Download } from 'lucide-react';
import { formatDate, formatDuration } from '@/lib/utils';

export default function CallDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: call, isLoading } = useCall(id);
  const { data: transcript } = useCallTranscript(id);
  const triggerExtraction = useTriggerExtraction();

  if (isLoading) return <PageLoader />;
  if (!call) return <p>Call not found</p>;

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/calls')}>
          <ArrowLeft size={20} />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Call Details</h1>
          <p className="text-gray-500 font-mono text-sm">{call.id}</p>
        </div>
      </div>

      {/* Call info */}
      <Card>
        <CardHeader><CardTitle>Overview</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">Direction</p>
              <Badge variant={call.direction === 'inbound' ? 'default' : 'outline'}>{call.direction}</Badge>
            </div>
            <div>
              <p className="text-sm text-gray-500">Status</p>
              <Badge variant={call.status === 'completed' ? 'success' : 'warning'}>{call.status}</Badge>
            </div>
            <div>
              <p className="text-sm text-gray-500">Duration</p>
              <p className="font-semibold">{call.duration_seconds ? formatDuration(call.duration_seconds) : '—'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Date</p>
              <p className="font-semibold">{call.created_at ? formatDate(call.created_at) : '—'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">From</p>
              <p className="font-mono text-sm">{call.from_phone || '—'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">To</p>
              <p className="font-mono text-sm">{call.to_phone || '—'}</p>
            </div>
          </div>

          {/* Recording */}
          {call.recording_url && (
            <div className="mt-4 pt-4 border-t">
              <p className="text-sm text-gray-500 mb-2">Recording</p>
              <div className="flex items-center gap-3">
                <audio controls src={call.recording_url} className="flex-1" />
                <a href={call.recording_url} download>
                  <Button variant="outline" size="sm"><Download size={14} /></Button>
                </a>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex gap-2">
        <Button
          onClick={() => triggerExtraction.mutate(call.id)}
          disabled={triggerExtraction.isPending}
        >
          <Database size={16} className="mr-2" /> Extract Data
        </Button>
      </div>

      {/* Transcript */}
      <Card>
        <CardHeader><CardTitle>Transcript</CardTitle></CardHeader>
        <CardContent>
          {transcript ? (
            <div className="space-y-3">
              {transcript.segments && transcript.segments.length > 0 ? (
                transcript.segments.map((seg: any, i: number) => (
                  <div key={i} className={`flex gap-3 ${seg.role === 'agent' ? '' : 'flex-row-reverse'}`}>
                    <div
                      className={`max-w-[70%] rounded-lg px-4 py-2 text-sm ${
                        seg.role === 'agent'
                          ? 'bg-primary-50 text-primary-900'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <p className="text-xs font-medium mb-1 opacity-70">
                        {seg.role === 'agent' ? 'AI Agent' : 'Caller'}
                      </p>
                      <p>{seg.text}</p>
                    </div>
                  </div>
                ))
              ) : transcript.full_text ? (
                <pre className="whitespace-pre-wrap text-sm">{transcript.full_text}</pre>
              ) : (
                <p className="text-gray-500 text-sm">No transcript available yet.</p>
              )}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No transcript available.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
