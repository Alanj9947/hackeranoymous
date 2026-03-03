/**
 * phoneNumberService - API client for phone number management
 */

import { apiClient } from './apiClient';

export const phoneNumberService = {
  /**
   * Get all phone numbers for current user
   */
  async getPhoneNumbers(agentId = null, status = null) {
    try {
      const params = new URLSearchParams();
      if (agentId) params.append('agent_id', agentId);
      if (status) params.append('status', status);

      const response = await apiClient.get(
        `/phone-numbers?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting phone numbers:', error);
      throw error;
    }
  },

  /**
   * Search available phone numbers
   */
  async getAvailableNumbers(country = 'US', areaCode = null, limit = 20) {
    try {
      const params = new URLSearchParams({
        country,
        limit: limit.toString(),
      });

      if (areaCode) {
        params.append('area_code', areaCode);
      }

      const response = await apiClient.get(
        `/phone-numbers/available?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      console.error('Error searching available numbers:', error);
      throw error;
    }
  },

  /**
   * Provision a new phone number
   */
  async provisionPhoneNumber(phoneNumber, agentId) {
    try {
      const params = new URLSearchParams({
        phone_number: phoneNumber,
        agent_id: agentId,
      });

      const response = await apiClient.post(
        `/phone-numbers?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      console.error('Error provisioning phone number:', error);
      throw error;
    }
  },

  /**
   * Get details for a specific phone number
   */
  async getPhoneNumberDetails(phoneNumberId) {
    try {
      const response = await apiClient.get(
        `/phone-numbers/${phoneNumberId}`
      );
      return response.data;
    } catch (error) {
      console.error('Error getting phone number details:', error);
      throw error;
    }
  },

  /**
   * Release a phone number
   */
  async releasePhoneNumber(phoneNumberId) {
    try {
      const response = await apiClient.delete(
        `/phone-numbers/${phoneNumberId}`
      );
      return response.data;
    } catch (error) {
      console.error('Error releasing phone number:', error);
      throw error;
    }
  },
};

export default phoneNumberService;
