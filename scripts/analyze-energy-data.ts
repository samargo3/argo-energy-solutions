#!/usr/bin/env ts-node
/**
 * Energy Data Analysis Script
 * 
 * Connects to Eniscope Core API and performs data analysis
 * 
 * Usage:
 *   npm run analyze:energy
 *   or
 *   ts-node scripts/analyze-energy-data.ts
 */

import axios from 'axios';
import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables
import dotenv from 'dotenv';
dotenv.config({ path: path.join(__dirname, '..', '.env') });

const ENISCOPE_API_URL = process.env.VITE_ENISCOPE_API_URL || 'https://core.eniscope.com';
const ENISCOPE_API_KEY = process.env.VITE_ENISCOPE_API_KEY || '';
const ENISCOPE_EMAIL = process.env.VITE_ENISCOPE_EMAIL || '';
const ENISCOPE_PASSWORD = process.env.VITE_ENISCOPE_PASSWORD || '';

interface EniscopeClient {
  sessionToken: string | null;
  authenticate(): Promise<void>;
  getOrganizations(): Promise<any>;
  getDevices(organizationId?: string): Promise<any>;
  getChannels(organizationId?: string, deviceId?: string): Promise<any>;
  getReadings(channelId: string, params: any): Promise<any>;
}

class EniscopeAPIClient implements EniscopeClient {
  sessionToken: string | null = null;
  private apiKey: string;
  private email: string;
  private passwordMd5: string;
  private baseUrl: string;

  constructor() {
    this.apiKey = ENISCOPE_API_KEY;
    this.email = ENISCOPE_EMAIL;
    this.passwordMd5 = crypto.createHash('md5').update(ENISCOPE_PASSWORD).digest('hex');
    this.baseUrl = ENISCOPE_API_URL;

    if (!this.apiKey || !this.email || !ENISCOPE_PASSWORD) {
      throw new Error('Missing required environment variables: VITE_ENISCOPE_API_KEY, VITE_ENISCOPE_EMAIL, VITE_ENISCOPE_PASSWORD');
    }
  }

  async authenticate(): Promise<void> {
    const authString = `${this.email}:${this.passwordMd5}`;
    const authB64 = Buffer.from(authString).toString('base64');

    try {
      const response = await axios.get(`${this.baseUrl}/v1/1/organizations`, {
        headers: {
          'Authorization': `Basic ${authB64}`,
          'X-Eniscope-API': this.apiKey,
          'Accept': 'text/json',
        },
      });

      this.sessionToken = response.headers['x-eniscope-token'] || response.headers['X-Eniscope-Token'] || null;
      
      if (!this.sessionToken) {
        console.warn('Warning: No session token received. Will use Basic Auth for subsequent requests.');
      } else {
        console.log('✓ Authentication successful');
      }
    } catch (error: any) {
      console.error('Authentication failed:', error.response?.data || error.message);
      throw error;
    }
  }

  private async makeRequest(endpoint: string, params?: any): Promise<any> {
    const headers: any = {
      'X-Eniscope-API': this.apiKey,
      'Accept': 'text/json',
    };

    if (this.sessionToken) {
      headers['X-Eniscope-Token'] = this.sessionToken;
    } else {
      const authString = `${this.email}:${this.passwordMd5}`;
      const authB64 = Buffer.from(authString).toString('base64');
      headers['Authorization'] = `Basic ${authB64}`;
    }

    const response = await axios.get(`${this.baseUrl}${endpoint}`, {
      headers,
      params,
    });

    return response.data;
  }

  async getOrganizations(): Promise<any> {
    return this.makeRequest('/v1/1/organizations');
  }

  async getDevices(organizationId?: string): Promise<any> {
    const params = organizationId ? { organization: organizationId } : undefined;
    return this.makeRequest('/v1/1/devices', params);
  }

  async getChannels(organizationId?: string, deviceId?: string): Promise<any> {
    const params: any = {};
    if (organizationId) params.organization = organizationId;
    if (deviceId) params.deviceId = deviceId;
    return this.makeRequest('/v1/1/channels', Object.keys(params).length > 0 ? params : undefined);
  }

  async getReadings(channelId: string, params: {
    fields: string[];
    daterange?: string | [string, string];
    res?: string;
    action?: string;
  }): Promise<any> {
    const queryParams: any = {
      res: params.res || '3600',
      action: params.action || 'summarize',
    };

    params.fields.forEach((field) => {
      queryParams['fields[]'] = field;
    });

    if (params.daterange) {
      if (Array.isArray(params.daterange)) {
        queryParams['daterange[]'] = params.daterange[0];
        queryParams['daterange[]'] = params.daterange[1];
      } else {
        queryParams.daterange = params.daterange;
      }
    }

    return this.makeRequest(`/v1/1/readings/${channelId}`, queryParams);
  }
}

/**
 * Save data to JSON file for analysis
 */
function saveToFile(data: any, filename: string): void {
  const outputDir = path.join(__dirname, '..', 'data');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const filepath = path.join(outputDir, filename);
  fs.writeFileSync(filepath, JSON.stringify(data, null, 2));
  console.log(`✓ Data saved to: ${filepath}`);
}

/**
 * Analyze energy consumption data
 */
function analyzeEnergyData(readings: any[]): void {
  if (!readings || readings.length === 0) {
    console.log('No readings data to analyze');
    return;
  }

  console.log('\n=== Energy Data Analysis ===');
  console.log(`Total readings: ${readings.length}`);

  // Calculate statistics if readings have energy data
  const energyValues = readings
    .map((r: any) => r.E || r.energy || 0)
    .filter((v: number) => typeof v === 'number' && !isNaN(v));

  if (energyValues.length > 0) {
    const totalEnergy = energyValues.reduce((sum, val) => sum + val, 0);
    const avgEnergy = totalEnergy / energyValues.length;
    const maxEnergy = Math.max(...energyValues);
    const minEnergy = Math.min(...energyValues);

    console.log(`\nEnergy Statistics:`);
    console.log(`  Total: ${totalEnergy.toFixed(2)} Wh`);
    console.log(`  Average: ${avgEnergy.toFixed(2)} Wh`);
    console.log(`  Max: ${maxEnergy.toFixed(2)} Wh`);
    console.log(`  Min: ${minEnergy.toFixed(2)} Wh`);
  }

  // Power statistics
  const powerValues = readings
    .map((r: any) => r.P || r.power || 0)
    .filter((v: number) => typeof v === 'number' && !isNaN(v));

  if (powerValues.length > 0) {
    const avgPower = powerValues.reduce((sum, val) => sum + val, 0) / powerValues.length;
    const maxPower = Math.max(...powerValues);
    console.log(`\nPower Statistics:`);
    console.log(`  Average: ${avgPower.toFixed(2)} W`);
    console.log(`  Max: ${maxPower.toFixed(2)} W`);
  }
}

/**
 * Main analysis function
 */
async function main() {
  console.log('🔌 Connecting to Eniscope Core API...\n');

  const client = new EniscopeAPIClient();

  try {
    // Authenticate
    await client.authenticate();

    // Get organizations
    console.log('\n📊 Fetching organizations...');
    const organizations = await client.getOrganizations();
    console.log(`Found ${Array.isArray(organizations) ? organizations.length : 'unknown'} organizations`);
    saveToFile(organizations, 'organizations.json');

    // Get first organization if available
    const orgList = Array.isArray(organizations) ? organizations : (organizations.result || []);
    if (orgList.length > 0) {
      const firstOrg = orgList[0];
      const orgId = firstOrg.organizationId || firstOrg.id;

      console.log(`\n📱 Fetching devices for organization ${orgId}...`);
      const devices = await client.getDevices(orgId);
      const deviceList = Array.isArray(devices) ? devices : (devices.result || []);
      console.log(`Found ${deviceList.length} devices`);
      saveToFile(devices, `devices-org-${orgId}.json`);

      // Get channels
      console.log(`\n📡 Fetching channels for organization ${orgId}...`);
      const channels = await client.getChannels(orgId);
      const channelList = Array.isArray(channels) ? channels : (channels.result || []);
      console.log(`Found ${channelList.length} channels`);
      saveToFile(channels, `channels-org-${orgId}.json`);

      // Get readings for first channel if available
      if (channelList.length > 0) {
        const firstChannel = channelList[0];
        const channelId = firstChannel.channelId || firstChannel.id;

        console.log(`\n⚡ Fetching readings for channel ${channelId}...`);
        const readings = await client.getReadings(channelId.toString(), {
          fields: ['E', 'P', 'V', 'I', 'PF'],
          daterange: 'lastweek',
          res: '3600',
          action: 'summarize',
        });

        const readingList = Array.isArray(readings) ? readings : (readings.result || readings.data || []);
        console.log(`Found ${readingList.length} readings`);
        saveToFile(readings, `readings-channel-${channelId}.json`);

        // Analyze the data
        analyzeEnergyData(readingList);
      }
    }

    console.log('\n✅ Analysis complete!');
    console.log('📁 Check the /data directory for saved JSON files');

  } catch (error: any) {
    console.error('\n❌ Error:', error.message);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', JSON.stringify(error.response.data, null, 2));
    }
    process.exit(1);
  }
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { EniscopeAPIClient, analyzeEnergyData };


