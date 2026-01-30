import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import type { Reading } from '../services/api/eniscopeApi';

export interface ChannelReading {
  timestamp: string;
  energy: number; // kWh
  power: number; // kW
  voltage?: number; // V
  current?: number; // A
  powerFactor?: number;
  rawReading: Reading;
}

export interface ChannelAnalysisParams {
  channelId: string;
  startDate: Date;
  endDate: Date;
  resolution?: '60' | '900' | '1800' | '3600' | '86400'; // seconds
}

/**
 * Convert Eniscope API readings to standardized format
 */
const convertReadings = (readings: Reading[]): ChannelReading[] => {
  return readings.map((reading) => ({
    timestamp: reading.ts,
    energy: reading.E ? reading.E / 1000 : 0, // Convert Wh to kWh
    power: reading.P ? reading.P / 1000 : 0, // Convert W to kW
    voltage: reading.V,
    current: reading.I,
    powerFactor: reading.PF,
    rawReading: reading,
  }));
};

/**
 * Hook to fetch Eniscope channel readings via proxy
 */
export const useEniscopeChannelReadings = (params: ChannelAnalysisParams) => {
  return useQuery({
    queryKey: ['eniscope', 'channel', params.channelId, params.startDate, params.endDate, params.resolution],
    queryFn: async () => {
      // Format dates for Eniscope API (Unix timestamps)
      const startTs = Math.floor(params.startDate.getTime() / 1000);
      const endTs = Math.floor(params.endDate.getTime() / 1000);
      const daterange = [startTs.toString(), endTs.toString()];

      // Call the proxy API server instead of Eniscope directly
      const API_SERVER_URL = import.meta.env.VITE_API_SERVER_URL || 'http://localhost:3001';
      
      const response = await axios.get(`${API_SERVER_URL}/api/eniscope/readings/${params.channelId}`, {
        params: {
          fields: ['E', 'P', 'V', 'I', 'PF'],
          daterange: daterange,
          res: params.resolution || '3600',
          action: 'summarize',
        },
      });

      // Handle different response formats
      const readingList = Array.isArray(response.data) ? response.data : (response.data.records || response.data.data || response.data.result || []);
      return convertReadings(readingList);
    },
    enabled: !!params.channelId && !!params.startDate && !!params.endDate,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};
