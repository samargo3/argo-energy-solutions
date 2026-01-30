#!/usr/bin/env node
/**
 * Energy Data Analysis Script
 * 
 * Connects to Eniscope Core API and performs data analysis
 * 
 * Usage:
 *   node scripts/analyze-energy-data.js
 */

import axios from 'axios';
import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.join(__dirname, '..', '.env') });

const ENISCOPE_API_URL = process.env.VITE_ENISCOPE_API_URL || process.env.VITE_BEST_ENERGY_API_URL || 'https://core.eniscope.com';
const ENISCOPE_API_KEY = process.env.VITE_ENISCOPE_API_KEY || process.env.VITE_BEST_ENERGY_API_KEY || '';
const ENISCOPE_EMAIL = process.env.VITE_ENISCOPE_EMAIL || '';
const ENISCOPE_PASSWORD = process.env.VITE_ENISCOPE_PASSWORD || '';

class EniscopeAPIClient {
  constructor() {
    this.sessionToken = null;
    this.apiKey = ENISCOPE_API_KEY;
    this.email = ENISCOPE_EMAIL;
    this.passwordMd5 = crypto.createHash('md5').update(ENISCOPE_PASSWORD).digest('hex');
    // Remove trailing slash if present
    this.baseUrl = ENISCOPE_API_URL.replace(/\/$/, '');

    if (!this.apiKey || !this.email || !ENISCOPE_PASSWORD) {
      throw new Error('Missing required environment variables. Please check your .env file.');
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
      
      if (!this.sessionToken) {
        console.warn('⚠️  Warning: No session token received. Will use Basic Auth for subsequent requests.');
      } else {
        console.log('✓ Authentication successful');
      }
    } catch (error) {
      console.error('❌ Authentication failed:', error.response?.data || error.message);
      throw error;
    }
  }

  async makeRequest(endpoint, params = {}, retries = 3) {
    const headers = {
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

    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const response = await axios.get(`${this.baseUrl}${endpoint}`, {
          headers,
          params,
        });
        return response.data;
      } catch (error) {
        if (error.response?.status === 429 && attempt < retries - 1) {
          const delay = Math.pow(2, attempt) * 1000; // Exponential backoff: 1s, 2s, 4s
          console.log(`⏳ Rate limited. Retrying in ${delay/1000}s... (attempt ${attempt + 1}/${retries})`);
          await new Promise(resolve => setTimeout(resolve, delay));
        } else {
          throw error;
        }
      }
    }
  }

  async getOrganizations() {
    return this.makeRequest('/organizations');
  }

  async getDevices(organizationId) {
    const params = organizationId ? { organization: organizationId } : {};
    return this.makeRequest('/devices', params);
  }

  async getChannels(organizationId, deviceId) {
    const params = {};
    if (organizationId) params.organization = organizationId;
    if (deviceId) params.deviceId = deviceId;
    return this.makeRequest('/channels', params);
  }

  async getReadings(channelId, options = {}) {
    const {
      fields = ['E', 'P', 'V', 'I'],
      daterange = 'lastweek',
      res = '3600',
      action = 'summarize',
    } = options;

    const params = {
      res,
      action,
    };

    // Add fields as array parameters
    fields.forEach(field => {
      if (!params['fields[]']) {
        params['fields[]'] = [];
      }
      params['fields[]'].push(field);
    });

    // Handle daterange
    if (Array.isArray(daterange)) {
      params['daterange[]'] = daterange;
    } else {
      params.daterange = daterange;
    }

    return this.makeRequest(`/readings/${channelId}`, params);
  }
}

function saveToFile(data, filename) {
  const outputDir = path.join(__dirname, '..', 'data');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const filepath = path.join(outputDir, filename);
  fs.writeFileSync(filepath, JSON.stringify(data, null, 2));
  console.log(`✓ Data saved to: ${filepath}`);
}

function analyzeEnergyData(readings) {
  if (!readings || readings.length === 0) {
    console.log('No readings data to analyze');
    return;
  }

  console.log('\n=== Energy Data Analysis ===');
  console.log(`Total readings: ${readings.length}`);

  // Calculate statistics if readings have energy data
  const energyValues = readings
    .map(r => r.E || r.energy || 0)
    .filter(v => typeof v === 'number' && !isNaN(v));

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
    .map(r => r.P || r.power || 0)
    .filter(v => typeof v === 'number' && !isNaN(v));

  if (powerValues.length > 0) {
    const avgPower = powerValues.reduce((sum, val) => sum + val, 0) / powerValues.length;
    const maxPower = Math.max(...powerValues);
    const minPower = Math.min(...powerValues);
    console.log(`\nPower Statistics:`);
    console.log(`  Average: ${avgPower.toFixed(2)} W`);
    console.log(`  Max: ${maxPower.toFixed(2)} W`);
    console.log(`  Min: ${minPower.toFixed(2)} W`);
  }

  // Voltage statistics
  const voltageValues = readings
    .map(r => r.V || r.voltage || 0)
    .filter(v => typeof v === 'number' && !isNaN(v));

  if (voltageValues.length > 0) {
    const avgVoltage = voltageValues.reduce((sum, val) => sum + val, 0) / voltageValues.length;
    console.log(`\nVoltage Statistics:`);
    console.log(`  Average: ${avgVoltage.toFixed(2)} V`);
  }
}

async function main() {
  console.log('🔌 Connecting to Eniscope Core API...\n');

  const client = new EniscopeAPIClient();

  try {
    // Authenticate
    await client.authenticate();

    // Get organizations
    console.log('\n📊 Fetching organizations...');
    const organizations = await client.getOrganizations();
    const orgList = organizations.organizations || organizations.data || (Array.isArray(organizations) ? organizations : [organizations]);
    console.log(`Found ${orgList.length} organization(s)`);
    saveToFile(organizations, 'organizations.json');

    // Small delay to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 500));

    // Get first organization if available
    if (orgList.length > 0) {
      const firstOrg = orgList[0];
      const orgId = firstOrg.organizationId;
      console.log(`   Organization: ${firstOrg.organizationName} (ID: ${orgId})`);

      console.log(`\n📱 Fetching devices for organization ${orgId}...`);
      const devices = await client.getDevices(orgId);
      const deviceList = devices.devices || devices.data || (Array.isArray(devices) ? devices : [devices]);
      console.log(`Found ${deviceList.length} device(s)`);
      saveToFile(devices, `devices-org-${orgId}.json`);

      await new Promise(resolve => setTimeout(resolve, 500));

      // Get channels
      console.log(`\n📡 Fetching channels for organization ${orgId}...`);
      const channels = await client.getChannels(orgId);
      const channelList = channels.channels || channels.data || (Array.isArray(channels) ? channels : [channels]);
      console.log(`Found ${channelList.length} channel(s)`);
      saveToFile(channels, `channels-org-${orgId}.json`);

      await new Promise(resolve => setTimeout(resolve, 500));

      // Get readings for first channel if available
      if (channelList.length > 0) {
        const firstChannel = channelList[0];
        const channelId = firstChannel.dataChannelId || firstChannel.channelId || firstChannel.id;
        console.log(`   Channel: ${firstChannel.channelName} (ID: ${channelId})`);

        console.log(`\n⚡ Fetching readings for channel ${channelId}...`);
        console.log('   (This may take a moment...)');
        
        const readings = await client.getReadings(channelId.toString(), {
          fields: ['E', 'P', 'V', 'I', 'PF'],
          daterange: 'lastweek',
          res: '3600',
          action: 'summarize',
        });

        const readingList = Array.isArray(readings) ? readings : (readings.records || readings.data || readings.result || []);
        console.log(`Found ${readingList.length} reading(s)`);
        saveToFile(readings, `readings-channel-${channelId}.json`);

        // Analyze the data
        analyzeEnergyData(readingList);
      } else {
        console.log('\n⚠️  No channels found. Cannot fetch readings.');
      }
    } else {
      console.log('\n⚠️  No organizations found.');
    }

    console.log('\n✅ Analysis complete!');
    console.log('📁 Check the /data directory for saved JSON files');

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', JSON.stringify(error.response.data, null, 2));
    }
    process.exit(1);
  }
}

// Run the main function
main();


