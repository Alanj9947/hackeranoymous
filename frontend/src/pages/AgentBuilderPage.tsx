import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAgent, useCreateAgent, useUpdateAgent } from '@/hooks/use-api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { PageLoader } from '@/components/ui/Spinner';
import { ArrowLeft, Save } from 'lucide-react';
import { AxiosError } from 'axios';
import toast from 'react-hot-toast';

interface FormData {
  name: string;
  description: string;
  language: string;
  system_prompt: { role: string; personality: string; instructions: string; greeting: string };
  voice_settings: { provider: string; voice_id: string; speed: number; pitch: number };
  call_settings: { max_duration: number; silence_timeout: number; recording_enabled: boolean };
  data_extraction: { enabled: boolean; extract_after_call: boolean; fields: Record<string, string> };
}

const defaultForm: FormData = {
  name: '',
  description: '',
  language: 'en-US',
  system_prompt: {
    role: 'Customer Support Agent',
    personality: 'Professional, friendly, and helpful',
    instructions: 'Help the customer with their inquiry. Be concise and accurate.',
    greeting: 'Hello! How can I help you today?',
  },
  voice_settings: { provider: 'elevenlabs', voice_id: '', speed: 1.0, pitch: 1.0 },
  call_settings: { max_duration: 600, silence_timeout: 30, recording_enabled: true },
  data_extraction: {
    enabled: true,
    extract_after_call: true,
    fields: { customer_name: 'string', issue_summary: 'string', resolution: 'string', satisfaction: 'number' },
  },
};

export default function AgentBuilderPage() {
  const { id } = useParams();
  const isEdit = !!id;
  const navigate = useNavigate();
  const { data: existingAgent, isLoading } = useAgent(id);
  const createAgent = useCreateAgent();
  const updateAgent = useUpdateAgent();

  const [form, setForm] = useState<FormData>(defaultForm);
  const [activeTab, setActiveTab] = useState('general');

  useEffect(() => {
    if (existingAgent) {
      setForm({
        name: existingAgent.name || '',
        description: existingAgent.description || '',
        language: existingAgent.system_prompt?.language || existingAgent.language || 'en-US',
        system_prompt: existingAgent.system_prompt || defaultForm.system_prompt,
        voice_settings: existingAgent.voice_settings || defaultForm.voice_settings,
        call_settings: existingAgent.call_settings || defaultForm.call_settings,
        data_extraction: existingAgent.data_extraction || defaultForm.data_extraction,
      });
    }
  }, [existingAgent]);

  if (isEdit && isLoading) return <PageLoader />;

  const handleSave = async () => {
    if (!form.name.trim()) {
      toast.error('Agent name is required');
      return;
    }
    // Map top-level language into system_prompt.language for the backend
    const payload = {
      ...form,
      system_prompt: { ...form.system_prompt, language: form.language },
    };
    try {
      if (isEdit) {
        await updateAgent.mutateAsync({ id: id!, data: payload });
      } else {
        await createAgent.mutateAsync(payload);
      }
      navigate('/agents');
    } catch (err: unknown) {
      const message = err instanceof AxiosError ? err.response?.data?.detail : 'Failed to save agent';
      toast.error(message || 'Failed to save agent');
    }
  };

  const tabs = [
    { key: 'general', label: 'General' },
    { key: 'prompt', label: 'System Prompt' },
    { key: 'voice', label: 'Voice' },
    { key: 'call', label: 'Call Settings' },
    { key: 'extraction', label: 'Data Extraction' },
  ];

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/agents')}>
          <ArrowLeft size={20} />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">{isEdit ? 'Edit Agent' : 'New Agent'}</h1>
          <p className="text-gray-500">Configure your voice agent</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'general' && (
        <Card>
          <CardHeader><CardTitle>General Information</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Agent Name *</label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Support Agent" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Brief description of this agent's purpose" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Language</label>
              <select
                className="w-full h-10 rounded-md border border-gray-300 px-3 text-sm"
                value={form.language}
                onChange={(e) => setForm({ ...form, language: e.target.value })}
              >
                <option value="en-US">English (US)</option>
                <option value="en-GB">English (UK)</option>
                <option value="es-ES">Spanish</option>
                <option value="fr-FR">French</option>
                <option value="de-DE">German</option>
              </select>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'prompt' && (
        <Card>
          <CardHeader><CardTitle>System Prompt</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Role</label>
              <Input
                value={form.system_prompt.role}
                onChange={(e) => setForm({ ...form, system_prompt: { ...form.system_prompt, role: e.target.value } })}
                placeholder="Customer Support Agent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Personality</label>
              <Textarea
                value={form.system_prompt.personality}
                onChange={(e) => setForm({ ...form, system_prompt: { ...form.system_prompt, personality: e.target.value } })}
                placeholder="Professional, friendly, and helpful"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Instructions</label>
              <Textarea
                value={form.system_prompt.instructions}
                onChange={(e) => setForm({ ...form, system_prompt: { ...form.system_prompt, instructions: e.target.value } })}
                rows={4}
                placeholder="Detailed instructions for this agent..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Greeting Message</label>
              <Input
                value={form.system_prompt.greeting}
                onChange={(e) => setForm({ ...form, system_prompt: { ...form.system_prompt, greeting: e.target.value } })}
                placeholder="Hello! How can I help you today?"
              />
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'voice' && (
        <Card>
          <CardHeader><CardTitle>Voice Settings</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">TTS Provider</label>
              <select
                className="w-full h-10 rounded-md border border-gray-300 px-3 text-sm"
                value={form.voice_settings.provider}
                onChange={(e) => setForm({ ...form, voice_settings: { ...form.voice_settings, provider: e.target.value } })}
              >
                <option value="elevenlabs">ElevenLabs</option>
                <option value="openai">OpenAI</option>
                <option value="azure">Azure</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Voice ID</label>
              <Input
                value={form.voice_settings.voice_id}
                onChange={(e) => setForm({ ...form, voice_settings: { ...form.voice_settings, voice_id: e.target.value } })}
                placeholder="Enter voice ID from your TTS provider"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Speed ({form.voice_settings.speed}x)</label>
                <input
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                  value={form.voice_settings.speed}
                  onChange={(e) => setForm({ ...form, voice_settings: { ...form.voice_settings, speed: parseFloat(e.target.value) } })}
                  className="w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Pitch ({form.voice_settings.pitch}x)</label>
                <input
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                  value={form.voice_settings.pitch}
                  onChange={(e) => setForm({ ...form, voice_settings: { ...form.voice_settings, pitch: parseFloat(e.target.value) } })}
                  className="w-full"
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'call' && (
        <Card>
          <CardHeader><CardTitle>Call Settings</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Max Duration (seconds)</label>
              <Input
                type="number"
                value={form.call_settings.max_duration}
                onChange={(e) => setForm({ ...form, call_settings: { ...form.call_settings, max_duration: parseInt(e.target.value) } })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Silence Timeout (seconds)</label>
              <Input
                type="number"
                value={form.call_settings.silence_timeout}
                onChange={(e) => setForm({ ...form, call_settings: { ...form.call_settings, silence_timeout: parseInt(e.target.value) } })}
              />
            </div>
            <div className="flex items-center gap-3">
              <input
                id="recording"
                type="checkbox"
                checked={form.call_settings.recording_enabled}
                onChange={(e) => setForm({ ...form, call_settings: { ...form.call_settings, recording_enabled: e.target.checked } })}
                className="h-4 w-4 rounded border-gray-300"
              />
              <label htmlFor="recording" className="text-sm font-medium">Enable call recording</label>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'extraction' && (
        <Card>
          <CardHeader><CardTitle>Data Extraction</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <input
                id="extraction-enabled"
                type="checkbox"
                checked={form.data_extraction.enabled}
                onChange={(e) => setForm({ ...form, data_extraction: { ...form.data_extraction, enabled: e.target.checked } })}
                className="h-4 w-4 rounded border-gray-300"
              />
              <label htmlFor="extraction-enabled" className="text-sm font-medium">Enable data extraction</label>
            </div>
            <div className="flex items-center gap-3">
              <input
                id="extract-after"
                type="checkbox"
                checked={form.data_extraction.extract_after_call}
                onChange={(e) => setForm({ ...form, data_extraction: { ...form.data_extraction, extract_after_call: e.target.checked } })}
                className="h-4 w-4 rounded border-gray-300"
              />
              <label htmlFor="extract-after" className="text-sm font-medium">Auto-extract after each call</label>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Extraction Fields (JSON)</label>
              <Textarea
                rows={6}
                value={JSON.stringify(form.data_extraction.fields, null, 2)}
                onChange={(e) => {
                  try {
                    const fields = JSON.parse(e.target.value);
                    setForm({ ...form, data_extraction: { ...form.data_extraction, fields } });
                  } catch { /* invalid JSON, let user keep typing */ }
                }}
              />
              <p className="text-xs text-gray-400 mt-1">Define field names and their types (string, number, boolean, array)</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Save button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={createAgent.isPending || updateAgent.isPending}>
          <Save size={18} className="mr-2" />
          {isEdit ? 'Update Agent' : 'Create Agent'}
        </Button>
      </div>
    </div>
  );
}
