/**
 * API Client for accessing stored data via the Express API server
 * 
 * This client makes HTTP requests to the local API server which
 * provides access to the SQLite database.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_STORED_DATA_API_URL || 'http://localhost:3001';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Reading {
  id: number;
  channel_id: number;
  timestamp: string;
  energy_kwh: number | null;
  power_kw: number | null;
  voltage_v: number | null;
  current_a: number | null;
  power_factor: number | null;
  temperature_c: number | null;
}

export interface AggregatedReading {
  period: string;
  channel_id: number;
  total_energy_kwh: number;
  average_power_kw: number;
  peak_power_kw: number;
  min_power_kw: number;
  average_voltage_v: number;
  count: number;
}

export interface EnergyStatistics {
  total_energy_kwh: number;
  average_power_kw: number;
  peak_power_kw: number;
  peak_timestamp: string | null;
  min_power_kw: number;
  min_timestamp: string | null;
  average_voltage_v: number;
  count: number;
}

export interface ChannelInfo {
  channel_id: number;
  channel_name: string;
  device_id: number;
  device_name: string;
  organization_id: number;
  organization_name: string;
}

class StoredDataAPIClient {
  /**
   * Get all channels
   */
  async getChannels(organizationId?: number): Promise<ChannelInfo[]> {
    const params = organizationId ? { organizationId } : {};
    const response = await apiClient.get('/api/channels', { params });
    return response.data;
  }

  /**
   * Get raw readings for a channel
   */
  async getChannelReadings(
    channelId: number,
    startDate: string,
    endDate: string,
    limit?: number
  ): Promise<Reading[]> {
    const params: any = { startDate, endDate };
    if (limit) params.limit = limit;
    
    const response = await apiClient.get(`/api/channels/${channelId}/readings`, { params });
    return response.data;
  }

  /**
   * Get aggregated readings for a channel
   */
  async getAggregatedReadings(
    channelId: number,
    startDate: string,
    endDate: string,
    resolution: 'hour' | 'day' | 'week' | 'month' = 'hour'
  ): Promise<AggregatedReading[]> {
    const params = { startDate, endDate, resolution };
    const response = await apiClient.get(
      `/api/channels/${channelId}/readings/aggregated`,
      { params }
    );
    return response.data;
  }

  /**
   * Get energy statistics for a channel
   */
  async getEnergyStatistics(
    channelId: number,
    startDate: string,
    endDate: string
  ): Promise<EnergyStatistics> {
    const params = { startDate, endDate };
    const response = await apiClient.get(`/api/channels/${channelId}/statistics`, { params });
    return response.data;
  }

  /**
   * Get organization summary
   */
  async getOrganizationSummary(
    organizationId: number,
    startDate: string,
    endDate: string
  ) {
    const params = { startDate, endDate };
    const response = await apiClient.get(
      `/api/organizations/${organizationId}/summary`,
      { params }
    );
    return response.data;
  }

  /**
   * Get latest reading for a channel
   */
  async getLatestReading(channelId: number): Promise<Reading | null> {
    const response = await apiClient.get(`/api/channels/${channelId}/readings/latest`);
    return response.data;
  }

  /**
   * Get data availability range for a channel
   */
  async getDataRange(channelId: number) {
    const response = await apiClient.get(`/api/channels/${channelId}/range`);
    return response.data;
  }
}

export const storedDataApi = new StoredDataAPIClient();
