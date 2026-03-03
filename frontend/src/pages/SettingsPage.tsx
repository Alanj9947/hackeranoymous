import { useState } from 'react';
import { useCustomServerConfig, useSaveCustomServerConfig, useCustomServerHealth } from '@/hooks/use-api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { Server, Shield, RefreshCw, Save, Activity } from 'lucide-react';
import { AxiosError } from 'axios';
import toast from 'react-hot-toast';

export default function SettingsPage() {
  const { data: config, isLoading: configLoading } = useCustomServerConfig();
  const saveConfig = useSaveCustomServerConfig();
  const { data: health, isLoading: healthLoading, refetch: refetchHealth } = useCustomServerHealth();

  const [endpoint, setEndpoint] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [modelName, setModelName] = useState('llama3.1:8b');
  const [timeout, setTimeout] = useState(120);
  const [maxRetries, setMaxRetries] = useState(2);
  const [initialized, setInitialized] = useState(false);

  // Populate form from existing config once
  if (config && !initialized) {
    setEndpoint(config.endpoint || '');
    setModelName(config.model_name || 'llama3.1:8b');
    setTimeout(config.timeout_seconds || 120);
    setMaxRetries(config.max_retries || 2);
    setInitialized(true);
  }

  const handleSave = async () => {
    if (!endpoint.trim()) {
      toast.error('Server endpoint is required');
      return;
    }
    try {
      await saveConfig.mutateAsync({
        endpoint: endpoint.trim(),
        api_key: apiKey || '',
        model_name: modelName,
        timeout_seconds: timeout,
        max_retries: maxRetries,
      });
      setApiKey(''); // Clear after save
    } catch (err: unknown) {
      const message = err instanceof AxiosError ? err.response?.data?.detail : 'Failed to save';
      toast.error(message || 'Failed to save');
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-gray-500">Configure your AI server and platform settings</p>
      </div>

      {/* Custom AI Server */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server size={18} /> Custom AI Server (VPS)
          </CardTitle>
          <CardDescription>
            Connect your dedicated AI server running Ollama + FastAPI for data extraction
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Server Endpoint *</label>
            <Input
              value={endpoint}
              onChange={(e) => setEndpoint(e.target.value)}
              placeholder="https://your-vps-ip:8100"
            />
            <p className="text-xs text-gray-400 mt-1">Full URL to your VPS AI server</p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">API Key</label>
            <Input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={config ? '••••••• (leave blank to keep existing)' : 'your-api-key'}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Model Name</label>
            <Input
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              placeholder="llama3.1:8b"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Timeout (seconds)</label>
              <Input
                type="number"
                value={timeout}
                onChange={(e) => setTimeout(parseInt(e.target.value))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Max Retries</label>
              <Input
                type="number"
                value={maxRetries}
                onChange={(e) => setMaxRetries(parseInt(e.target.value))}
              />
            </div>
          </div>

          <Button onClick={handleSave} disabled={saveConfig.isPending}>
            <Save size={16} className="mr-2" />
            {saveConfig.isPending ? 'Saving…' : 'Save Configuration'}
          </Button>
        </CardContent>
      </Card>

      {/* Server Health */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity size={18} /> Server Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          {configLoading || healthLoading ? (
            <div className="flex items-center gap-2">
              <Spinner size={18} /> Checking...
            </div>
          ) : health ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Badge variant={health.status === 'healthy' ? 'success' : 'destructive'}>
                  {health.status}
                </Badge>
                <span className="text-sm text-gray-500">Response time: {health.response_time}ms</span>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Ollama Connected</p>
                  <p className="font-medium">{health.ollama_connected ? 'Yes' : 'No'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Model Loaded</p>
                  <p className="font-medium">{health.model_loaded ? 'Yes' : 'No'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Model</p>
                  <p className="font-medium">{health.model_name || '—'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Active Requests</p>
                  <p className="font-medium">{health.active_requests ?? '—'}</p>
                </div>
              </div>

              <Button variant="outline" size="sm" onClick={() => refetchHealth()}>
                <RefreshCw size={14} className="mr-2" /> Refresh
              </Button>
            </div>
          ) : (
            <div className="text-sm text-gray-500">
              {config ? 'Unable to reach server. Check the endpoint.' : 'No server configured yet.'}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Security */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield size={18} /> Security
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-gray-500">
          <ul className="space-y-2">
            <li>• API keys are encrypted at rest using Fernet encryption</li>
            <li>• JWT tokens expire after 30 minutes (access) and 7 days (refresh)</li>
            <li>• All API communications use HTTPS in production</li>
            <li>• Twilio webhooks are validated with request signatures</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
