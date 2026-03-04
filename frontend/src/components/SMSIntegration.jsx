import React, { useState, useEffect } from 'react';
import {
  MessageSquare, Send, Plus, AlertCircle, Check, Loader,
  Settings, Phone, Search, X
} from 'lucide-react';

/**
 * SMS Integration Component - Send and manage SMS conversations.
 */
function SMSIntegration({ companyId = 'default' }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('configure'); // configure, conversations, send
  const [provider, setProvider] = useState('twilio');
  const [configForm, setConfigForm] = useState({
    account_sid: '',
    auth_token: '',
    phone_number: ''
  });
  const [configLoading, setConfigLoading] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [conversationsLoading, setConversationsLoading] = useState(false);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);

  const [sendForm, setSendForm] = useState({
    phone: '',
    message: ''
  });
  const [sending, setSending] = useState(false);
  const [newMessage, setNewMessage] = useState('');
  const [posting, setPosting] = useState(false);

  // Load status on mount
  useEffect(() => {
    loadStatus();
  }, []);

  // Load conversations when connected
  useEffect(() => {
    if (status?.connected && activeTab === 'conversations') {
      loadConversations();
    }
  }, [status?.connected, activeTab]);

  const loadStatus = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/sms/status');
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
      const response = await fetch(`/api/v1/sms/configure/${provider}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configForm)
      });

      if (!response.ok) throw new Error('Configuration failed');

      const data = await response.json();
      setStatus(data.status);
      setConfigForm({ account_sid: '', auth_token: '', phone_number: '' });
    } catch (err) {
      setError(err.message);
    } finally {
      setConfigLoading(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      const response = await fetch('/api/v1/sms/disconnect', {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Disconnection failed');

      setStatus(null);
      setConversations([]);
      setSelectedConversation(null);
    } catch (err) {
      setError(err.message);
    }
  };

  const loadConversations = async () => {
    setConversationsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/sms/conversations?limit=50');
      if (!response.ok) throw new Error('Failed to load conversations');

      const data = await response.json();
      setConversations(data.conversations);
    } catch (err) {
      setError(err.message);
    } finally {
      setConversationsLoading(false);
    }
  };

  const handleSendSMS = async (e) => {
    e.preventDefault();
    setSending(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/sms/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sendForm)
      });

      if (!response.ok) throw new Error('Failed to send SMS');

      setSendForm({ phone: '', message: '' });
      loadConversations();
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  };

  const handleSendMessage = async (phone) => {
    if (!newMessage.trim()) return;

    setPosting(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/sms/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone,
          message: newMessage
        })
      });

      if (!response.ok) throw new Error('Failed to send message');

      setNewMessage('');
      // Reload conversation
      const convResponse = await fetch(`/api/v1/sms/conversations/${encodeURIComponent(phone)}`);
      if (convResponse.ok) {
        const convData = await convResponse.json();
        setSelectedConversation(convData);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setPosting(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearching(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/v1/sms/search?query=${encodeURIComponent(searchQuery)}&limit=20`
      );

      if (!response.ok) throw new Error('Search failed');

      const data = await response.json();
      setConversations(data.conversations);
    } catch (err) {
      setError(err.message);
    } finally {
      setSearching(false);
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
          <h1 className="text-3xl font-bold text-gray-900">SMS Integration</h1>
          <p className="text-gray-500 mt-1">Send and manage SMS conversations</p>
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
                  <span className="text-gray-600 ml-4">
                    {status.conversations} conversations
                  </span>
                </div>
              ) : (
                <div className="text-gray-600">No SMS provider connected</div>
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
            onClick={() => setActiveTab('conversations')}
            disabled={!status?.provider}
            className={`px-6 py-3 rounded-lg font-medium disabled:opacity-50 ${
              activeTab === 'conversations'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            <MessageSquare className="w-4 h-4 inline mr-2" />
            Conversations ({status?.conversations || 0})
          </button>
          <button
            onClick={() => setActiveTab('send')}
            disabled={!status?.provider}
            className={`px-6 py-3 rounded-lg font-medium disabled:opacity-50 ${
              activeTab === 'send'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700'
            }`}
          >
            <Send className="w-4 h-4 inline mr-2" />
            Send SMS
          </button>
        </div>

        {/* Configure Tab */}
        {activeTab === 'configure' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Configure SMS</h2>

              <form onSubmit={handleConfigure} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Account SID
                  </label>
                  <input
                    type="password"
                    value={configForm.account_sid}
                    onChange={(e) => setConfigForm(prev => ({
                      ...prev,
                      account_sid: e.target.value
                    }))}
                    placeholder="Enter Account SID"
                    required
                    disabled={status?.provider}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Auth Token
                  </label>
                  <input
                    type="password"
                    value={configForm.auth_token}
                    onChange={(e) => setConfigForm(prev => ({
                      ...prev,
                      auth_token: e.target.value
                    }))}
                    placeholder="Enter Auth Token"
                    required
                    disabled={status?.provider}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Twilio Phone Number
                  </label>
                  <input
                    type="tel"
                    value={configForm.phone_number}
                    onChange={(e) => setConfigForm(prev => ({
                      ...prev,
                      phone_number: e.target.value
                    }))}
                    placeholder="+1 (555) 123-4567"
                    required
                    disabled={status?.provider}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
                  />
                </div>

                <button
                  type="submit"
                  disabled={configLoading || !configForm.account_sid || status?.provider}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {configLoading ? 'Configuring...' : 'Configure'}
                </button>
              </form>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h3 className="font-semibold text-blue-900 mb-4">How to get credentials:</h3>
              <div className="text-sm text-blue-800 space-y-2">
                <p>1. Go to Twilio Console (twilio.com)</p>
                <p>2. Find your Account SID in the dashboard</p>
                <p>3. Find your Auth Token in Account Settings</p>
                <p>4. Have a Twilio phone number ready</p>
              </div>
            </div>
          </div>
        )}

        {/* Conversations Tab */}
        {activeTab === 'conversations' && status?.provider && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow p-4 sticky top-8">
                <form onSubmit={handleSearch} className="mb-4">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search conversations..."
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    />
                    <button
                      type="submit"
                      disabled={searching}
                      className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                    >
                      <Search className="w-4 h-4" />
                    </button>
                  </div>
                </form>

                {conversationsLoading ? (
                  <div className="text-center py-4">
                    <Loader className="w-5 h-5 text-blue-600 animate-spin mx-auto" />
                  </div>
                ) : conversations.length === 0 ? (
                  <div className="text-center py-4 text-gray-500 text-sm">
                    No conversations
                  </div>
                ) : (
                  <div className="space-y-2">
                    {conversations.map((conv) => (
                      <button
                        key={conv.conversation_id}
                        onClick={() => setSelectedConversation(conv)}
                        className={`w-full p-3 rounded-lg text-left transition-colors ${
                          selectedConversation?.conversation_id === conv.conversation_id
                            ? 'bg-blue-100 border border-blue-300'
                            : 'hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <Phone className="w-4 h-4 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm text-gray-900 truncate">
                              {conv.contact_name || conv.phone_number}
                            </p>
                            <p className="text-xs text-gray-600 truncate">
                              {conv.message_count} messages
                            </p>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Conversation Detail */}
            {selectedConversation && (
              <div className="lg:col-span-2 bg-white rounded-lg shadow flex flex-col h-[600px]">
                {/* Header */}
                <div className="p-4 border-b flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {selectedConversation.contact_name || selectedConversation.phone_number}
                    </h3>
                    <p className="text-xs text-gray-600">
                      {selectedConversation.message_count} messages
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedConversation(null)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  {selectedConversation.messages && selectedConversation.messages.map((msg) => (
                    <div
                      key={msg.message_id}
                      className={`flex ${msg.direction === 'outbound' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs px-4 py-2 rounded-lg ${
                          msg.direction === 'outbound'
                            ? 'bg-blue-600 text-white rounded-br-none'
                            : 'bg-gray-200 text-gray-900 rounded-bl-none'
                        }`}
                      >
                        <p className="text-sm">{msg.content}</p>
                        <p className="text-xs opacity-70 mt-1">
                          {new Date(msg.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Input */}
                <div className="border-t p-4">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage(selectedConversation.phone_number);
                        }
                      }}
                      placeholder="Type a message..."
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                    />
                    <button
                      onClick={() => handleSendMessage(selectedConversation.phone_number)}
                      disabled={posting || !newMessage.trim()}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Send SMS Tab */}
        {activeTab === 'send' && status?.provider && (
          <div className="max-w-2xl">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Send SMS</h2>

              <form onSubmit={handleSendSMS} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number *
                  </label>
                  <input
                    type="tel"
                    value={sendForm.phone}
                    onChange={(e) => setSendForm(prev => ({
                      ...prev,
                      phone: e.target.value
                    }))}
                    placeholder="+1 (555) 123-4567"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Message *
                  </label>
                  <textarea
                    value={sendForm.message}
                    onChange={(e) => setSendForm(prev => ({
                      ...prev,
                      message: e.target.value
                    }))}
                    placeholder="Type your message"
                    rows="6"
                    required
                    maxLength="160"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {sendForm.message.length}/160 characters
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={sending || !sendForm.phone || !sendForm.message}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {sending ? 'Sending...' : 'Send SMS'}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default SMSIntegration;
