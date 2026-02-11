/**
 * API Client for accessing stored energy data via the FastAPI backend.
 *
 * All queries go to Neon PostgreSQL through FastAPI.
 */

import apiClient from './apiClient'

export interface Reading {
  timestamp: string
  energy_kwh: number | null
  power_kw: number | null
  voltage_v: number | null
  current_a: number | null
  power_factor: number | null
}

export interface AggregatedReading {
  period: string
  channel_id: number
  total_energy_kwh: number
  average_power_kw: number
  peak_power_kw: number
  min_power_kw: number
  average_voltage_v: number
  count: number
}

export interface EnergyStatistics {
  total_energy_kwh: number
  average_power_kw: number
  peak_power_kw: number
  peak_timestamp: string | null
  min_power_kw: number
  min_timestamp: string | null
  average_voltage_v: number
  count: number
}

export interface ChannelInfo {
  channel_id: number
  channel_name: string
  device_id: number
  device_name: string
  organization_id: number
  organization_name: string
}

class StoredDataAPIClient {
  async getChannels(organizationId?: number): Promise<ChannelInfo[]> {
    const params = organizationId ? { organizationId } : {}
    const response = await apiClient.get('/api/channels', { params })
    return response.data
  }

  async getChannelReadings(
    channelId: number,
    startDate: string,
    endDate: string,
    limit?: number,
  ): Promise<Reading[]> {
    const params: Record<string, unknown> = { startDate, endDate }
    if (limit) params.limit = limit
    const response = await apiClient.get(`/api/channels/${channelId}/readings`, { params })
    return response.data
  }

  async getAggregatedReadings(
    channelId: number,
    startDate: string,
    endDate: string,
    resolution: 'hour' | 'day' | 'week' | 'month' = 'hour',
  ): Promise<AggregatedReading[]> {
    const params = { startDate, endDate, resolution }
    const response = await apiClient.get(`/api/channels/${channelId}/readings/aggregated`, { params })
    return response.data
  }

  async getEnergyStatistics(
    channelId: number,
    startDate: string,
    endDate: string,
  ): Promise<EnergyStatistics> {
    const params = { startDate, endDate }
    const response = await apiClient.get(`/api/channels/${channelId}/statistics`, { params })
    return response.data
  }

  async getOrganizationSummary(
    organizationId: number,
    startDate: string,
    endDate: string,
  ) {
    const params = { startDate, endDate }
    const response = await apiClient.get(`/api/organizations/${organizationId}/summary`, { params })
    return response.data
  }

  async getLatestReading(channelId: number): Promise<Reading | null> {
    const response = await apiClient.get(`/api/channels/${channelId}/readings/latest`)
    return response.data
  }

  async getDataRange(channelId: number) {
    const response = await apiClient.get(`/api/channels/${channelId}/range`)
    return response.data
  }
}

export const storedDataApi = new StoredDataAPIClient()
