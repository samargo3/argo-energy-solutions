import apiClient from './apiClient';
import type {
  EnergyConsumption,
  EnergyConsumptionGrouped,
  Site,
  Customer,
  DateRangeParams,
  PaginationParams,
  PaginatedResponse,
} from '../../types';

// Configured for Eniscope/Best.Energy API structure
// Based on Wilson Center data format

/**
 * Get energy consumption data for a specific customer/channel
 * Eniscope uses channel-based readings with Unix timestamps
 */
export const getCustomerEnergyConsumption = async (
  customerId: string,
  params: DateRangeParams & PaginationParams
): Promise<PaginatedResponse<EnergyConsumption>> => {
  // Convert dates to Unix timestamps for Eniscope API
  const startTs = Math.floor(new Date(params.startDate || '').getTime() / 1000);
  const endTs = Math.floor(new Date(params.endDate || '').getTime() / 1000);
  
  // Try Eniscope API endpoints
  const endpoints = [
    `/v1/readings/${customerId}`,
    `/readings/${customerId}`,
    `/v1/channels/${customerId}/readings`,
  ];
  
  let lastError;
  for (const endpoint of endpoints) {
    try {
      const response = await apiClient.get(endpoint, {
        params: {
          start: startTs,
          end: endTs,
          resolution: '3600', // Hourly
          ...params,
        },
      });
      
      // Transform Eniscope format to our format
      return transformEniscopeResponse(response.data);
    } catch (error) {
      lastError = error;
      continue;
    }
  }
  
  throw lastError;
};

/**
 * Transform Eniscope API response to our format
 */
function transformEniscopeResponse(data: any): PaginatedResponse<EnergyConsumption> {
  const items: EnergyConsumption[] = [];
  
  // Handle Eniscope channel-based structure
  const channels = data.channels || (Array.isArray(data) ? data : [data]);
  
  for (const channel of channels) {
    const channelName = channel.channel || channel.channelName || 'Unknown';
    const readings = channel.rawReadings || channel.readings || [];
    
    for (const reading of readings) {
      // Convert Unix timestamp to ISO string
      const timestamp = new Date(reading.ts * 1000).toISOString();
      
      // E field is energy in Wh, convert to kWh
      const value = (reading.E || reading.energy || 0) / 1000;
      
      items.push({
        id: `${channelName}_${reading.ts}`,
        siteId: channelName,
        customerId: channel.channelId || '',
        timestamp,
        value,
        cost: value * 0.15, // Default rate, update as needed
      });
    }
  }
  
  return {
    data: items,
    total: items.length,
    page: 1,
    pageSize: items.length,
  };
}

/**
 * Get energy consumption data for a specific site
 */
export const getSiteEnergyConsumption = async (
  siteId: string,
  params: DateRangeParams & PaginationParams
): Promise<PaginatedResponse<EnergyConsumption>> => {
  const startTs = Math.floor(new Date(params.startDate || '').getTime() / 1000);
  const endTs = Math.floor(new Date(params.endDate || '').getTime() / 1000);
  
  const response = await apiClient.get(`/v1/sites/${siteId}/data`, {
    params: {
      start: startTs,
      end: endTs,
      resolution: '3600',
      ...params,
    },
  });
  
  return transformEniscopeResponse(response.data);
};

/**
 * Get aggregated energy consumption data (grouped by day/week/month)
 */
export const getGroupedEnergyConsumption = async (
  customerId: string,
  params: DateRangeParams & { groupBy?: 'day' | 'week' | 'month' }
): Promise<EnergyConsumptionGrouped[]> => {
  const startTs = Math.floor(new Date(params.startDate || '').getTime() / 1000);
  const endTs = Math.floor(new Date(params.endDate || '').getTime() / 1000);
  
  // Calculate resolution based on groupBy
  let resolution = '3600'; // default hourly
  if (params.groupBy === 'day') resolution = '86400';
  if (params.groupBy === 'week') resolution = '604800';
  if (params.groupBy === 'month') resolution = '2592000';
  
  const response = await apiClient.get(`/v1/readings/${customerId}`, {
    params: {
      start: startTs,
      end: endTs,
      resolution,
    },
  });
  
  // Transform to grouped format
  return transformToGroupedData(response.data, params.groupBy || 'day');
};

/**
 * Transform Eniscope data to grouped format
 */
function transformToGroupedData(data: any, groupBy: string): EnergyConsumptionGrouped[] {
  const channels = data.channels || (Array.isArray(data) ? data : [data]);
  const grouped = new Map<string, { value: number; cost: number; count: number }>();
  
  for (const channel of channels) {
    const readings = channel.rawReadings || channel.readings || [];
    
    for (const reading of readings) {
      const date = new Date(reading.ts * 1000);
      let key: string;
      
      if (groupBy === 'day') {
        key = date.toISOString().split('T')[0];
      } else if (groupBy === 'week') {
        const weekStart = new Date(date);
        weekStart.setDate(date.getDate() - date.getDay());
        key = weekStart.toISOString().split('T')[0];
      } else {
        key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      }
      
      const value = (reading.E || reading.energy || 0) / 1000;
      const cost = value * 0.15;
      
      const existing = grouped.get(key) || { value: 0, cost: 0, count: 0 };
      grouped.set(key, {
        value: existing.value + value,
        cost: existing.cost + cost,
        count: existing.count + 1,
      });
    }
  }
  
  return Array.from(grouped.entries()).map(([date, data]) => ({
    date,
    value: data.value,
    cost: data.cost,
  })).sort((a, b) => a.date.localeCompare(b.date));
};

/**
 * Get all customers
 */
export const getCustomers = async (
  params?: PaginationParams
): Promise<PaginatedResponse<Customer>> => {
  const response = await apiClient.get('/customers', { params });
  return response.data;
};

/**
 * Get a specific customer by ID
 */
export const getCustomer = async (customerId: string): Promise<Customer> => {
  const response = await apiClient.get(`/customers/${customerId}`);
  return response.data;
};

/**
 * Get sites for a customer
 */
export const getCustomerSites = async (
  customerId: string
): Promise<Site[]> => {
  const response = await apiClient.get(`/customers/${customerId}/sites`);
  return response.data;
};

/**
 * Get a specific site by ID
 */
export const getSite = async (siteId: string): Promise<Site> => {
  const response = await apiClient.get(`/sites/${siteId}`);
  return response.data;
};

// Export all API functions
export const bestEnergyApi = {
  getCustomerEnergyConsumption,
  getSiteEnergyConsumption,
  getGroupedEnergyConsumption,
  getCustomers,
  getCustomer,
  getCustomerSites,
  getSite,
};

