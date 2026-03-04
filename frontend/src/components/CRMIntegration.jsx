import React, { useState, useEffect } from 'react';
import {
  Settings, Plus, Search, Link, Check, AlertCircle,
  Loader, Trash2, Mail, Phone, Building2
} from 'lucide-react';

/**
 * CRM Integration Component - Configure and manage CRM connections.
 */
function CRMIntegration({ companyId = 'default' }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('configure'); // configure, search, activity
  const [provider, setProvider] = useState('hubspot');
  const [configForm, setConfigForm] = useState({
    api_key: '',
    api_url: ''
  });
  const [configLoading, setConfigLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedContact, setSelectedContact] = useState(null);

  // Load CRM status on mount
  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/crm/status');
      if (!response.ok) throw new Error('Failed to load CRM status');

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
      const response = await fetch(`/api/v1/crm/configure/${provider}`, {
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
      const response = await fetch(`/api/v1/crm/disconnect/${status.provider}`, {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Disconnection failed');

      setStatus(null);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearching(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/v1/crm/contacts?query=${encodeURIComponent(searchQuery)}&limit=20`
      );

      if (!response.ok) throw new Error('Search failed');

      const data = await response.json();
      setSearchResults(data.results);
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
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">CRM Integration</h1>
          <p className="text-gray-500 mt-1">Connect and manage your CRM system</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {/* Connection Status */}
        <div className="mb-8 p-6 bg-white rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Status
              </h2>
              {status?.provider ? (
                <div className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-green-600" />
                  <span className="text-gray-700">
                    Connected to <strong>{status.provider.toUpperCase()}</strong>
                  </span>
                </div>
              ) : (
                <div className="text-gray-600">No CRM connected</div>
              )}
            </div>

            {status?.provider && (
              <button
                onClick={handleDisconnect}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
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
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              activeTab === 'configure'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Settings className="w-4 h-4 inline mr-2" />
            Configure
          </button>
          <button
            onClick={() => setActiveTab('search')}
            disabled={!status?.connected}
            className={`px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
              activeTab === 'search'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Search className="w-4 h-4 inline mr-2" />
            Search Contacts
          </button>
        </div>

        {/* Configure Tab */}
        {activeTab === 'configure' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Form */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Configure CRM</h2>

              <form onSubmit={handleConfigure} className="space-y-4">
                {/* Provider Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    CRM Provider
                  </label>
                  <select
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    disabled={status?.connected}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                  >
                    <option value="hubspot">HubSpot</option>
                    <option value="salesforce">Salesforce</option>
                  </select>
                </div>

                {/* API Key */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    API Key / Token
                  </label>
                  <input
                    type="password"
                    value={configForm.api_key}
                    onChange={(e) => setConfigForm(prev => ({
                      ...prev,
                      api_key: e.target.value
                    }))}
                    placeholder="Enter your API key"
                    required
                    disabled={status?.connected}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Your API credentials are encrypted
                  </p>
                </div>

                {/* Salesforce URL */}
                {provider === 'salesforce' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Salesforce Instance URL (Optional)
                    </label>
                    <input
                      type="url"
                      value={configForm.api_url}
                      onChange={(e) => setConfigForm(prev => ({
                        ...prev,
                        api_url: e.target.value
                      }))}
                      placeholder="https://your-instance.salesforce.com"
                      disabled={status?.connected}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                    />
                  </div>
                )}

                {/* Submit */}
                <button
                  type="submit"
                  disabled={configLoading || !configForm.api_key || status?.connected}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                  {configLoading ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin" />
                      Configuring...
                    </>
                  ) : (
                    <>
                      <Check className="w-4 h-4" />
                      Configure
                    </>
                  )}
                </button>
              </form>
            </div>

            {/* Info */}
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm font-medium text-blue-900 mb-2">How to get API credentials:</p>
                <div className="text-sm text-blue-800 space-y-2">
                  {provider === 'hubspot' ? (
                    <>
                      <p>1. Go to HubSpot Settings → Integrations → Private apps</p>
                      <p>2. Create a new private app</p>
                      <p>3. Copy the access token</p>
                    </>
                  ) : (
                    <>
                      <p>1. Go to Salesforce Setup → Apps → App Manager</p>
                      <p>2. Create a connected app</p>
                      <p>3. Generate a security token</p>
                    </>
                  )}
                </div>
              </div>

              <div className="bg-white rounded-lg border p-4">
                <p className="text-sm font-medium text-gray-900 mb-2">Features:</p>
                <ul className="text-sm text-gray-700 space-y-1">
                  <li>✓ Search and view contacts</li>
                  <li>✓ Log call activities</li>
                  <li>✓ Sync contact data</li>
                  <li>✓ Track interactions</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Search Tab */}
        {activeTab === 'search' && status?.connected && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Search Form */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow p-6 sticky top-8">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Search Contacts</h2>

                <form onSubmit={handleSearch} className="space-y-4">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by name, email, phone..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />

                  <button
                    type="submit"
                    disabled={searching || !searchQuery.trim()}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors flex items-center justify-center gap-2"
                  >
                    {searching ? (
                      <>
                        <Loader className="w-4 h-4 animate-spin" />
                        Searching...
                      </>
                    ) : (
                      <>
                        <Search className="w-4 h-4" />
                        Search
                      </>
                    )}
                  </button>
                </form>
              </div>
            </div>

            {/* Results */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow">
                {searchResults.length === 0 ? (
                  <div className="p-12 text-center text-gray-500">
                    {searchQuery ? 'No contacts found' : 'Enter a search query'}
                  </div>
                ) : (
                  <div className="divide-y">
                    {searchResults.map((contact) => (
                      <div
                        key={contact.external_id}
                        className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                        onClick={() => setSelectedContact(contact)}
                      >
                        <h3 className="font-semibold text-gray-900">{contact.name}</h3>
                        <div className="mt-2 space-y-1 text-sm text-gray-600">
                          {contact.email && (
                            <div className="flex items-center gap-2">
                              <Mail className="w-4 h-4" />
                              {contact.email}
                            </div>
                          )}
                          {contact.phone && (
                            <div className="flex items-center gap-2">
                              <Phone className="w-4 h-4" />
                              {contact.phone}
                            </div>
                          )}
                          {contact.company && (
                            <div className="flex items-center gap-2">
                              <Building2 className="w-4 h-4" />
                              {contact.company}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Contact Detail */}
              {selectedContact && (
                <div className="mt-8 bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Contact Details
                  </h3>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-gray-600">Name</p>
                      <p className="font-medium text-gray-900">{selectedContact.name}</p>
                    </div>
                    {selectedContact.email && (
                      <div>
                        <p className="text-sm text-gray-600">Email</p>
                        <p className="font-medium text-gray-900">{selectedContact.email}</p>
                      </div>
                    )}
                    {selectedContact.phone && (
                      <div>
                        <p className="text-sm text-gray-600">Phone</p>
                        <p className="font-medium text-gray-900">{selectedContact.phone}</p>
                      </div>
                    )}
                    {selectedContact.company && (
                      <div>
                        <p className="text-sm text-gray-600">Company</p>
                        <p className="font-medium text-gray-900">{selectedContact.company}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default CRMIntegration;
