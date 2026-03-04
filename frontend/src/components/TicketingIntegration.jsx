import React, { useState, useEffect } from 'react';
import {
  Settings, Plus, Ticket, AlertCircle, Check, Loader,
  MessageSquare, Clock, Flag, Trash2, Edit2
} from 'lucide-react';

/**
 * Ticketing Integration Component - Configure and manage ticketing systems.
 */
function TicketingIntegration({ companyId = 'default' }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('configure'); // configure, tickets, create
  const [provider, setProvider] = useState('zendesk');
  const [configForm, setConfigForm] = useState({
    api_key: '',
    api_url: ''
  });
  const [configLoading, setConfigLoading] = useState(false);
  const [tickets, setTickets] = useState([]);
  const [ticketsLoading, setTicketsLoading] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [createForm, setCreateForm] = useState({
    title: '',
    description: '',
    priority: 'medium'
  });
  const [creating, setCreating] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [posting, setPosting] = useState(false);

  // Load status on mount
  useEffect(() => {
    loadStatus();
  }, []);

  // Load tickets when connected
  useEffect(() => {
    if (status?.connected && activeTab === 'tickets') {
      loadTickets();
    }
  }, [status?.connected, activeTab]);

  const loadStatus = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/ticketing/status');
      if (!response.ok) throw new Error('Failed to load status');

      const data = await response.json();
      setStatus(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleConfigure = async (e) => {
    e.preventDefault();
    setConfigLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/ticketing/configure/${provider}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configForm)
      });

      if (!response.ok) throw new Error('Configuration failed');

      const data = await response.json();
      setStatus(data.status);
      setConfigForm({ api_key: '', api_url: '' });
    } catch (err) {
      setError(err.message);
    } finally {
      setConfigLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (!status?.provider) return;

    try {
      const response = await fetch(`/api/v1/ticketing/disconnect/${status.provider}`, {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Disconnection failed');

      setStatus(null);
      setTickets([]);
      setSelectedTicket(null);
    } catch (err) {
      setError(err.message);
    }
  };

  const loadTickets = async () => {
    setTicketsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/ticketing/tickets?limit=50');
      if (!response.ok) throw new Error('Failed to load tickets');

      const data = await response.json();
      setTickets(data.tickets);
    } catch (err) {
      setError(err.message);
    } finally {
      setTicketsLoading(false);
    }
  };

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    setCreating(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/ticketing/tickets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(createForm)
      });

      if (!response.ok) throw new Error('Failed to create ticket');

      const data = await response.json();
      setTickets([...tickets, data]);
      setCreateForm({ title: '', description: '', priority: 'medium' });
      setActiveTab('tickets');
    } catch (err) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  };

  const handleAddComment = async (ticketId) => {
    if (!commentText.trim()) return;

    setPosting(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/ticketing/tickets/${ticketId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: commentText })
      });

      if (!response.ok) throw new Error('Failed to post comment');

      setCommentText('');
    } catch (err) {
      setError(err.message);
    } finally {
      setPosting(false);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-600 bg-orange-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'open': return 'bg-blue-50 text-blue-700';
      case 'in_progress': return 'bg-yellow-50 text-yellow-700';
      case 'resolved': return 'bg-green-50 text-green-700';
      case 'closed': return 'bg-gray-50 text-gray-700';
      default: return 'bg-gray-50 text-gray-700';
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
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Ticketing Integration</h1>
          <p className="text-gray-500 mt-1">Connect and manage your ticketing system</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {/* Status Card */}
        <div className="mb-8 p-6 bg-white rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Status</h2>
              {status?.provider ? (
                <div className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-green-600" />
                  <span className="text-gray-700">
                    Connected to <strong>{status.provider.toUpperCase()}</strong>
                  </span>
                </div>
              ) : (
                <div className="text-gray-600">No ticketing system connected</div>
              )}
            </div>

            {status?.provider && (
              <button
                onClick={handleDisconnect}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Disconnect
              </button>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setActiveTab('configure')}
            className={`px-6 py-3 rounded-lg font-medium ${
              activeTab === 'configure'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            <Settings className="w-4 h-4 inline mr-2" />
            Configure
          </button>
          <button
            onClick={() => setActiveTab('tickets')}
            disabled={!status?.connected}
            className={`px-6 py-3 rounded-lg font-medium disabled:opacity-50 ${
              activeTab === 'tickets'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            <Ticket className="w-4 h-4 inline mr-2" />
            Tickets
          </button>
          <button
            onClick={() => setActiveTab('create')}
            disabled={!status?.connected}
            className={`px-6 py-3 rounded-lg font-medium disabled:opacity-50 ${
              activeTab === 'create'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            <Plus className="w-4 h-4 inline mr-2" />
            Create Ticket
          </button>
        </div>

        {/* Configure Tab */}
        {activeTab === 'configure' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Configure</h2>

              <form onSubmit={handleConfigure} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Provider
                  </label>
                  <select
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    disabled={status?.connected}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
                  >
                    <option value="zendesk">Zendesk</option>
                    <option value="jira">Jira</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    API Key
                  </label>
                  <input
                    type="password"
                    value={configForm.api_key}
                    onChange={(e) => setConfigForm(prev => ({
                      ...prev,
                      api_key: e.target.value
                    }))}
                    placeholder="Enter API key"
                    required
                    disabled={status?.connected}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
                  />
                </div>

                {provider === 'jira' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Jira Instance URL (Optional)
                    </label>
                    <input
                      type="url"
                      value={configForm.api_url}
                      onChange={(e) => setConfigForm(prev => ({
                        ...prev,
                        api_url: e.target.value
                      }))}
                      placeholder="https://your-instance.atlassian.net"
                      disabled={status?.connected}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
                    />
                  </div>
                )}

                <button
                  type="submit"
                  disabled={configLoading || !configForm.api_key || status?.connected}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {configLoading ? 'Configuring...' : 'Configure'}
                </button>
              </form>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h3 className="font-semibold text-blue-900 mb-4">How to get API credentials:</h3>
              {provider === 'zendesk' ? (
                <div className="text-sm text-blue-800 space-y-2">
                  <p>1. Go to Zendesk Admin Settings</p>
                  <p>2. Navigate to Apps & Integrations → APIs</p>
                  <p>3. Create OAuth token under Personal Access Tokens</p>
                  <p>4. Copy the token</p>
                </div>
              ) : (
                <div className="text-sm text-blue-800 space-y-2">
                  <p>1. Go to Jira Settings → Personal Settings</p>
                  <p>2. Create API Token</p>
                  <p>3. Copy the token</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tickets Tab */}
        {activeTab === 'tickets' && status?.connected && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Tickets ({tickets.length})
                  </h2>
                </div>

                {ticketsLoading ? (
                  <div className="p-12 text-center">
                    <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
                  </div>
                ) : tickets.length === 0 ? (
                  <div className="p-12 text-center text-gray-500">
                    No tickets found
                  </div>
                ) : (
                  <div className="divide-y">
                    {tickets.map((ticket) => (
                      <div
                        key={ticket.external_id}
                        className="p-4 hover:bg-gray-50 cursor-pointer"
                        onClick={() => setSelectedTicket(ticket)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h3 className="font-semibold text-gray-900">
                              {ticket.title}
                            </h3>
                            <div className="mt-2 flex items-center gap-3 text-sm">
                              <span className={`px-2 py-1 rounded-full ${getStatusColor(ticket.status)}`}>
                                {ticket.status}
                              </span>
                              <span className={`px-2 py-1 rounded-full ${getPriorityColor(ticket.priority)}`}>
                                {ticket.priority}
                              </span>
                            </div>
                          </div>
                          <Ticket className="w-5 h-5 text-gray-400" />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Ticket Detail */}
            {selectedTicket && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Details
                </h3>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-600">Title</p>
                    <p className="font-medium text-gray-900">{selectedTicket.title}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Status</p>
                    <p className="font-medium text-gray-900">{selectedTicket.status}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Priority</p>
                    <p className="font-medium text-gray-900">{selectedTicket.priority}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Description</p>
                    <p className="text-gray-700 text-sm mt-1">{selectedTicket.description}</p>
                  </div>

                  {/* Add Comment */}
                  <div className="border-t pt-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Add Comment
                    </label>
                    <textarea
                      value={commentText}
                      onChange={(e) => setCommentText(e.target.value)}
                      placeholder="Type a comment..."
                      rows="3"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                    <button
                      onClick={() => handleAddComment(selectedTicket.external_id)}
                      disabled={posting || !commentText.trim()}
                      className="mt-2 w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                    >
                      {posting ? 'Posting...' : 'Post Comment'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Create Ticket Tab */}
        {activeTab === 'create' && status?.connected && (
          <div className="max-w-2xl">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Create Ticket</h2>

              <form onSubmit={handleCreateTicket} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Title *
                  </label>
                  <input
                    type="text"
                    value={createForm.title}
                    onChange={(e) => setCreateForm(prev => ({
                      ...prev,
                      title: e.target.value
                    }))}
                    placeholder="Ticket title"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description *
                  </label>
                  <textarea
                    value={createForm.description}
                    onChange={(e) => setCreateForm(prev => ({
                      ...prev,
                      description: e.target.value
                    }))}
                    placeholder="Ticket description"
                    rows="6"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Priority
                  </label>
                  <select
                    value={createForm.priority}
                    onChange={(e) => setCreateForm(prev => ({
                      ...prev,
                      priority: e.target.value
                    }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={creating || !createForm.title || !createForm.description}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {creating ? 'Creating...' : 'Create Ticket'}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default TicketingIntegration;
