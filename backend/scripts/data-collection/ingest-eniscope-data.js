#!/usr/bin/env node

/**
 * Eniscope Data Ingestion Script
 * 
 * Pulls data from Eniscope API and stores it in SQLite database
 * 
 * Usage:
 *   node scripts/ingest-eniscope-data.js [--full] [--incremental] [--days=30]
 * 
 * Options:
 *   --full: Full ingestion (all historical data)
 *   --incremental: Only fetch new data since last ingestion (default)
 *   --days=N: Number of days to fetch (default: 30)
 */

import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import axios from 'axios';
import CryptoJS from 'crypto-js';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import dotenv from 'dotenv';

// Load environment variables - explicitly set path to match working scripts
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
dotenv.config({ path: join(__dirname, '..', '.env') });

// Debug: Log what environment variables are available (without values)
if (process.env.DEBUG) {
  console.log('🔍 Environment variables check:');
  console.log('   VITE_ENISCOPE_API_URL:', process.env.VITE_ENISCOPE_API_URL ? '✓ Set' : '✗ Missing');
  console.log('   VITE_ENISCOPE_API_KEY:', process.env.VITE_ENISCOPE_API_KEY ? '✓ Set (' + process.env.VITE_ENISCOPE_API_KEY.substring(0, 8) + '...)' : '✗ Missing');
  console.log('   VITE_BEST_ENERGY_API_KEY:', process.env.VITE_BEST_ENERGY_API_KEY ? '✓ Set (' + process.env.VITE_BEST_ENERGY_API_KEY.substring(0, 8) + '...)' : '✗ Missing');
  console.log('   VITE_ENISCOPE_EMAIL:', process.env.VITE_ENISCOPE_EMAIL ? '✓ Set' : '✗ Missing');
  console.log('   VITE_ENISCOPE_PASSWORD:', process.env.VITE_ENISCOPE_PASSWORD ? '✓ Set' : '✗ Missing');
  console.log('   ENISCOPE_API_KEY:', process.env.ENISCOPE_API_KEY ? '✓ Set' : '✗ Missing');
  console.log('   ENISCOPE_EMAIL:', process.env.ENISCOPE_EMAIL ? '✓ Set' : '✗ Missing');
  console.log('   ENISCOPE_PASSWORD:', process.env.ENISCOPE_PASSWORD ? '✓ Set' : '✗ Missing');
  console.log('');
}

// Create a Node.js compatible Eniscope API client
// (since the main one uses import.meta.env which is Vite-specific)
class NodeEniscopeAPIClient {
  constructor() {
    // Use the same base URL as your working scripts (core.eniscope.com)
    // Check multiple possible variable names (matching your working scripts)
    const apiUrl = process.env.VITE_ENISCOPE_API_URL || process.env.VITE_BEST_ENERGY_API_URL || process.env.ENISCOPE_API_URL || 'https://core.eniscope.com';
    this.apiUrl = apiUrl.replace(/\/$/, ''); // Remove trailing slash
    this.apiKey = process.env.VITE_ENISCOPE_API_KEY || process.env.VITE_BEST_ENERGY_API_KEY || process.env.ENISCOPE_API_KEY || '';
    this.email = process.env.VITE_ENISCOPE_EMAIL || process.env.ENISCOPE_EMAIL || '';
    this.password = process.env.VITE_ENISCOPE_PASSWORD || process.env.ENISCOPE_PASSWORD || '';
    this.passwordMd5 = CryptoJS.MD5(this.password).toString();
    this.sessionToken = null;
    
    // Validate required credentials
    if (!this.apiKey || !this.email || !this.password) {
      const missing = [];
      if (!this.apiKey) missing.push('API_KEY (VITE_ENISCOPE_API_KEY, VITE_BEST_ENERGY_API_KEY, or ENISCOPE_API_KEY)');
      if (!this.email) missing.push('EMAIL (VITE_ENISCOPE_EMAIL or ENISCOPE_EMAIL)');
      if (!this.password) missing.push('PASSWORD (VITE_ENISCOPE_PASSWORD or ENISCOPE_PASSWORD)');
      
      console.error('\n❌ Missing required environment variables:');
      console.error('   Missing:', missing.join(', '));
      console.error('\n💡 Please check your .env file has one of these sets:');
      console.error('   VITE_ENISCOPE_API_KEY=your_key');
      console.error('   VITE_ENISCOPE_EMAIL=your_email');
      console.error('   VITE_ENISCOPE_PASSWORD=your_password');
      console.error('\n   OR:');
      console.error('   ENISCOPE_API_KEY=your_key');
      console.error('   ENISCOPE_EMAIL=your_email');
      console.error('   ENISCOPE_PASSWORD=your_password');
      console.error(`\n   Current .env file location: ${process.cwd()}/.env`);
      console.error('   To debug, run with: DEBUG=1 npm run ingest:full\n');
      throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
    }
  }

  async authenticate() {
    try {
      const authString = `${this.email}:${this.passwordMd5}`;
      const authB64 = Buffer.from(authString).toString('base64');

      // Use /organizations endpoint (matches your working scripts like wilson-center-analysis.js)
      const endpoint = `${this.apiUrl}/organizations`;
      const response = await axios.get(endpoint, {
        headers: {
          'Authorization': `Basic ${authB64}`,
          'X-Eniscope-API': this.apiKey,
          'Accept': 'text/json',
        },
      });

      this.sessionToken = response.headers['x-eniscope-token'] || response.headers['X-Eniscope-Token'] || null;
      return this.sessionToken;
    } catch (error) {
      if (error.response) {
        console.error('❌ Authentication failed:');
        console.error(`   Status: ${error.response.status} ${error.response.statusText}`);
        console.error(`   URL: ${error.config?.url}`);
        console.error(`   Response:`, error.response.data);
        if (error.response.status === 403) {
          console.error('\n💡 403 Forbidden usually means:');
          console.error('   - API key is invalid or missing');
          console.error('   - Email/password credentials are incorrect');
          console.error('   - Account doesn\'t have permission to access organizations');
          console.error('   - Check your .env file has correct VITE_ENISCOPE_API_KEY, VITE_ENISCOPE_EMAIL, VITE_ENISCOPE_PASSWORD');
          console.error(`   - Current API URL: ${this.apiUrl}`);
        }
      } else {
        console.error('❌ Authentication failed:', error.message);
      }
      throw error;
    }
  }

  async makeRequest(method, endpoint, params = {}) {
    if (!this.sessionToken && endpoint !== '/organizations') {
      await this.authenticate();
    }

    const config = {
      method,
      url: `${this.apiUrl}${endpoint}`,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/json',
        'X-Eniscope-API': this.apiKey,
      },
    };

    if (this.sessionToken) {
      config.headers['X-Eniscope-Token'] = this.sessionToken;
    } else {
      const authString = `${this.email}:${this.passwordMd5}`;
      const authB64 = Buffer.from(authString).toString('base64');
      config.headers['Authorization'] = `Basic ${authB64}`;
    }

    if (method === 'get') {
      config.params = params;
    } else {
      config.data = params;
    }

    try {
      const response = await axios(config);
      const token = response.headers['x-eniscope-token'] || response.headers['X-Eniscope-Token'];
      if (token) {
        this.sessionToken = token;
      }
      return response.data;
    } catch (error) {
      if (error.response?.status === 401 || error.response?.status === 419) {
        this.sessionToken = null;
        await this.authenticate();
        // Retry once
        return this.makeRequest(method, endpoint, params);
      }
      throw error;
    }
  }

  async getOrganizations(params) {
    return this.makeRequest('get', '/organizations', params);
  }

  async getDevices(params) {
    // Try /devices first (simpler), fallback to /v1/1/devices if needed
    return this.makeRequest('get', '/devices', params);
  }

  async getChannels(params) {
    // Try /channels first (simpler), fallback to /v1/1/channels if needed
    return this.makeRequest('get', '/channels', params);
  }

  async getReadings(channelId, params) {
    const queryParams = {
      res: params.res || '3600',
      action: params.action || 'summarize',
      showCounters: params.showCounters ? '1' : '0',
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

    return this.makeRequest('get', `/readings/${channelId}`, queryParams);
  }
}

const eniscopeApi = new NodeEniscopeAPIClient();

const DB_PATH = join(__dirname, '../data/eniscope.db');

class EniscopeDataIngestion {
  constructor() {
    this.db = null;
    this.stats = {
      organizations: 0,
      devices: 0,
      channels: 0,
      readings: 0,
      errors: 0,
    };
  }

  async initialize() {
    console.log('🔄 Initializing database connection...');
    
    this.db = await open({
      filename: DB_PATH,
      driver: sqlite3.Database,
    });

    await this.setupSchema();
    console.log('✅ Database initialized');
  }

  async setupSchema() {
    // Organizations table
    await this.db.exec(`
      CREATE TABLE IF NOT EXISTS organizations (
        organization_id TEXT PRIMARY KEY,
        organization_name TEXT NOT NULL,
        parent_id TEXT,
        address1 TEXT,
        city TEXT,
        country TEXT,
        default_email_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Devices table
    await this.db.exec(`
      CREATE TABLE IF NOT EXISTS devices (
        device_id INTEGER PRIMARY KEY,
        device_name TEXT NOT NULL,
        device_type_id INTEGER,
        device_type_name TEXT,
        organization_id INTEGER,
        uuid TEXT UNIQUE,
        status INTEGER,
        registered TEXT,
        expires TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Channels table
    await this.db.exec(`
      CREATE TABLE IF NOT EXISTS channels (
        channel_id INTEGER PRIMARY KEY,
        channel_name TEXT NOT NULL,
        device_id INTEGER,
        organization_id INTEGER,
        tariff_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES devices(device_id),
        FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
      )
    `);

    // Readings table (time-series data)
    await this.db.exec(`
      CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        energy_kwh REAL,
        power_kw REAL,
        voltage_v REAL,
        current_a REAL,
        power_factor REAL,
        temperature_c REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (channel_id) REFERENCES channels(channel_id)
      )
    `);

    // Create indexes for performance
    await this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_readings_channel_timestamp 
      ON readings(channel_id, timestamp);
      
      CREATE INDEX IF NOT EXISTS idx_readings_timestamp 
      ON readings(timestamp);
      
      CREATE INDEX IF NOT EXISTS idx_devices_organization 
      ON devices(organization_id);
      
      CREATE INDEX IF NOT EXISTS idx_channels_device 
      ON channels(device_id);
      
      CREATE INDEX IF NOT EXISTS idx_channels_organization 
      ON channels(organization_id);
    `);

    console.log('✅ Database schema created/verified');
  }

  async ingestOrganizations() {
    console.log('📥 Ingesting organizations...');
    
    try {
      const orgs = await eniscopeApi.getOrganizations();
      
      // Handle different response formats
      // Based on your data files, the response has { organizations: [...], meta: {...} }
      let orgsArray = [];
      if (Array.isArray(orgs)) {
        orgsArray = orgs;
      } else if (orgs && typeof orgs === 'object') {
        // Check for the actual response structure from your data
        orgsArray = orgs.organizations || orgs.data || orgs.items || orgs.results || [];
        if (orgsArray.length === 0 && Object.keys(orgs).length > 0) {
          // Might be a single organization object
          orgsArray = [orgs];
        }
      }
      
      if (orgsArray.length === 0) {
        console.warn('⚠️  No organizations found in response');
        console.warn('   Response type:', typeof orgs);
        console.warn('   Response keys:', orgs && typeof orgs === 'object' ? Object.keys(orgs) : 'N/A');
        return;
      }

      for (const org of orgsArray) {
        try {
          await this.db.run(`
            INSERT OR REPLACE INTO organizations 
            (organization_id, organization_name, parent_id, address1, city, country, default_email_address, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
          `, [
            org.organizationId || org.organization_id,
            org.organizationName || org.organization_name,
            org.parentId || org.parent_id || null,
            org.address1 || null,
            org.city || null,
            org.country || null,
            org.defaultEmailAddress || org.default_email_address || null,
          ]);
          this.stats.organizations++;
        } catch (error) {
          console.error(`❌ Error ingesting organization ${org.organizationId}:`, error.message);
          this.stats.errors++;
        }
      }
      
      console.log(`✅ Ingested ${this.stats.organizations} organizations`);
    } catch (error) {
      console.error('❌ Error fetching organizations:', error.message);
      this.stats.errors++;
    }
  }

  async ingestDevices(organizationId) {
    try {
      const devices = await eniscopeApi.getDevices({ organization: organizationId });
      
      if (!Array.isArray(devices)) {
        return;
      }

      for (const device of devices) {
        try {
          await this.db.run(`
            INSERT OR REPLACE INTO devices 
            (device_id, device_name, device_type_id, device_type_name, organization_id, uuid, status, registered, expires, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
          `, [
            device.deviceId || device.device_id,
            device.deviceName || device.device_name,
            device.deviceTypeId || device.device_type_id || null,
            device.deviceTypeName || device.device_type_name || null,
            device.organizationId || device.organization_id,
            device.uuId || device.uuid || null,
            device.status || null,
            device.registered || null,
            device.expires || null,
          ]);
          this.stats.devices++;
        } catch (error) {
          console.error(`❌ Error ingesting device ${device.deviceId}:`, error.message);
          this.stats.errors++;
        }
      }
    } catch (error) {
      console.error(`❌ Error fetching devices for org ${organizationId}:`, error.message);
      this.stats.errors++;
    }
  }

  async ingestChannels(organizationId) {
    try {
      const channels = await eniscopeApi.getChannels({ organization: organizationId });
      
      if (!Array.isArray(channels)) {
        return;
      }

      for (const channel of channels) {
        try {
          await this.db.run(`
            INSERT OR REPLACE INTO channels 
            (channel_id, channel_name, device_id, organization_id, tariff_id, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
          `, [
            channel.channelId || channel.channel_id,
            channel.channelName || channel.channel_name,
            channel.deviceId || channel.device_id,
            channel.organizationId || channel.organization_id,
            channel.tariffId || channel.tariff_id || null,
          ]);
          this.stats.channels++;
        } catch (error) {
          console.error(`❌ Error ingesting channel ${channel.channelId}:`, error.message);
          this.stats.errors++;
        }
      }
    } catch (error) {
      console.error(`❌ Error fetching channels for org ${organizationId}:`, error.message);
      this.stats.errors++;
    }
  }

  async ingestReadings(channelId, startDate, endDate) {
    try {
      const readings = await eniscopeApi.getReadings(channelId.toString(), {
        fields: ['E', 'P', 'V', 'I', 'PF', 'T'],
        daterange: [startDate, endDate],
        res: '3600', // 1-hour resolution
        action: 'summarize',
      });

      // Handle different response formats
      let readingsArray = [];
      if (Array.isArray(readings)) {
        readingsArray = readings;
      } else if (readings && typeof readings === 'object') {
        // Check for common response wrappers
        readingsArray = readings.data || readings.readings || readings.items || [readings];
      }

      if (readingsArray.length === 0) {
        return;
      }

      // Use transaction for better performance
      await this.db.exec('BEGIN TRANSACTION');
      
      try {
        for (const reading of readingsArray) {
          const timestamp = reading.ts || reading.timestamp || reading.time;
          if (!timestamp) continue;

          await this.db.run(`
            INSERT OR REPLACE INTO readings 
            (channel_id, timestamp, energy_kwh, power_kw, voltage_v, current_a, power_factor, temperature_c)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
          `, [
            channelId,
            timestamp,
            reading.E || reading.energy || reading.energy_kwh || null,
            reading.P || reading.power || reading.power_kw || null,
            reading.V || reading.voltage || reading.voltage_v || null,
            reading.I || reading.current || reading.current_a || null,
            reading.PF || reading.power_factor || reading.powerFactor || null,
            reading.T || reading.temperature || reading.temperature_c || null,
          ]);
          this.stats.readings++;
        }
        
        await this.db.exec('COMMIT');
      } catch (error) {
        await this.db.exec('ROLLBACK');
        throw error;
      }
    } catch (error) {
      console.error(`❌ Error ingesting readings for channel ${channelId}:`, error.message);
      this.stats.errors++;
    }
  }

  async getLastIngestionTime(channelId) {
    const result = await this.db.get(
      'SELECT MAX(timestamp) as last_timestamp FROM readings WHERE channel_id = ?',
      [channelId]
    );
    return result?.last_timestamp || null;
  }

  async runIngestion(options = {}) {
    const { full = false, incremental = true, days = 30 } = options;
    
    console.log('🔄 Starting Eniscope data ingestion...');
    console.log(`Mode: ${full ? 'FULL' : 'INCREMENTAL'}`);
    console.log(`Days to fetch: ${days}`);

    // 1. Ingest organizations
    await this.ingestOrganizations();

    // 2. Get all organizations and ingest their devices
    const orgs = await this.db.all('SELECT organization_id FROM organizations');
    console.log(`📥 Found ${orgs.length} organizations, ingesting devices...`);
    
    for (const org of orgs) {
      await this.ingestDevices(org.organization_id);
    }

    // 3. Ingest channels for all organizations
    console.log(`📥 Ingesting channels for ${orgs.length} organizations...`);
    for (const org of orgs) {
      await this.ingestChannels(org.organization_id);
    }

    // 4. Ingest readings for all channels
    const channels = await this.db.all('SELECT channel_id FROM channels');
    console.log(`📥 Found ${channels.length} channels, ingesting readings...`);

    const endDate = new Date().toISOString();
    const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();

    for (const channel of channels) {
      let fetchStartDate = startDate;
      
      // For incremental mode, start from last ingestion
      if (incremental && !full) {
        const lastTimestamp = await this.getLastIngestionTime(channel.channel_id);
        if (lastTimestamp) {
          fetchStartDate = new Date(new Date(lastTimestamp).getTime() + 1000).toISOString();
        }
      }

      try {
        await this.ingestReadings(channel.channel_id, fetchStartDate, endDate);
        process.stdout.write(`\r✅ Processed ${this.stats.readings} readings...`);
      } catch (error) {
        console.error(`\n❌ Error processing channel ${channel.channel_id}:`, error.message);
      }
    }

    console.log('\n');
    console.log('========================================');
    console.log('📊 INGESTION SUMMARY');
    console.log('========================================');
    console.log(`Organizations: ${this.stats.organizations}`);
    console.log(`Devices: ${this.stats.devices}`);
    console.log(`Channels: ${this.stats.channels}`);
    console.log(`Readings: ${this.stats.readings}`);
    console.log(`Errors: ${this.stats.errors}`);
    console.log('========================================');
  }

  async close() {
    if (this.db) {
      await this.db.close();
      console.log('✅ Database connection closed');
    }
  }
}

// Main execution
async function main() {
  const args = process.argv.slice(2);
  const options = {
    full: args.includes('--full'),
    incremental: args.includes('--incremental') || !args.includes('--full'),
    days: parseInt(args.find(arg => arg.startsWith('--days='))?.split('=')[1] || '30'),
  };

  const ingestion = new EniscopeDataIngestion();
  
  try {
    await ingestion.initialize();
    await ingestion.runIngestion(options);
  } catch (error) {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  } finally {
    await ingestion.close();
  }
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { EniscopeDataIngestion };
