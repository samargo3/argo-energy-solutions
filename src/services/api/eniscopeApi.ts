import axios, { AxiosInstance } from 'axios';
import CryptoJS from 'crypto-js';

/**
 * Eniscope Core API Client
 * Handles authentication and API calls to the Eniscope Platform
 */

const ENISCOPE_API_URL = import.meta.env.VITE_ENISCOPE_API_URL || 'https://core.eniscope.com';
const ENISCOPE_API_KEY = import.meta.env.VITE_ENISCOPE_API_KEY || '';
const ENISCOPE_EMAIL = import.meta.env.VITE_ENISCOPE_EMAIL || '';
const ENISCOPE_PASSWORD = import.meta.env.VITE_ENISCOPE_PASSWORD || '';

interface EniscopeAuthResponse {
  sessionToken: string | null;
}

class EniscopeAPIClient {
  private apiClient: AxiosInstance;
  private sessionToken: string | null = null;
  private apiKey: string;
  private email: string;
  private passwordMd5: string;

  constructor() {
    this.apiKey = ENISCOPE_API_KEY;
    this.email = ENISCOPE_EMAIL;
    this.passwordMd5 = CryptoJS.MD5(ENISCOPE_PASSWORD).toString();

    this.apiClient = axios.create({
      baseURL: ENISCOPE_API_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/json',
        'X-Eniscope-API': this.apiKey,
      },
    });

    // Request interceptor to add auth headers
    this.apiClient.interceptors.request.use(
      async (config) => {
        // If no session token, authenticate first
        if (!this.sessionToken && config.url !== '/v1/1/organizations') {
          await this.authenticate();
        }

        if (this.sessionToken) {
          config.headers['X-Eniscope-Token'] = this.sessionToken;
        } else {
          // Use Basic Auth for initial authentication
          const authString = `${this.email}:${this.passwordMd5}`;
          const authB64 = btoa(authString);
          config.headers['Authorization'] = `Basic ${authB64}`;
        }

        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to capture session token
    this.apiClient.interceptors.response.use(
      (response) => {
        const token = response.headers['x-eniscope-token'] || response.headers['X-Eniscope-Token'];
        if (token) {
          this.sessionToken = token;
        }
        return response;
      },
      async (error) => {
        // If 401/419, try to re-authenticate
        if (error.response?.status === 401 || error.response?.status === 419) {
          this.sessionToken = null;
          await this.authenticate();
          // Retry the original request
          if (error.config) {
            error.config.headers['X-Eniscope-Token'] = this.sessionToken;
            return this.apiClient.request(error.config);
          }
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Authenticate and get session token
   */
  private async authenticate(): Promise<string | null> {
    try {
      const authString = `${this.email}:${this.passwordMd5}`;
      const authB64 = btoa(authString);

      const response = await axios.get(`${ENISCOPE_API_URL}/v1/1/organizations`, {
        headers: {
          'Authorization': `Basic ${authB64}`,
          'X-Eniscope-API': this.apiKey,
          'Accept': 'text/json',
        },
      });

      this.sessionToken = response.headers['x-eniscope-token'] || response.headers['X-Eniscope-Token'] || null;
      return this.sessionToken;
    } catch (error: any) {
      console.error('Authentication failed:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * Get organizations
   */
  async getOrganizations(params?: { name?: string; email?: string; parent?: string }) {
    const response = await this.apiClient.get('/v1/1/organizations', { params });
    return response.data;
  }

  /**
   * Get a specific organization by ID
   */
  async getOrganization(organizationId: string) {
    const response = await this.apiClient.get(`/v1/1/organizations/${organizationId}`);
    return response.data;
  }

  /**
   * Get devices
   */
  async getDevices(params?: {
    organization?: string;
    uuid?: string;
    deviceType?: string;
    name?: string;
    page?: number;
    limit?: number;
  }) {
    const response = await this.apiClient.get('/v1/1/devices', { params });
    return response.data;
  }

  /**
   * Get a specific device by ID
   */
  async getDevice(deviceId: string) {
    const response = await this.apiClient.get(`/v1/1/devices/${deviceId}`);
    return response.data;
  }

  /**
   * Get channels
   */
  async getChannels(params?: {
    organization?: string;
    deviceId?: string;
    name?: string;
    tariff?: string;
    page?: number;
    limit?: number;
  }) {
    const response = await this.apiClient.get('/v1/1/channels', { params });
    return response.data;
  }

  /**
   * Get a specific channel by ID
   */
  async getChannel(channelId: string) {
    const response = await this.apiClient.get(`/v1/1/channels/${channelId}`);
    return response.data;
  }

  /**
   * Get readings for a channel
   */
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
    const queryParams: any = {
      res: params.res || '3600',
      action: params.action || 'summarize',
      showCounters: params.showCounters ? '1' : '0',
    };

    // Handle fields array
    params.fields.forEach((field) => {
      queryParams['fields[]'] = field;
    });

    // Handle daterange
    if (params.daterange) {
      if (Array.isArray(params.daterange)) {
        // For array format, use daterange[] for both values
        queryParams['daterange[]'] = [params.daterange[0], params.daterange[1]];
      } else {
        queryParams.daterange = params.daterange;
      }
    }

    const response = await this.apiClient.get(`/v1/1/readings/${channelId}`, {
      params: queryParams,
    });
    return response.data;
  }

  /**
   * Get meters
   */
  async getMeters(params?: {
    organization?: string;
    device?: string;
    uuid?: string;
    name?: string;
    page?: number;
    limit?: number;
  }) {
    const response = await this.apiClient.get('/v1/1/meters', { params });
    return response.data;
  }

  /**
   * Get accounts
   */
  async getAccounts(params?: {
    organization?: string;
    email?: string;
    name?: string;
    status?: string;
    page?: number;
    limit?: number;
  }) {
    const response = await this.apiClient.get('/v1/1/accounts', { params });
    return response.data;
  }

  /**
   * Get alarms
   */
  async getAlarms(params?: {
    organization?: string;
    channel?: string;
    status?: string;
    type?: string;
    page?: number;
    limit?: number;
  }) {
    const response = await this.apiClient.get('/v1/1/alarms', { params });
    return response.data;
  }

  /**
   * Get events
   */
  async getEvents(params?: {
    organization?: string;
    resource?: string;
    account?: string;
    type?: string;
    startTs?: string;
    page?: number;
    limit?: number;
  }) {
    const response = await this.apiClient.get('/v1/1/events', { params });
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
  [key: string]: any; // Other fields
}


