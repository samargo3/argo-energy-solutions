import axios, { AxiosInstance } from 'axios';

/**
 * Eniscope API Client — proxied through Express backend
 *
 * All Eniscope calls are routed through /api/eniscope/* on the Express
 * server, which holds the API credentials server-side.  The frontend
 * NEVER touches Eniscope credentials directly.
 */

class EniscopeAPIClient {
  private apiClient: AxiosInstance;

  constructor() {
    // Proxy base — Vite dev server forwards /api → Express (localhost:3001)
    this.apiClient = axios.create({
      baseURL: '',            // same origin; Vite proxy handles /api
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });
  }

  // ── Organisations ─────────────────────────────────────────────
  async getOrganizations(params?: { name?: string; email?: string; parent?: string }) {
    const response = await this.apiClient.get('/api/eniscope/channels', {
      params: { ...params, _type: 'organizations' },
    });
    return response.data;
  }

  async getOrganization(organizationId: string) {
    const response = await this.apiClient.get('/api/eniscope/channels', {
      params: { organization: organizationId },
    });
    return response.data;
  }

  // ── Devices ───────────────────────────────────────────────────
  async getDevices(params?: {
    organization?: string;
    uuid?: string;
    deviceType?: string;
    name?: string;
    page?: number;
    limit?: number;
  }) {
    const response = await this.apiClient.get('/api/eniscope/devices', { params });
    return response.data;
  }

  async getDevice(deviceId: string) {
    const response = await this.apiClient.get('/api/eniscope/devices', {
      params: { uuid: deviceId },
    });
    return response.data;
  }

  // ── Channels ──────────────────────────────────────────────────
  async getChannels(params?: {
    organization?: string;
    deviceId?: string;
    name?: string;
    tariff?: string;
    page?: number;
    limit?: number;
  }) {
    const response = await this.apiClient.get('/api/eniscope/channels', { params });
    return response.data;
  }

  async getChannel(channelId: string) {
    const response = await this.apiClient.get('/api/eniscope/channels', {
      params: { channelId },
    });
    return response.data;
  }

  // ── Readings ──────────────────────────────────────────────────
  async getReadings(
    channelId: string,
    params: {
      fields: string[];
      daterange?: string | [string, string];
      res?: 'auto' | '60' | '900' | '1800' | '3600' | '86400';
      action?: 'summarize' | 'total' | 'averageday' | 'typicalday' | 'medianday' | 'meanday' | 'minday' | 'maxday';
      showCounters?: boolean;
    }
  ) {
    const queryParams: Record<string, unknown> = {
      res: params.res || '3600',
      action: params.action || 'summarize',
      showCounters: params.showCounters ? '1' : '0',
      'fields[]': params.fields,
    };

    if (params.daterange) {
      if (Array.isArray(params.daterange)) {
        queryParams['daterange[]'] = params.daterange;
      } else {
        queryParams.daterange = params.daterange;
      }
    }

    const response = await this.apiClient.get(`/api/eniscope/readings/${channelId}`, {
      params: queryParams,
    });
    return response.data;
  }

  // ── Meters ────────────────────────────────────────────────────
  async getMeters(params?: {
    organization?: string;
    device?: string;
    uuid?: string;
    name?: string;
    page?: number;
    limit?: number;
  }) {
    // Note: meters endpoint not yet proxied — add to api-server.js if needed
    const response = await this.apiClient.get('/api/eniscope/channels', { params });
    return response.data;
  }
}

// Export singleton instance
export const eniscopeApi = new EniscopeAPIClient();

// Export types
export interface Organization {
  organizationId: string;
  organizationName: string;
  parentId: string | null;
  address1?: string;
  city?: string;
  country?: string;
  defaultEmailAddress?: string;
  links?: {
    devices?: string;
    channels?: string;
    meters?: string;
    [key: string]: string | undefined;
  };
}

export interface Device {
  deviceId: number;
  deviceName: string;
  deviceTypeId: number;
  deviceTypeName: string;
  organizationId: number;
  uuId: string;
  status: number;
  registered: string;
  expires: string;
  links?: {
    channels?: string;
    readings?: string;
    [key: string]: string | undefined;
  };
}

export interface Channel {
  channelId: number;
  channelName: string;
  deviceId: number;
  organizationId: number;
  tariffId?: number;
  links?: {
    readings?: string;
    [key: string]: string | undefined;
  };
}

export interface Reading {
  ts: string;
  E?: number; // Energy
  P?: number; // Power
  V?: number; // Voltage
  I?: number; // Current
  PF?: number; // Power Factor
  T?: number; // Temperature
  [key: string]: unknown; // Other fields
}
