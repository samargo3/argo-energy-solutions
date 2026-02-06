/**
 * Data Fetcher for Weekly Reports
 * 
 * Wraps Eniscope API client and handles data retrieval for report generation
 */

import axios from 'axios';
import crypto from 'crypto';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
import { toUnixTimestamp, generateExpectedTimestamps } from './date-utils.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// Go up from backend/scripts/reports/lib/ to project root
dotenv.config({ path: path.join(__dirname, '..', '..', '..', '..', '.env') });

/**
 * Eniscope API Client (Node.js compatible)
 */
class EniscopeAPIClient {
  constructor() {
    this.baseUrl = (process.env.VITE_ENISCOPE_API_URL || process.env.VITE_BEST_ENERGY_API_URL || 'https://core.eniscope.com').replace(/\/$/, '');
    this.apiKey = process.env.VITE_ENISCOPE_API_KEY || process.env.VITE_BEST_ENERGY_API_KEY || process.env.ENISCOPE_API_KEY || '';
    this.email = process.env.VITE_ENISCOPE_EMAIL || process.env.ENISCOPE_EMAIL || '';
    this.password = process.env.VITE_ENISCOPE_PASSWORD || process.env.ENISCOPE_PASSWORD || '';
    this.passwordMd5 = crypto.createHash('md5').update(this.password).digest('hex');
    this.sessionToken = null;
    
    if (!this.apiKey || !this.email || !this.password) {
      throw new Error('Missing required Eniscope API credentials in environment variables');
    }
  }
  
  async authenticate() {
    const authString = `${this.email}:${this.passwordMd5}`;
    const authB64 = Buffer.from(authString).toString('base64');
    
    try {
      const response = await axios.get(`${this.baseUrl}/organizations`, {
        headers: {
          'Authorization': `Basic ${authB64}`,
          'X-Eniscope-API': this.apiKey,
          'Accept': 'text/json',
        },
      });
      
      this.sessionToken = response.headers['x-eniscope-token'] || response.headers['X-Eniscope-Token'] || null;
      return true;
    } catch (error) {
      console.error('Authentication failed:', error.response?.data || error.message);
      throw error;
    }
  }
  
  async makeRequest(endpoint, params = {}, retries = 3) {
    if (!this.sessionToken) {
      await this.authenticate();
    }
    
    const headers = {
      'X-Eniscope-API': this.apiKey,
      'Accept': 'text/json',
    };
    
    if (this.sessionToken) {
      headers['X-Eniscope-Token'] = this.sessionToken;
    }
    
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const response = await axios.get(`${this.baseUrl}${endpoint}`, {
          headers,
          params,
        });
        return response.data;
      } catch (error) {
        if (error.response?.status === 429 && attempt < retries - 1) {
          const delay = Math.pow(2, attempt) * 1000;
          console.log(`Rate limited. Retrying in ${delay/1000}s...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        } else if ((error.response?.status === 401 || error.response?.status === 419) && attempt < retries - 1) {
          this.sessionToken = null;
          await this.authenticate();
        } else {
          throw error;
        }
      }
    }
  }
  
  async getOrganizations() {
    return this.makeRequest('/organizations');
  }
  
  async getOrganization(orgId) {
    return this.makeRequest(`/organizations/${orgId}`);
  }
  
  async getDevices(params) {
    return this.makeRequest('/devices', params);
  }
  
  async getChannels(params) {
    return this.makeRequest('/channels', params);
  }
  
  async getReadings(channelId, options = {}) {
    const params = {
      action: 'summarize', // Always use summarize for time series
      res: options.res || options.resolution || '3600',
    };
    
    // Add fields
    if (options.fields && Array.isArray(options.fields)) {
      // Send as multiple parameters, not as array
      options.fields.forEach(field => {
        if (!params['fields[]']) {
          params['fields[]'] = [];
        }
        if (Array.isArray(params['fields[]'])) {
          params['fields[]'].push(field);
        }
      });
    }
    
    // Add date range - use array format
    if (options.daterange) {
      if (Array.isArray(options.daterange)) {
        params['daterange[]'] = options.daterange;
      } else {
        params.daterange = options.daterange;
      }
    }
    
    return this.makeRequest(`/readings/${channelId}`, params);
  }
  
  async getAlarms(params) {
    return this.makeRequest('/alarms', params);
  }
  
  async getEvents(params) {
    return this.makeRequest('/events', params);
  }
}

/**
 * Data Fetcher for weekly reports
 */
export class WeeklyReportDataFetcher {
  constructor(config) {
    this.config = config;
    this.client = new EniscopeAPIClient();
  }
  
  /**
   * Fetch site metadata
   */
  async fetchSiteMetadata(siteId) {
    console.log(`Fetching site metadata for ${siteId}...`);
    
    // Get organization details
    const org = await this.client.getOrganization(siteId);
    
    return {
      siteId: org.organizationId || siteId,
      siteName: org.organizationName || 'Unknown Site',
      address: org.address1 || null,
      city: org.city || null,
      country: org.country || null,
      timezone: this.config.timezone,
    };
  }
  
  /**
   * Fetch channels (meters/submeters) for a site
   */
  async fetchChannels(siteId) {
    console.log(`Fetching channels for site ${siteId}...`);
    
    const response = await this.client.getChannels({ organization: siteId });
    
    // Handle different response formats
    let channelsArray = [];
    if (Array.isArray(response)) {
      channelsArray = response;
    } else if (response && typeof response === 'object') {
      // Try different possible wrapper properties
      channelsArray = response.channels || response.data || response.items || response.results || [];
    }
    
    if (channelsArray.length === 0) {
      console.warn('⚠️  No channels found in response');
      return [];
    }
    
    return channelsArray.map(ch => ({
      channelId: ch.channelId || ch.channel_id || ch.dataChannelId,
      channelName: ch.channelName || ch.channel_name || ch.name,
      deviceId: ch.deviceId || ch.device_id,
      organizationId: ch.organizationId || ch.organization_id,
      tariffId: ch.tariffId || ch.tariff_id || null,
    }));
  }
  
  /**
   * Determine best resolution to use
   */
  determineResolution(intervalPreferences) {
    // For now, return preferred resolution
    // In production, you might query the API to see what's available
    return intervalPreferences[0]; // Default to first preference (900s = 15min)
  }
  
  /**
   * Fetch readings for a channel and date range
   */
  async fetchReadings(channelId, startDate, endDate, resolution) {
    const fields = ['E', 'P', 'V', 'I', 'PF', 'T', 'kW', 'kWh']; // Energy, Power, Voltage, Current, PF, Temperature
    
    try {
      const readings = await this.client.getReadings(channelId.toString(), {
        fields,
        daterange: [toUnixTimestamp(startDate), toUnixTimestamp(endDate)],
        res: resolution.toString(),
        action: 'summarize',
      });
      
      // Handle different response formats - API returns readings in 'records' property
      let readingsArray = [];
      if (Array.isArray(readings)) {
        readingsArray = readings;
      } else if (readings && typeof readings === 'object') {
        // Try different wrapper properties (records is the main one for Eniscope API)
        readingsArray = readings.records || readings.data || readings.readings || readings.items || readings.result || [];
      }
      
      // Convert units: API returns Wh and W, we need kWh and kW
      // E (energy) is in Wh, P (power) is in W - divide by 1000 to get kWh and kW
      readingsArray = readingsArray.map(reading => ({
        ...reading,
        E: reading.E != null ? reading.E / 1000 : null, // Wh to kWh
        P: reading.P != null ? reading.P / 1000 : null, // W to kW
        energy_kwh: reading.E != null ? reading.E / 1000 : null,
        power_kw: reading.P != null ? reading.P / 1000 : null,
        kWh: reading.kWh != null ? reading.kWh / 1000 : reading.E != null ? reading.E / 1000 : null,
        kW: reading.kW != null ? reading.kW / 1000 : reading.P != null ? reading.P / 1000 : null,
      }));
      
      return readingsArray;
    } catch (error) {
      console.error(`Error fetching readings for channel ${channelId}:`, error.message);
      return [];
    }
  }
  
  /**
   * Fetch report period data for all channels
   */
  async fetchReportData(siteId, startDate, endDate, resolution) {
    console.log(`Fetching report data for period ${startDate.toISOString()} to ${endDate.toISOString()}...`);
    
    const channels = await this.fetchChannels(siteId);
    console.log(`Found ${channels.length} channels`);
    
    const channelsData = [];
    
    for (const channel of channels) {
      console.log(`  Fetching data for channel ${channel.channelId} (${channel.channelName})...`);
      
      const readings = await this.fetchReadings(channel.channelId, startDate, endDate, resolution);
      
      // Calculate expected intervals for completeness check
      const expectedTimestamps = generateExpectedTimestamps(startDate, endDate, resolution);
      
      channelsData.push({
        ...channel,
        readings,
        expectedIntervals: expectedTimestamps.length,
      });
      
      console.log(`    Retrieved ${readings.length} readings (expected ~${expectedTimestamps.length})`);
    }
    
    return channelsData;
  }
  
  /**
   * Fetch baseline data for all channels
   */
  async fetchBaselineData(siteId, startDate, endDate, resolution) {
    console.log(`Fetching baseline data for period ${startDate.toISOString()} to ${endDate.toISOString()}...`);
    
    const channels = await this.fetchChannels(siteId);
    const baselinesData = [];
    
    for (const channel of channels) {
      console.log(`  Fetching baseline for channel ${channel.channelId} (${channel.channelName})...`);
      
      const readings = await this.fetchReadings(channel.channelId, startDate, endDate, resolution);
      
      baselinesData.push({
        channelId: channel.channelId,
        channelName: channel.channelName,
        readings,
      });
      
      console.log(`    Retrieved ${readings.length} baseline readings`);
    }
    
    return baselinesData;
  }
  
  /**
   * Fetch alarms/events (if available)
   */
  async fetchAlarmsAndEvents(siteId, startDate, endDate) {
    console.log(`Fetching alarms and events...`);
    
    try {
      const alarms = await this.client.getAlarms({
        organization: siteId,
        // Note: API may not support date filtering on alarms
      });
      
      const events = await this.client.getEvents({
        organization: siteId,
        startTs: toUnixTimestamp(startDate),
      });
      
      return {
        alarms: Array.isArray(alarms) ? alarms : [],
        events: Array.isArray(events) ? events : [],
        source: 'api',
      };
    } catch (error) {
      console.warn('Could not fetch alarms/events:', error.message);
      return {
        alarms: [],
        events: [],
        source: 'unavailable',
      };
    }
  }
  
  /**
   * Fetch all data needed for report
   */
  async fetchAllData(siteId, reportPeriod, baselinePeriod) {
    console.log('='.repeat(60));
    console.log('FETCHING DATA FOR WEEKLY REPORT');
    console.log('='.repeat(60));
    
    // Determine resolution
    const resolution = this.determineResolution(this.config.intervalPreferences);
    console.log(`Using ${resolution}s (${resolution/60}min) interval resolution`);
    
    // Fetch metadata
    const siteMetadata = await this.fetchSiteMetadata(siteId);
    
    // Fetch report period data
    const reportData = await this.fetchReportData(
      siteId,
      reportPeriod.start,
      reportPeriod.end,
      resolution
    );
    
    // Fetch baseline data
    const baselineData = await this.fetchBaselineData(
      siteId,
      baselinePeriod.start,
      baselinePeriod.end,
      resolution
    );
    
    // Fetch alarms and events
    const alarmsAndEvents = await this.fetchAlarmsAndEvents(
      siteId,
      reportPeriod.start,
      reportPeriod.end
    );
    
    console.log('='.repeat(60));
    console.log('DATA FETCHING COMPLETE');
    console.log('='.repeat(60));
    
    return {
      siteMetadata,
      reportData,
      baselineData,
      alarmsAndEvents,
      resolution,
      reportPeriod,
      baselinePeriod,
    };
  }
}
