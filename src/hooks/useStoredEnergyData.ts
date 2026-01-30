/**
 * React Hooks for accessing stored energy data from SQLite database
 * 
 * These hooks provide access to locally stored data via the API server
 * instead of making direct Eniscope API calls. Much faster and more reliable.
 * 
 * Note: Requires the API server to be running (node server/api-server.js)
 */

import { useQuery } from '@tanstack/react-query';
import { storedDataApi } from '../services/api/storedDataApi';
import type { Reading, AggregatedReading, EnergyStatistics, ChannelInfo } from '../services/api/storedDataApi';

/**
 * Hook to fetch raw readings for a channel from the database
 */
export function useStoredChannelReadings(
  channelId: number | null,
  startDate: string,
  endDate: string,
  options?: {
    enabled?: boolean;
  }
) {
  return useQuery<Reading[]>({
    queryKey: ['stored-readings', channelId, startDate, endDate],
    queryFn: async () => {
      if (!channelId) throw new Error('Channel ID is required');
      return storedDataApi.getChannelReadings(channelId, startDate, endDate);
    },
    enabled: !!channelId && !!startDate && !!endDate && (options?.enabled !== false),
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
  });
}

/**
 * Hook to fetch aggregated readings (hourly, daily, weekly, monthly)
 */
export function useStoredAggregatedReadings(
  channelId: number | null,
  startDate: string,
  endDate: string,
  resolution: 'hour' | 'day' | 'week' | 'month' = 'hour',
  options?: {
    enabled?: boolean;
  }
) {
  return useQuery<AggregatedReading[]>({
    queryKey: ['stored-aggregated', channelId, startDate, endDate, resolution],
    queryFn: async () => {
      if (!channelId) throw new Error('Channel ID is required');
      return storedDataApi.getAggregatedReadings(channelId, startDate, endDate, resolution);
    },
    enabled: !!channelId && !!startDate && !!endDate && (options?.enabled !== false),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook to fetch energy statistics for a channel
 */
export function useStoredEnergyStatistics(
  channelId: number | null,
  startDate: string,
  endDate: string,
  options?: {
    enabled?: boolean;
  }
) {
  return useQuery<EnergyStatistics>({
    queryKey: ['stored-statistics', channelId, startDate, endDate],
    queryFn: async () => {
      if (!channelId) throw new Error('Channel ID is required');
      return storedDataApi.getEnergyStatistics(channelId, startDate, endDate);
    },
    enabled: !!channelId && !!startDate && !!endDate && (options?.enabled !== false),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook to fetch all channels with metadata
 */
export function useStoredChannels(organizationId?: number) {
  return useQuery<ChannelInfo[]>({
    queryKey: ['stored-channels', organizationId],
    queryFn: async () => {
      return storedDataApi.getChannels(organizationId);
    },
    staleTime: 30 * 60 * 1000, // Channels change less frequently
  });
}

/**
 * Hook to fetch organization summary
 */
export function useStoredOrganizationSummary(
  organizationId: number | null,
  startDate: string,
  endDate: string,
  options?: {
    enabled?: boolean;
  }
) {
  return useQuery({
    queryKey: ['stored-organization-summary', organizationId, startDate, endDate],
    queryFn: async () => {
      if (!organizationId) throw new Error('Organization ID is required');
      return storedDataApi.getOrganizationSummary(organizationId, startDate, endDate);
    },
    enabled: !!organizationId && !!startDate && !!endDate && (options?.enabled !== false),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook to fetch latest reading for a channel
 */
export function useStoredLatestReading(channelId: number | null) {
  return useQuery<Reading | null>({
    queryKey: ['stored-latest-reading', channelId],
    queryFn: async () => {
      if (!channelId) throw new Error('Channel ID is required');
      return storedDataApi.getLatestReading(channelId);
    },
    enabled: !!channelId,
    staleTime: 1 * 60 * 1000, // Latest reading changes frequently
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
}

/**
 * Hook to fetch data availability range for a channel
 */
export function useStoredDataRange(channelId: number | null) {
  return useQuery({
    queryKey: ['stored-data-range', channelId],
    queryFn: async () => {
      if (!channelId) throw new Error('Channel ID is required');
      return storedDataApi.getDataRange(channelId);
    },
    enabled: !!channelId,
    staleTime: 60 * 60 * 1000, // Data range changes infrequently
  });
}
