import { useState } from 'react';
import {
  useExportExcel,
  useExportSheets,
  useExportHistory,
  useScheduledExports,
  useCreateScheduledExport,
  useAgents,
} from '@/hooks/use-api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { PageLoader } from '@/components/ui/Spinner';
import { FileSpreadsheet, Table2, Download, Plus } from 'lucide-react';
import { formatDate } from '@/lib/utils';
import { AxiosError } from 'axios';
import toast from 'react-hot-toast';

export default function ExportsPage() {
  const { data: agents } = useAgents();
  const exportExcel = useExportExcel();
  const exportSheets = useExportSheets();
  const { data: history, isLoading: histLoading } = useExportHistory();
  const { data: schedules } = useScheduledExports();
  const createSchedule = useCreateScheduledExport();

  const [tab, setTab] = useState<'export' | 'history' | 'scheduled'>('export');
  const [agentId, setAgentId] = useState('');
  const [template, setTemplate] = useState('customer_service_summary');
  const [sheetTitle, setSheetTitle] = useState('');
  const [shareEmail, setShareEmail] = useState('');
  const [scheduleFreq, setScheduleFreq] = useState('daily');

  const agentList = agents || [];
  const historyList = history || [];
  const scheduleList = schedules || [];

  const handleExcelExport = async () => {
    try {
      await exportExcel.mutateAsync({
        agent_id: agentId || undefined,
        template,
        date_range: { days: 30 },
      });
    } catch (err: unknown) {
      const message = err instanceof AxiosError ? err.response?.data?.detail : 'Export failed';
      toast.error(message || 'Export failed');
    }
  };

  const handleSheetsExport = async () => {
    try {
      await exportSheets.mutateAsync({
        agent_id: agentId || undefined,
        spreadsheet_title: sheetTitle || 'Voice Agent Export',
        share_with: shareEmail ? [shareEmail] : [],
      });
    } catch (err: unknown) {
      const message = err instanceof AxiosError ? err.response?.data?.detail : 'Export failed';
      toast.error(message || 'Export failed');
    }
  };

  const handleCreateSchedule = async () => {
    try {
      await createSchedule.mutateAsync({
        name: `${scheduleFreq} export`,
        frequency: scheduleFreq,
        destination: 'excel',
        agent_id: agentId || undefined,
        template,
      });
    } catch (err: unknown) {
      const message = err instanceof AxiosError ? err.response?.data?.detail : 'Failed to create schedule';
      toast.error(message || 'Failed to create schedule');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Exports</h1>
        <p className="text-gray-500">Export call data to Excel or Google Sheets</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b">
        {[
          { key: 'export', label: 'New Export' },
          { key: 'history', label: 'History' },
          { key: 'scheduled', label: 'Scheduled' },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key as any)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t.key ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'export' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Excel Export */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileSpreadsheet size={18} className="text-green-600" /> Excel Export
              </CardTitle>
              <CardDescription>Download as .xlsx file</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Agent (optional)</label>
                <select
                  className="w-full h-10 rounded-md border border-gray-300 px-3 text-sm"
                  value={agentId}
                  onChange={(e) => setAgentId(e.target.value)}
                >
                  <option value="">All agents</option>
                  {agentList.map((a: any) => (
                    <option key={a.id} value={a.id}>{a.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Template</label>
                <select
                  className="w-full h-10 rounded-md border border-gray-300 px-3 text-sm"
                  value={template}
                  onChange={(e) => setTemplate(e.target.value)}
                >
                  <option value="customer_service_summary">Customer Service Summary</option>
                  <option value="sales_call_analysis">Sales Call Analysis</option>
                  <option value="recruitment_calls">Recruitment Calls</option>
                </select>
              </div>
              <Button onClick={handleExcelExport} disabled={exportExcel.isPending} className="w-full">
                <Download size={16} className="mr-2" />
                {exportExcel.isPending ? 'Exporting…' : 'Export to Excel'}
              </Button>
            </CardContent>
          </Card>

          {/* Google Sheets Export */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Table2 size={18} className="text-blue-600" /> Google Sheets
              </CardTitle>
              <CardDescription>Export directly to Google Sheets</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Spreadsheet Title</label>
                <Input
                  value={sheetTitle}
                  onChange={(e) => setSheetTitle(e.target.value)}
                  placeholder="Voice Agent Export"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Share with (email)</label>
                <Input
                  type="email"
                  value={shareEmail}
                  onChange={(e) => setShareEmail(e.target.value)}
                  placeholder="team@company.com"
                />
              </div>
              <Button onClick={handleSheetsExport} disabled={exportSheets.isPending} className="w-full">
                <Table2 size={16} className="mr-2" />
                {exportSheets.isPending ? 'Exporting…' : 'Export to Sheets'}
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {tab === 'history' && (
        <Card>
          <CardContent className="p-0">
            {histLoading ? (
              <PageLoader />
            ) : historyList.length === 0 ? (
              <div className="p-12 text-center text-gray-500">No export history yet</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50 text-left text-gray-500">
                      <th className="p-3 font-medium">Type</th>
                      <th className="p-3 font-medium">Status</th>
                      <th className="p-3 font-medium">Rows</th>
                      <th className="p-3 font-medium">Date</th>
                      <th className="p-3 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historyList.map((h: any) => (
                      <tr key={h.id} className="border-b last:border-0">
                        <td className="p-3">{h.export_type}</td>
                        <td className="p-3">
                          <Badge variant={h.status === 'completed' ? 'success' : 'warning'}>{h.status}</Badge>
                        </td>
                        <td className="p-3">{h.row_count || '—'}</td>
                        <td className="p-3 text-gray-500">{h.created_at && formatDate(h.created_at)}</td>
                        <td className="p-3">
                          {h.file_path && (
                            <Button variant="ghost" size="sm">
                              <Download size={14} className="mr-1" /> Download
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {tab === 'scheduled' && (
        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Create Schedule</CardTitle></CardHeader>
            <CardContent className="flex items-end gap-4">
              <div className="flex-1">
                <label className="block text-sm font-medium mb-1">Frequency</label>
                <select
                  className="w-full h-10 rounded-md border border-gray-300 px-3 text-sm"
                  value={scheduleFreq}
                  onChange={(e) => setScheduleFreq(e.target.value)}
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
              <Button onClick={handleCreateSchedule} disabled={createSchedule.isPending}>
                <Plus size={16} className="mr-2" /> Create
              </Button>
            </CardContent>
          </Card>

          {scheduleList.length > 0 && (
            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-gray-50 text-left text-gray-500">
                        <th className="p-3 font-medium">Name</th>
                        <th className="p-3 font-medium">Frequency</th>
                        <th className="p-3 font-medium">Destination</th>
                        <th className="p-3 font-medium">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {scheduleList.map((s: any) => (
                        <tr key={s.id} className="border-b last:border-0">
                          <td className="p-3">{s.name}</td>
                          <td className="p-3">{s.frequency}</td>
                          <td className="p-3">{s.destination}</td>
                          <td className="p-3">
                            <Badge variant={s.is_active ? 'success' : 'outline'}>
                              {s.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
