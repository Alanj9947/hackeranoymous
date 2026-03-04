/**
 * analyticsService - API client for analytics endpoints
 */

import { apiClient } from './apiClient';

export const analyticsService = {
  /**
   * Get overall call statistics
   */
  async getCallsSummary(dateFrom = null, dateTo = null) {
    try {
      const params = new URLSearchParams();
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);

      const response = await apiClient.get(
        `/analytics/calls/summary?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting calls summary:', error);
      throw error;
    }
  },

  /**
   * Get calls by agent
   */
  async getCallsByAgent(dateFrom = null, dateTo = null, limit = 100) {
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
      });
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);

      const response = await apiClient.get(
        `/analytics/calls/by-agent?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting calls by agent:', error);
      throw error;
    }
  },

  /**
   * Get calls by phone number
   */
  async getCallsByPhone(dateFrom = null, dateTo = null, limit = 100) {
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
      });
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);

      const response = await apiClient.get(
        `/analytics/calls/by-phone?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting calls by phone:', error);
      throw error;
    }
  },

  /**
   * Get call trends
   */
  async getCallTrends(bucket = 'day', dateFrom = null, dateTo = null, limit = 100) {
    try {
      const params = new URLSearchParams({
        bucket,
        limit: limit.toString(),
      });
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);

      const response = await apiClient.get(
        `/analytics/calls/trend?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting call trends:', error);
      throw error;
    }
  },

  /**
   * Get agent metrics
   */
  async getAgentMetrics(agentId, dateFrom = null, dateTo = null) {
    try {
      const params = new URLSearchParams();
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);

      const response = await apiClient.get(
        `/analytics/agents/${agentId}/metrics?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting agent metrics:', error);
      throw error;
    }
  },

  /**
   * Get agent ranking
   */
  async getAgentRanking(metric = 'calls', dateFrom = null, dateTo = null, limit = 50) {
    try {
      const params = new URLSearchParams({
        metric,
        limit: limit.toString(),
      });
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);

      const response = await apiClient.get(
        `/analytics/agents/ranking?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting agent ranking:', error);
      throw error;
    }
  },

  /**
   * Get costs summary
   */
  async getCostsSummary(dateFrom = null, dateTo = null) {
    try {
      const params = new URLSearchParams();
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);

      const response = await apiClient.get(
        `/analytics/costs/summary?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting costs summary:', error);
      throw error;
    }
  },

  /**
   * Get cost trends
   */
  async getCostTrends(bucket = 'day', dateFrom = null, dateTo = null, limit = 100) {
    try {
      const params = new URLSearchParams({
        bucket,
        limit: limit.toString(),
      });
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);

      const response = await apiClient.get(
        `/analytics/costs/trend?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting cost trends:', error);
      throw error;
    }
  },

  /**
   * Get system health
   */
  async getSystemHealth() {
    try {
      const response = await apiClient.get('/analytics/health');
      return response.data;
    } catch (error) {
      console.error('Error getting system health:', error);
      throw error;
    }
  },
};

export default analyticsService;
