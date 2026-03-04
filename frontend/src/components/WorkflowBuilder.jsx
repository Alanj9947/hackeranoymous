import React, { useState, useEffect } from 'react';
import {
  Plus, Trash2, Play, Pause, AlertCircle, Loader, Eye,
  CheckCircle, XCircle, Settings, Copy
} from 'lucide-react';

/**
 * Workflow Component - Visual workflow builder and automation engine.
 */
function WorkflowBuilder({ companyId = 'default' }) {
  const [activeTab, setActiveTab] = useState('workflows'); // workflows, builder, templates
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [executions, setExecutions] = useState([]);

  const [newWorkflow, setNewWorkflow] = useState({
    name: '',
    triggers: [],
    actions: []
  });
  const [building, setBuilding] = useState(false);

  const [templates, setTemplates] = useState([]);

  const triggerOptions = [
    { value: 'call_completed', label: 'Call Completed' },
    { value: 'call_failed', label: 'Call Failed' },
    { value: 'call_duration', label: 'Call Duration' },
    { value: 'agent_offline', label: 'Agent Offline' },
    { value: 'cost_threshold', label: 'Cost Threshold' },
    { value: 'sentiment_low', label: 'Low Sentiment' },
    { value: 'customer_feedback', label: 'Customer Feedback' }
  ];

  const actionOptions = [
    { value: 'send_sms', label: 'Send SMS' },
    { value: 'send_email', label: 'Send Email' },
    { value: 'create_ticket', label: 'Create Ticket' },
    { value: 'log_activity', label: 'Log Activity' },
    { value: 'update_crm', label: 'Update CRM' },
    { value: 'escalate', label: 'Escalate' },
    { value: 'notify_agent', label: 'Notify Agent' },
    { value: 'generate_report', label: 'Generate Report' },
    { value: 'trigger_forecast', label: 'Trigger Forecast' },
    { value: 'archive_call', label: 'Archive Call' }
  ];

  // Load workflows on mount
  useEffect(() => {
    loadWorkflows();
    loadTemplates();
  }, []);

  // Load executions when workflow selected
  useEffect(() => {
    if (selectedWorkflow && activeTab === 'workflows') {
      loadExecutions(selectedWorkflow.workflow_id);
    }
  }, [selectedWorkflow, activeTab]);

  const loadWorkflows = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/workflows');
      if (!response.ok) throw new Error('Failed to load workflows');

      const data = await response.json();
      setWorkflows(data.workflows);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await fetch('/api/v1/workflows/templates');
      if (!response.ok) throw new Error('Failed to load templates');

      const data = await response.json();
      setTemplates(data.templates);
    } catch (err) {
      // Templates optional
    }
  };

  const loadExecutions = async (workflowId) => {
    try {
      const response = await fetch(`/api/v1/workflows/${workflowId}/executions`);
      if (!response.ok) throw new Error('Failed to load executions');

      const data = await response.json();
      setExecutions(data.executions);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateWorkflow = async (e) => {
    e.preventDefault();
    setBuilding(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newWorkflow)
      });

      if (!response.ok) throw new Error('Failed to create workflow');

      setNewWorkflow({ name: '', triggers: [], actions: [] });
      loadWorkflows();
      setActiveTab('workflows');
    } catch (err) {
      setError(err.message);
    } finally {
      setBuilding(false);
    }
  };

  const handleDeleteWorkflow = async (workflowId) => {
    if (!window.confirm('Delete this workflow?')) return;

    try {
      const response = await fetch(`/api/v1/workflows/${workflowId}`, {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Failed to delete');

      loadWorkflows();
      setSelectedWorkflow(null);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEnableWorkflow = async (workflowId) => {
    try {
      const response = await fetch(
        `/api/v1/workflows/${workflowId}/enable`,
        { method: 'POST' }
      );

      if (!response.ok) throw new Error('Failed to enable');

      loadWorkflows();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDisableWorkflow = async (workflowId) => {
    try {
      const response = await fetch(
        `/api/v1/workflows/${workflowId}/disable`,
        { method: 'POST' }
      );

      if (!response.ok) throw new Error('Failed to disable');

      loadWorkflows();
    } catch (err) {
      setError(err.message);
    }
  };

  const loadTemplate = (template) => {
    setNewWorkflow({
      name: template.name,
      triggers: template.triggers,
      actions: template.actions
    });
    setActiveTab('builder');
  };

  const addTrigger = () => {
    setNewWorkflow(prev => ({
      ...prev,
      triggers: [...prev.triggers, { type: 'call_completed', condition: {} }]
    }));
  };

  const addAction = () => {
    setNewWorkflow(prev => ({
      ...prev,
      actions: [...prev.actions, { type: 'send_sms', config: {} }]
    }));
  };

  const removeTrigger = (idx) => {
    setNewWorkflow(prev => ({
      ...prev,
      triggers: prev.triggers.filter((_, i) => i !== idx)
    }));
  };

  const removeAction = (idx) => {
    setNewWorkflow(prev => ({
      ...prev,
      actions: prev.actions.filter((_, i) => i !== idx)
    }));
  };

  const getStatusColor = (status) => {
    if (status === 'active') return 'bg-green-50 text-green-700';
    if (status === 'paused') return 'bg-yellow-50 text-yellow-700';
    return 'bg-gray-50 text-gray-700';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Workflows</h1>
          <p className="text-gray-500 mt-1">Build custom automation workflows</p>
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
            onClick={() => setActiveTab('workflows')}
            className={`px-6 py-3 rounded-lg font-medium ${
              activeTab === 'workflows'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            My Workflows
          </button>
          <button
            onClick={() => setActiveTab('builder')}
            className={`px-6 py-3 rounded-lg font-medium ${
              activeTab === 'builder'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            <Plus className="w-4 h-4 inline mr-2" />
            Build
          </button>
          <button
            onClick={() => setActiveTab('templates')}
            className={`px-6 py-3 rounded-lg font-medium ${
              activeTab === 'templates'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            Templates
          </button>
        </div>

        {/* My Workflows Tab */}
        {activeTab === 'workflows' && (
          <div className="space-y-6">
            {loading ? (
              <div className="text-center py-12">
                <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
              </div>
            ) : workflows.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                No workflows. Create one to get started.
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Workflow List */}
                <div className="lg:col-span-1 space-y-3">
                  {workflows.map((workflow) => (
                    <div
                      key={workflow.workflow_id}
                      onClick={() => setSelectedWorkflow(workflow)}
                      className={`p-4 rounded-lg cursor-pointer transition-all ${
                        selectedWorkflow?.workflow_id === workflow.workflow_id
                          ? 'bg-blue-50 border-2 border-blue-500'
                          : 'bg-white border border-gray-200 hover:shadow'
                      }`}
                    >
                      <h3 className="font-semibold text-gray-900">{workflow.name}</h3>
                      <div className="mt-2 space-y-1 text-sm text-gray-600">
                        <p>{workflow.triggers.length} triggers</p>
                        <p>{workflow.actions.length} actions</p>
                        <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${getStatusColor(workflow.status)}`}>
                          {workflow.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Workflow Detail */}
                {selectedWorkflow && (
                  <div className="lg:col-span-2 bg-white rounded-lg shadow p-6 space-y-6">
                    {/* Header */}
                    <div className="border-b pb-4 flex items-center justify-between">
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900">
                          {selectedWorkflow.name}
                        </h2>
                        <p className="text-sm text-gray-600 mt-1">
                          Executions: {selectedWorkflow.execution_count}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        {selectedWorkflow.status === 'active' ? (
                          <button
                            onClick={() => handleDisableWorkflow(selectedWorkflow.workflow_id)}
                            className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
                          >
                            <Pause className="w-4 h-4 inline mr-2" />
                            Pause
                          </button>
                        ) : (
                          <button
                            onClick={() => handleEnableWorkflow(selectedWorkflow.workflow_id)}
                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                          >
                            <Play className="w-4 h-4 inline mr-2" />
                            Enable
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteWorkflow(selectedWorkflow.workflow_id)}
                          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {/* Triggers */}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">Triggers</h3>
                      <div className="space-y-2">
                        {selectedWorkflow.triggers.map((trigger, idx) => (
                          <div key={idx} className="p-3 bg-blue-50 rounded-lg">
                            <p className="font-medium text-blue-900">
                              {trigger.type.replace(/_/g, ' ').toUpperCase()}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Actions */}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">Actions</h3>
                      <div className="space-y-2">
                        {selectedWorkflow.actions.map((action, idx) => (
                          <div key={idx} className="p-3 bg-green-50 rounded-lg">
                            <p className="font-medium text-green-900">
                              {action.type.replace(/_/g, ' ').toUpperCase()}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Recent Executions */}
                    {executions.length > 0 && (
                      <div className="border-t pt-4">
                        <h3 className="text-lg font-semibold text-gray-900 mb-3">
                          Recent Executions
                        </h3>
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                          {executions.slice(0, 5).map((exec) => (
                            <div key={exec.execution_id} className="p-3 bg-gray-50 rounded-lg flex items-center gap-3">
                              {exec.status === 'completed' && exec.actions_failed === 0 ? (
                                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                              ) : (
                                <XCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
                              )}
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-gray-900">
                                  {new Date(exec.started_at).toLocaleString()}
                                </p>
                                <p className="text-xs text-gray-600">
                                  {exec.actions_executed}/{exec.actions_executed + exec.actions_failed} actions
                                </p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Builder Tab */}
        {activeTab === 'builder' && (
          <div className="bg-white rounded-lg shadow p-8 max-w-2xl">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Build Workflow</h2>

            <form onSubmit={handleCreateWorkflow} className="space-y-6">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Workflow Name *
                </label>
                <input
                  type="text"
                  value={newWorkflow.name}
                  onChange={(e) => setNewWorkflow(prev => ({
                    ...prev,
                    name: e.target.value
                  }))}
                  placeholder="e.g., Escalate Failed Calls"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>

              {/* Triggers */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-gray-900">Triggers</h3>
                  <button
                    type="button"
                    onClick={addTrigger}
                    className="px-3 py-1 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                  >
                    + Add
                  </button>
                </div>
                <div className="space-y-3">
                  {newWorkflow.triggers.map((trigger, idx) => (
                    <div key={idx} className="flex gap-2">
                      <select
                        value={trigger.type}
                        onChange={(e) => {
                          const updated = [...newWorkflow.triggers];
                          updated[idx].type = e.target.value;
                          setNewWorkflow(prev => ({ ...prev, triggers: updated }));
                        }}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                      >
                        {triggerOptions.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={() => removeTrigger(idx)}
                        className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-gray-900">Actions</h3>
                  <button
                    type="button"
                    onClick={addAction}
                    className="px-3 py-1 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700"
                  >
                    + Add
                  </button>
                </div>
                <div className="space-y-3">
                  {newWorkflow.actions.map((action, idx) => (
                    <div key={idx} className="flex gap-2">
                      <select
                        value={action.type}
                        onChange={(e) => {
                          const updated = [...newWorkflow.actions];
                          updated[idx].type = e.target.value;
                          setNewWorkflow(prev => ({ ...prev, actions: updated }));
                        }}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                      >
                        {actionOptions.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={() => removeAction(idx)}
                        className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Submit */}
              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  disabled={building || !newWorkflow.name || newWorkflow.triggers.length === 0 || newWorkflow.actions.length === 0}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {building ? 'Creating...' : 'Create Workflow'}
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('workflows')}
                  className="px-4 py-2 bg-gray-200 text-gray-900 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Templates Tab */}
        {activeTab === 'templates' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {templates.map((template) => (
              <div key={template.id} className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {template.name}
                </h3>
                <p className="text-gray-600 text-sm mb-4">{template.description}</p>
                <div className="space-y-2 mb-4 text-sm">
                  <p className="text-gray-700"><strong>Triggers:</strong> {template.triggers.length}</p>
                  <p className="text-gray-700"><strong>Actions:</strong> {template.actions.length}</p>
                </div>
                <button
                  onClick={() => loadTemplate(template)}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Copy className="w-4 h-4 inline mr-2" />
                  Use Template
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default WorkflowBuilder;
