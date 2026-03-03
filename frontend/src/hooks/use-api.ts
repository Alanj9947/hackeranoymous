import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import toast from 'react-hot-toast';

// Shared types that mirror backend schemas
type UUID = string;

type User = {
  id: UUID;
  email: string;
  full_name: string;
  role: string;
  company_id: UUID;
  company_name?: string | null;
  is_active: boolean;
  avatar_url?: string | null;
};

type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
};

type Agent = {
  id: UUID;
  company_id: UUID;
  name: string;
  description?: string | null;
  status: string;
  system_prompt: Record<string, unknown>;
  voice_settings: Record<string, unknown>;
  call_settings: Record<string, unknown>;
  data_extraction: Record<string, unknown>;
  phone_numbers?: string[] | null;
  total_calls: number;
  total_minutes: number;
  created_at?: string | null;
  updated_at?: string | null;
};

type AgentListResponse = {
  agents: Agent[];
  total: number;
  page: number;
  per_page: number;
};

type AgentCreateInput = Partial<Omit<Agent, 'id' | 'company_id' | 'total_calls' | 'total_minutes'>>;

type Call = {
  id: UUID;
  company_id: UUID;
  agent_id: UUID;
  twilio_call_sid?: string | null;
  direction: string;
  from_number?: string | null;
  to_number?: string | null;
  status: string;
  started_at?: string | null;
  ended_at?: string | null;
  duration_seconds?: number | null;
  recording_url?: string | null;
  stt_model?: string | null;
  llm_model?: string | null;
  tts_model?: string | null;
  ai_cost_usd?: number | null;
  metadata_json?: Record<string, unknown> | null;
  created_at?: string | null;
};

type CallListResponse = {
  calls: Call[];
  total: number;
  page: number;
  per_page: number;
};

type Transcript = {
  id: UUID;
  call_id: UUID;
  full_text: string;
  segments?: Record<string, unknown>[] | null;
  language?: string | null;
  word_count?: number | null;
};

type ExtractionItem = {
  id: UUID;
  call_id: UUID;
  company_id: UUID;
  agent_id: UUID;
  extraction_method?: string | null;
  model_used?: string | null;
  processing_time_ms?: number | null;
  confidence_score?: number | null;
  extracted_data: Record<string, unknown>;
  reviewed: boolean;
  approved?: boolean | null;
  quality_comments?: string | null;
  exported: boolean;
  export_destinations?: Record<string, unknown> | null;
  created_at?: string | null;
};

type ExtractionListResponse = {
  items: ExtractionItem[];
  total: number;
  page: number;
  per_page: number;
};

type ExtractionTriggerResponse = {
  job_id: UUID;
  call_id: UUID;
  status: string;
  estimated_wait_time: number;
  message: string;
};

type ExportResponse = {
  job_id: UUID;
  status: string;
  estimated_completion_time?: number | null;
  download_url?: string | null;
  spreadsheet_url?: string | null;
  rows_exported?: number | null;
};

type ExportHistoryEntry = {
  id: UUID;
  export_type: string;
  destination: string;
  rows_exported?: number | null;
  file_path?: string | null;
  status: string;
  error_message?: string | null;
  completed_at?: string | null;
  duration_ms?: number | null;
  created_at?: string | null;
};

type ScheduledExport = {
  id: UUID;
  name: string;
  description?: string | null;
  frequency: string;
  scheduled_time?: string | null;
  destination: string;
  template_name?: string | null;
  enabled: boolean;
  last_run_at?: string | null;
  next_run_at?: string | null;
  last_run_status?: string | null;
  run_count: number;
  created_at?: string | null;
};

type CustomServerConfig = {
  id: UUID;
  company_id: UUID;
  agent_id?: UUID | null;
  endpoint: string;
  model_name?: string | null;
  timeout_seconds: number;
  max_retries: number;
  enabled: boolean;
  health_status?: string | null;
  last_health_check?: string | null;
  last_response_time_ms?: number | null;
  fallback_to_openai: boolean;
};

type CustomServerHealth = {
  status: string;
  endpoint: string;
  last_check?: string | null;
  response_time?: number | null;
  model_loaded?: string | null;
  models_available?: string[] | null;
  gpu_available?: boolean | null;
  gpu_memory_usage?: string | null;
  request_queue_depth?: number | null;
  uptime?: string | null;
};

// ─── Auth ───────────────────────────────────────────────────

export function useLogin() {
  return useMutation({
    mutationFn: (data: { email: string; password: string }) =>
      api.post<LoginResponse>('/auth/login', data).then((r) => r.data),
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: (data: { email: string; password: string; full_name: string; company_name: string }) =>
      api.post<LoginResponse>('/auth/register', data).then((r) => r.data),
  });
}

export function useCurrentUser() {
  return useQuery({
    queryKey: ['me'],
    queryFn: () => api.get<User>('/auth/me').then((r) => r.data),
  });
}

// ─── Agents ─────────────────────────────────────────────────

export function useAgents(page = 1, limit = 20) {
  return useQuery<Agent[]>({
    queryKey: ['agents', page, limit],
    queryFn: () =>
      api
        .get<AgentListResponse>('/agents', { params: { page, per_page: limit } })
        .then((r) => r.data.agents),
  });
}

export function useAgent(id: string | undefined) {
  return useQuery<Agent>({
    queryKey: ['agent', id],
    queryFn: () => api.get<Agent>(`/agents/${id}`).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: AgentCreateInput) => api.post<Agent>('/agents', data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['agents'] });
      toast.success('Agent created');
    },
  });
}

export function useUpdateAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AgentCreateInput }) =>
      api.put<Agent>(`/agents/${id}`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['agents'] });
      toast.success('Agent updated');
    },
  });
}

export function useDeleteAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/agents/${id}`).then(() => undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['agents'] });
      toast.success('Agent deleted');
    },
  });
}

// ─── Calls ──────────────────────────────────────────────────

export function useCalls(page = 1, limit = 20, agentId?: string) {
  return useQuery<Call[]>({
    queryKey: ['calls', page, limit, agentId],
    queryFn: () =>
      api
        .get<CallListResponse>('/calls', {
          params: { page, per_page: limit, agent_id: agentId },
        })
        .then((r) => r.data.calls),
  });
}

export function useCall(id: string | undefined) {
  return useQuery<Call>({
    queryKey: ['call', id],
    queryFn: () => api.get<Call>(`/calls/${id}`).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCallTranscript(callId: string | undefined) {
  return useQuery<Transcript>({
    queryKey: ['callTranscript', callId],
    queryFn: () => api.get<Transcript>(`/calls/${callId}/transcript`).then((r) => r.data),
    enabled: !!callId,
  });
}

export function useInitiateCall() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { agent_id: string; to_number: string; direction?: string; metadata_json?: Record<string, unknown> }) =>
      api
        .post<Call>('/calls', {
          direction: data.direction ?? 'outbound',
          agent_id: data.agent_id,
          to_number: data.to_number,
          metadata_json: data.metadata_json,
        })
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['calls'] });
      toast.success('Call initiated');
    },
  });
}

// ─── Extraction ─────────────────────────────────────────────

export function useExtractions(page = 1, limit = 20) {
  return useQuery<ExtractionItem[]>({
    queryKey: ['extractions', page, limit],
    queryFn: () =>
      api
        .get<ExtractionListResponse>('/extract-data', {
          params: { page, per_page: limit },
        })
        .then((r) => r.data.items),
  });
}

export function useTriggerExtraction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (callId: string) => api.post<ExtractionTriggerResponse>(`/extract-data/${callId}`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['extractions'] });
      toast.success('Extraction started');
    },
  });
}

export function useReviewExtraction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: { approved: boolean; comments?: string; reviewed?: boolean };
    }) =>
      api
        .put<ExtractionItem>(`/extract-data/${id}/review`, {
          approved: data.approved,
          comments: data.comments,
        })
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['extractions'] });
      toast.success('Review saved');
    },
  });
}

// ─── Exports ────────────────────────────────────────────────

export function useExportExcel() {
  return useMutation({
    mutationFn: (data: { call_ids?: UUID[]; template?: string; include_charts?: boolean; filename?: string }) =>
      api
        .post<ExportResponse>('/export/excel', {
          call_ids: data.call_ids ?? [],
          template: data.template ?? 'customer_service_summary',
          include_charts: data.include_charts ?? false,
          filename: data.filename,
        })
        .then((r) => r.data),
    onSuccess: () => toast.success('Excel export started'),
  });
}

export function useExportSheets() {
  return useMutation({
    mutationFn: (data: { call_ids?: UUID[]; spreadsheet_id?: string; action?: string; template?: string; share_with?: string[] }) =>
      api
        .post<ExportResponse>('/export/sheets', {
          call_ids: data.call_ids ?? [],
          spreadsheet_id: data.spreadsheet_id,
          action: data.action ?? 'append',
          template: data.template ?? 'customer_service_summary',
          share_with: data.share_with,
        })
        .then((r) => r.data),
    onSuccess: () => toast.success('Sheets export started'),
  });
}

export function useExportHistory(page = 1, limit = 20) {
  return useQuery<ExportHistoryEntry[]>({
    queryKey: ['exportHistory', page, limit],
    queryFn: () =>
      api
        .get<ExportHistoryEntry[]>('/export/history', { params: { page, per_page: limit } })
        .then((r) => r.data),
  });
}

export function useScheduledExports() {
  return useQuery<ScheduledExport[]>({
    queryKey: ['scheduledExports'],
    queryFn: () => api.get<ScheduledExport[]>('/export/schedules').then((r) => r.data),
  });
}

export function useCreateScheduledExport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      name: string;
      description?: string;
      frequency: string;
      scheduled_time?: string;
      days_of_week?: number[];
      day_of_month?: number;
      destination: string;
      destination_config?: Record<string, unknown>;
      template?: string;
      columns_to_export?: string[];
      filters?: Record<string, unknown>;
      agent_id?: string;
    }) =>
      api
        .post<ScheduledExport>('/export/schedule', {
          name: data.name,
          description: data.description,
          frequency: data.frequency,
          scheduled_time: data.scheduled_time ?? '09:00',
          days_of_week: data.days_of_week,
          day_of_month: data.day_of_month,
          destination: data.destination,
          destination_config: data.destination_config,
          template: data.template ?? 'customer_service_summary',
          columns_to_export: data.columns_to_export,
          filters: data.filters,
          agent_id: data.agent_id,
        })
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['scheduledExports'] });
      toast.success('Schedule created');
    },
  });
}

// ─── Custom Server ──────────────────────────────────────────

export function useCustomServerConfig() {
  return useQuery<CustomServerConfig>({
    queryKey: ['customServer'],
    queryFn: () => api.get<CustomServerConfig>('/custom-server/config').then((r) => r.data),
    retry: false,
  });
}

export function useSaveCustomServerConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { endpoint: string; api_key: string; model_name?: string; timeout_seconds?: number; max_retries?: number }) =>
      api.post<CustomServerConfig>('/custom-server/config', data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['customServer'] });
      toast.success('Server config saved');
    },
  });
}

export function useCustomServerHealth() {
  return useQuery<CustomServerHealth>({
    queryKey: ['customServerHealth'],
    queryFn: () => api.get<CustomServerHealth>('/custom-server/health').then((r) => r.data),
    retry: false,
    refetchInterval: 30_000,
  });
}
