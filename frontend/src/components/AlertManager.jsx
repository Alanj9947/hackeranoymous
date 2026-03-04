import React, { useState, useCallback } from 'react';
import {
  AlertCircle, AlertTriangle, Info, X, CheckCircle,
  Mail, MessageSquare, Phone, Bell
} from 'lucide-react';

/**
 * Alert Manager Component - Create and manage custom alerts.
 */
function AlertManager({ companyId = 'default' }) {
  const [alerts, setAlerts] = useState([]);
  const [formData, setFormData] = useState({
    alert_type: 'error_rate',
    severity: 'warning',
    title: '',
    message: '',
    channels: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const alertTypes = [
    { value: 'error_rate', label: 'Error Rate' },
    { value: 'budget_exceeded', label: 'Budget Exceeded' },
    { value: 'cost_spike', label: 'Cost Spike' },
    { value: 'agent_offline', label: 'Agent Offline' },
    { value: 'call_failure', label: 'Call Failure' },
    { value: 'system_down', label: 'System Down' },
    { value: 'quota_limit', label: 'Quota Limit' }
  ];

  const severities = [
    { value: 'critical', label: 'Critical', color: 'bg-red-50', border: 'border-red-200' },
    { value: 'warning', label: 'Warning', color: 'bg-yellow-50', border: 'border-yellow-200' },
    { value: 'info', label: 'Info', color: 'bg-blue-50', border: 'border-blue-200' }
  ];

  const channels = [
    { value: 'email', label: 'Email', icon: Mail },
    { value: 'slack', label: 'Slack', icon: MessageSquare },
    { value: 'sms', label: 'SMS', icon: Phone },
    { value: 'webhook', label: 'Webhook', icon: Bell }
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleChannelToggle = (channelValue) => {
    setFormData(prev => ({
      ...prev,
      channels: prev.channels.includes(channelValue)
        ? prev.channels.filter(c => c !== channelValue)
        : [...prev.channels, channelValue]
    }));
  };

  const createAlert = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/alerts/custom', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...formData,
          channels: formData.channels.length > 0 ? formData.channels : undefined
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create alert');
      }

      const data = await response.json();
      
      // Add to local list
      setAlerts(prev => [{
        id: Date.now(),
        ...data.alert,
        timestamp: new Date().toISOString()
      }, ...prev]);

      // Reset form
      setFormData({
        alert_type: 'error_rate',
        severity: 'warning',
        title: '',
        message: '',
        channels: []
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const dismissAlert = (alertId) => {
    setAlerts(prev => prev.filter(a => a.id !== alertId));
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return { bg: 'bg-red-50', border: 'border-red-200', icon: 'text-red-500' };
      case 'warning':
        return { bg: 'bg-yellow-50', border: 'border-yellow-200', icon: 'text-yellow-500' };
      case 'info':
        return { bg: 'bg-blue-50', border: 'border-blue-200', icon: 'text-blue-500' };
      default:
        return { bg: 'bg-gray-50', border: 'border-gray-200', icon: 'text-gray-500' };
    }
  };

  const getIcon = (severity) => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle className="w-5 h-5" />;
      case 'warning':
        return <AlertCircle className="w-5 h-5" />;
      case 'info':
      default:
        return <Info className="w-5 h-5" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Alert Manager</h1>
          <p className="text-gray-500 mt-1">Create and manage custom alerts with multi-channel notifications</p>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Create Alert Form */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">Create Alert</h2>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                  {error}
                </div>
              )}

              <form onSubmit={createAlert} className="space-y-4">
                {/* Alert Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Alert Type
                  </label>
                  <select
                    name="alert_type"
                    value={formData.alert_type}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {alertTypes.map(type => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Severity */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Severity
                  </label>
                  <div className="space-y-2">
                    {severities.map(sev => (
                      <label key={sev.value} className="flex items-center">
                        <input
                          type="radio"
                          name="severity"
                          value={sev.value}
                          checked={formData.severity === sev.value}
                          onChange={handleInputChange}
                          className="w-4 h-4 text-blue-600"
                        />
                        <span className="ml-2 text-sm text-gray-700">{sev.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Title */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Title
                  </label>
                  <input
                    type="text"
                    name="title"
                    value={formData.title}
                    onChange={handleInputChange}
                    placeholder="Alert title"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Message */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Message
                  </label>
                  <textarea
                    name="message"
                    value={formData.message}
                    onChange={handleInputChange}
                    placeholder="Alert message"
                    rows="3"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Channels */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Notify Via
                  </label>
                  <div className="space-y-2">
                    {channels.map(ch => {
                      const Icon = ch.icon;
                      return (
                        <label key={ch.value} className="flex items-center">
                          <input
                            type="checkbox"
                            checked={formData.channels.includes(ch.value)}
                            onChange={() => handleChannelToggle(ch.value)}
                            className="w-4 h-4 text-blue-600"
                          />
                          <Icon className="w-4 h-4 ml-2 text-gray-500" />
                          <span className="ml-2 text-sm text-gray-700">{ch.label}</span>
                        </label>
                      );
                    })}
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Leave unchecked to use defaults based on severity
                  </p>
                </div>

                {/* Submit */}
                <button
                  type="submit"
                  disabled={loading || !formData.title || !formData.message}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? 'Creating...' : 'Create Alert'}
                </button>
              </form>
            </div>
          </div>

          {/* Alerts List */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">
                Recent Alerts ({alerts.length})
              </h2>

              {alerts.length === 0 ? (
                <div className="text-center py-12">
                  <Bell className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">No alerts created yet</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {alerts.map(alert => {
                    const colors = getSeverityColor(alert.severity);
                    return (
                      <div
                        key={alert.id}
                        className={`${colors.bg} border ${colors.border} rounded-lg p-4`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3">
                            <div className={colors.icon}>
                              {getIcon(alert.severity)}
                            </div>
                            <div>
                              <h3 className="font-semibold text-gray-900">
                                {alert.title}
                              </h3>
                              <p className="text-sm text-gray-600 mt-1">
                                {alert.message}
                              </p>
                              <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                                <span className="inline-block px-2 py-1 bg-gray-200 rounded">
                                  {alert.alert_type}
                                </span>
                                <span>{new Date(alert.timestamp).toLocaleTimeString()}</span>
                              </div>
                            </div>
                          </div>
                          <button
                            onClick={() => dismissAlert(alert.id)}
                            className="text-gray-400 hover:text-gray-600 transition-colors"
                          >
                            <X className="w-5 h-5" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AlertManager;
