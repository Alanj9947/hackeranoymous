/**
 * PhoneNumberSettings - Manage phone numbers for agents
 * Search available numbers, provision, release, and assign to agents
 */

import React, { useState, useEffect } from 'react';
import { Phone, Search, Plus, Trash2, Loader, AlertCircle, CheckCircle } from 'lucide-react';
import { phoneNumberService } from '../services/phoneNumberService';

export const PhoneNumberSettings = ({ agentId, agentName }) => {
  // State
  const [activeTab, setActiveTab] = useState('current'); // current, search, manage
  const [currentNumbers, setCurrentNumbers] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Search form state
  const [searchForm, setSearchForm] = useState({
    country: 'US',
    areaCode: '',
  });

  // Load current numbers on mount
  useEffect(() => {
    loadCurrentNumbers();
  }, []);

  const loadCurrentNumbers = async () => {
    try {
      setLoading(true);
      const numbers = await phoneNumberService.getPhoneNumbers();
      setCurrentNumbers(numbers.numbers || []);
      setError(null);
    } catch (err) {
      console.error('Error loading numbers:', err);
      setError('Failed to load phone numbers');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    try {
      setLoading(true);
      setError(null);
      const results = await phoneNumberService.getAvailableNumbers(
        searchForm.country,
        searchForm.areaCode
      );
      setSearchResults(results.numbers || []);
      setSuccess(`Found ${results.count} available numbers`);
    } catch (err) {
      console.error('Error searching numbers:', err);
      setError('Failed to search available numbers');
    } finally {
      setLoading(false);
    }
  };

  const handleProvision = async (phoneNumber) => {
    if (!agentId) {
      setError('Please select an agent first');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await phoneNumberService.provisionPhoneNumber(phoneNumber, agentId);
      setSuccess(`Successfully provisioned ${phoneNumber}`);
      setSearchResults([]);
      setActiveTab('current');
      await loadCurrentNumbers();
    } catch (err) {
      console.error('Error provisioning number:', err);
      setError(`Failed to provision ${phoneNumber}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRelease = async (numberId, phoneNumber) => {
    if (!window.confirm(`Release ${phoneNumber}? This cannot be undone.`)) {
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await phoneNumberService.releasePhoneNumber(numberId);
      setSuccess(`Released ${phoneNumber}`);
      await loadCurrentNumbers();
    } catch (err) {
      console.error('Error releasing number:', err);
      setError(`Failed to release ${phoneNumber}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Phone className="text-blue-600" size={24} />
        <div>
          <h2 className="text-2xl font-bold">Phone Numbers</h2>
          <p className="text-gray-600 text-sm">Manage Twilio phone numbers for {agentName}</p>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="text-red-600 flex-shrink-0 mt-0.5" size={20} />
          <div className="text-red-700">
            <p className="font-semibold">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Success Banner */}
      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
          <CheckCircle className="text-green-600 flex-shrink-0 mt-0.5" size={20} />
          <div className="text-green-700">
            <p className="font-semibold">Success</p>
            <p className="text-sm">{success}</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('current')}
          className={`px-4 py-2 font-medium border-b-2 transition ${
            activeTab === 'current'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          My Numbers ({currentNumbers.length})
        </button>
        <button
          onClick={() => setActiveTab('search')}
          className={`px-4 py-2 font-medium border-b-2 transition ${
            activeTab === 'search'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Get New Number
        </button>
      </div>

      {/* Current Numbers Tab */}
      {activeTab === 'current' && (
        <div className="space-y-4">
          {loading && <div className="text-center py-8 text-gray-500">Loading...</div>}

          {!loading && currentNumbers.length === 0 && (
            <div className="bg-gray-50 rounded-lg p-8 text-center">
              <Phone size={48} className="text-gray-300 mx-auto mb-3" />
              <p className="text-gray-600">No phone numbers provisioned yet</p>
              <button
                onClick={() => setActiveTab('search')}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
              >
                <Plus size={16} className="inline mr-2" />
                Get Your First Number
              </button>
            </div>
          )}

          {!loading && currentNumbers.length > 0 && (
            <div className="space-y-3">
              {currentNumbers.map((number) => (
                <div
                  key={number.id}
                  className="bg-white border border-gray-200 rounded-lg p-4 flex items-between justify-between"
                >
                  <div className="flex-1">
                    <p className="text-lg font-semibold text-gray-900">{number.phone_number}</p>
                    <div className="grid grid-cols-3 gap-4 mt-2 text-sm text-gray-600">
                      <div>
                        <span className="text-gray-500">Agent:</span> {number.agent_name || 'Unassigned'}
                      </div>
                      <div>
                        <span className="text-gray-500">Status:</span>
                        <span
                          className={`ml-1 px-2 py-1 rounded text-xs font-medium ${
                            number.status === 'active'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {number.status}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Cost:</span> ${number.monthly_cost}/month
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-gray-500">
                      Calls: {number.call_count} | Provisioned: {new Date(number.provisioned_at).toLocaleDateString()}
                    </div>
                  </div>
                  <button
                    onClick={() => handleRelease(number.id, number.phone_number)}
                    disabled={loading}
                    className="px-3 py-2 text-red-600 hover:bg-red-50 rounded font-medium disabled:opacity-50 transition"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Search Numbers Tab */}
      {activeTab === 'search' && (
        <div className="space-y-4">
          {/* Search Form */}
          <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">Country</label>
              <select
                value={searchForm.country}
                onChange={(e) => setSearchForm({ ...searchForm, country: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="US">United States</option>
                <option value="CA">Canada</option>
                <option value="GB">United Kingdom</option>
                <option value="AU">Australia</option>
              </select>
            </div>

            {searchForm.country === 'US' && (
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Area Code (US Only)
                </label>
                <input
                  type="text"
                  value={searchForm.areaCode}
                  onChange={(e) => setSearchForm({ ...searchForm, areaCode: e.target.value })}
                  placeholder="e.g., 415"
                  maxLength="3"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}

            <button
              onClick={handleSearch}
              disabled={loading}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? <Loader size={18} className="animate-spin" /> : <Search size={18} />}
              Search Numbers
            </button>
          </div>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-semibold text-gray-900">Available Numbers</h3>
              {searchResults.map((number) => (
                <div
                  key={number.phone_number}
                  className="bg-white border border-gray-200 rounded-lg p-4 flex items-center justify-between"
                >
                  <div>
                    <p className="text-lg font-semibold text-gray-900">{number.phone_number}</p>
                    <p className="text-sm text-gray-600">
                      {number.locality}, {number.region}
                    </p>
                  </div>
                  <button
                    onClick={() => handleProvision(number.phone_number)}
                    disabled={loading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                  >
                    {loading ? <Loader size={16} className="animate-spin" /> : <Plus size={16} />}
                    Select
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Loading Indicator */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 flex items-center gap-3">
            <Loader className="animate-spin text-blue-600" size={24} />
            <p className="text-gray-900">Processing...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default PhoneNumberSettings;
