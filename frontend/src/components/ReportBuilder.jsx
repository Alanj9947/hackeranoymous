import React, { useState, useEffect } from 'react';
import {
  FileText, Plus, Trash2, Download, Clock, Settings,
  CheckCircle, AlertCircle, Loader
} from 'lucide-react';

/**
 * Report Builder Component - Generate and schedule reports.
 */
function ReportBuilder({ companyId = 'default' }) {
  const [templates, setTemplates] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState('generate'); // generate | schedule
  const [generating, setGenerating] = useState(false);
  const [deleting, setDeleting] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    template: '',
    format: 'pdf',
    days: 7
  });

  const [scheduleForm, setScheduleForm] = useState({
    template: '',
    frequency: 'weekly',
    recipients: '',
    format: 'pdf'
  });

  // Load templates and schedules
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [templatesRes, schedulesRes] = await Promise.all([
        fetch('/api/v1/reports/templates'),
        fetch('/api/v1/reports/schedules')
      ]);

      if (!templatesRes.ok || !schedulesRes.ok) {
        throw new Error('Failed to load report data');
      }

      const templatesData = await templatesRes.json();
      const schedulesData = await schedulesRes.json();

      setTemplates(Object.entries(templatesData.templates).map(([key, value]) => ({
        id: key,
        ...value
      })));
      setSchedules(schedulesData.schedules);

      if (templatesData.templates) {
        const firstTemplate = Object.keys(templatesData.templates)[0];
        setFormData(prev => ({ ...prev, template: firstTemplate }));
        setScheduleForm(prev => ({ ...prev, template: firstTemplate }));
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async (e) => {
    e.preventDefault();
    setGenerating(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        template: formData.template,
        format: formData.format,
        days: formData.days
      });

      const response = await fetch(`/api/v1/reports/generate?${params}`);

      if (!response.ok) {
        throw new Error('Failed to generate report');
      }

      // For PDF/CSV, trigger download
      if (formData.format === 'pdf' || formData.format === 'csv') {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `report-${Date.now()}.${formData.format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        // For JSON/HTML, show in new tab
        const data = await response.json();
        const newWindow = window.open();
        newWindow.document.write(JSON.stringify(data, null, 2));
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  };

  const createSchedule = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      const recipients = scheduleForm.recipients
        .split(',')
        .map(r => r.trim())
        .filter(r => r);

      if (recipients.length === 0) {
        setError('At least one recipient email is required');
        return;
      }

      const response = await fetch('/api/v1/reports/schedules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template: scheduleForm.template,
          frequency: scheduleForm.frequency,
          recipients,
          format: scheduleForm.format
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create schedule');
      }

      const newSchedule = await response.json();
      setSchedules([...schedules, newSchedule]);
      setScheduleForm({
        template: scheduleForm.template,
        frequency: 'weekly',
        recipients: '',
        format: 'pdf'
      });
    } catch (err) {
      setError(err.message);
    }
  };

  const deleteSchedule = async (scheduleId) => {
    setDeleting(scheduleId);
    setError(null);

    try {
      const response = await fetch(`/api/v1/reports/schedules/${scheduleId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete schedule');
      }

      setSchedules(schedules.filter(s => s.schedule_id !== scheduleId));
    } catch (err) {
      setError(err.message);
    } finally {
      setDeleting(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Report Builder</h1>
          <p className="text-gray-500 mt-1">Generate custom reports and schedule automated delivery</p>
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
            onClick={() => setTab('generate')}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              tab === 'generate'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Download className="w-4 h-4 inline mr-2" />
            Generate Report
          </button>
          <button
            onClick={() => setTab('schedule')}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              tab === 'schedule'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Clock className="w-4 h-4 inline mr-2" />
            Scheduled Reports
          </button>
        </div>

        {tab === 'generate' ? (
          // Generate Report Tab
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Form */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-6">Generate Report</h2>

                <form onSubmit={generateReport} className="space-y-4">
                  {/* Template Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Template
                    </label>
                    <select
                      value={formData.template}
                      onChange={(e) => setFormData(prev => ({ ...prev, template: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {templates.map(tmpl => (
                        <option key={tmpl.id} value={tmpl.id}>
                          {tmpl.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Format Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Format
                    </label>
                    <select
                      value={formData.format}
                      onChange={(e) => setFormData(prev => ({ ...prev, format: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="pdf">PDF</option>
                      <option value="csv">CSV</option>
                      <option value="json">JSON</option>
                      <option value="html">HTML</option>
                    </select>
                  </div>

                  {/* Days Range */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Time Period (days)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="365"
                      value={formData.days}
                      onChange={(e) => setFormData(prev => ({ ...prev, days: parseInt(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Reports data from the last {formData.days} days
                    </p>
                  </div>

                  {/* Submit */}
                  <button
                    type="submit"
                    disabled={generating || !formData.template}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                  >
                    {generating ? (
                      <>
                        <Loader className="w-4 h-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Download className="w-4 h-4" />
                        Generate Report
                      </>
                    )}
                  </button>
                </form>
              </div>
            </div>

            {/* Templates Grid */}
            <div className="lg:col-span-2">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {templates.map(tmpl => (
                  <div key={tmpl.id} className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start gap-3">
                      <FileText className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">{tmpl.name}</h3>
                        <p className="text-sm text-gray-600 mt-1">
                          Type: {tmpl.report_type}
                        </p>
                        <p className="text-sm text-gray-600 mt-1">
                          {tmpl.sections?.length || 0} sections
                        </p>
                        {tmpl.include_charts && (
                          <p className="text-xs text-green-600 mt-2">✓ Includes charts</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          // Schedule Reports Tab
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Schedule Form */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-6">Schedule Report</h2>

                <form onSubmit={createSchedule} className="space-y-4">
                  {/* Template */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Template
                    </label>
                    <select
                      value={scheduleForm.template}
                      onChange={(e) => setScheduleForm(prev => ({ ...prev, template: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {templates.map(tmpl => (
                        <option key={tmpl.id} value={tmpl.id}>
                          {tmpl.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Frequency */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Frequency
                    </label>
                    <select
                      value={scheduleForm.frequency}
                      onChange={(e) => setScheduleForm(prev => ({ ...prev, frequency: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                    </select>
                  </div>

                  {/* Format */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Format
                    </label>
                    <select
                      value={scheduleForm.format}
                      onChange={(e) => setScheduleForm(prev => ({ ...prev, format: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="pdf">PDF</option>
                      <option value="csv">CSV</option>
                      <option value="json">JSON</option>
                      <option value="html">HTML</option>
                    </select>
                  </div>

                  {/* Recipients */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Recipients
                    </label>
                    <textarea
                      value={scheduleForm.recipients}
                      onChange={(e) => setScheduleForm(prev => ({ ...prev, recipients: e.target.value }))}
                      placeholder="email@example.com&#10;other@example.com"
                      rows="3"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      One email per line
                    </p>
                  </div>

                  {/* Submit */}
                  <button
                    type="submit"
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Create Schedule
                  </button>
                </form>
              </div>
            </div>

            {/* Schedules List */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Active Schedules ({schedules.length})
                  </h2>
                </div>

                {schedules.length === 0 ? (
                  <div className="p-12 text-center">
                    <Clock className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500">No scheduled reports</p>
                  </div>
                ) : (
                  <div className="divide-y">
                    {schedules.map(schedule => (
                      <div key={schedule.schedule_id} className="p-4 hover:bg-gray-50">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-semibold text-gray-900">{schedule.template}</h3>
                            <div className="mt-2 space-y-1 text-sm text-gray-600">
                              <p>Frequency: <span className="capitalize">{schedule.frequency}</span></p>
                              <p>Format: <span className="uppercase">{schedule.format}</span></p>
                              <p>Recipients: {schedule.recipients?.length || 0}</p>
                              <p className="text-xs text-gray-500 mt-2">
                                Next run: {new Date(schedule.next_run).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                          <button
                            onClick={() => deleteSchedule(schedule.schedule_id)}
                            disabled={deleting === schedule.schedule_id}
                            className="p-2 text-red-600 hover:bg-red-50 rounded disabled:opacity-50"
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ReportBuilder;
