#!/usr/bin/env node

/**
 * Eniscope Data Ingestion to PostgreSQL (Neon)
 * 
 * Pulls data from Eniscope API and stores it in PostgreSQL database
 * 
 * Usage:
 *   node ingest-to-postgres.js --site=23271 --days=90
 */

import pg from 'pg';
import axios from 'axios';
import crypto from 'crypto';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.join(__dirname, '..', '..', '..', '.env') });

const { Pool } = pg;

// Eniscope API Client
class EniscopeClient {
  constructor() {
    this.baseUrl = (process.env.VITE_ENISCOPE_API_URL || 'https://core.eniscope.com').replace(/\/$/, '');
    this.apiKey = process.env.VITE_ENISCOPE_API_KEY;
    this.email = process.env.VITE_ENISCOPE_EMAIL;
    this.password = process.env.VITE_ENISCOPE_PASSWORD;
    this.passwordMd5 = crypto.createHash('md5').update(this.password).digest('hex');
    this.sessionToken = null;
  }

  async authenticate() {
    if (this.sessionToken) return this.cachedOrganizations || [];

    const authString = `${this.email}:${this.passwordMd5}`;
    const authB64 = Buffer.from(authString).toString('base64');
    
    try {
      const response = await axios.get(`${this.baseUrl}/organizations`, {
        headers: {
          'Authorization': `Basic ${authB64}`,
          'X-Eniscope-API': this.apiKey,
          'Accept': 'text/json'
        }
      });

      this.sessionToken = response.headers['x-eniscope-token'] || response.headers['X-Eniscope-Token'] || null;
      this.cachedOrganizations = response.data; // Cache organizations from auth call
      return this.cachedOrganizations;
    } catch (error) {
      console.error('Authentication failed:', error.response?.data || error.message);
      throw error;
    }
  }

  async getOrganizations() {
    // Return cached orgs from authentication to avoid extra API call
    if (this.cachedOrganizations) {
      return this.cachedOrganizations;
    }
    return await this.authenticate();
  }

  async makeRequestWithRetry(url, config, retries = 3) {
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        return await axios.get(url, config);
      } catch (error) {
        if (error.response?.status === 429 && attempt < retries - 1) {
          const delay = Math.pow(2, attempt + 3) * 1000; // 8s, 16s, 32s
          console.log(`\n   Rate limited. Waiting ${delay/1000}s before retry...`);
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

  async getChannels(organizationId) {
    await this.authenticate();
    const response = await this.makeRequestWithRetry(`${this.baseUrl}/channels`, {
      params: { organization: organizationId },
      headers: {
        'X-Eniscope-API': this.apiKey,
        'X-Eniscope-Token': this.sessionToken,
        'Accept': 'text/json'
      }
    });
    
    // Handle various response formats
    if (Array.isArray(response.data)) {
      return response.data;
    } else if (response.data?.channels) {
      return response.data.channels;
    } else if (response.data?.data) {
      return response.data.data;
    }
    return [];
  }

  async getReadings(channelId, options = {}) {
    await this.authenticate();
    
    const params = {
      action: 'summarize',
      res: options.resolution || '900' // 15 minutes in seconds
    };
    
    // Add fields
    if (options.fields && Array.isArray(options.fields)) {
      options.fields.forEach(field => {
        if (!params['fields[]']) {
          params['fields[]'] = [];
        }
        params['fields[]'].push(field);
      });
    }
    
    // Add daterange as array
    if (options.daterange) {
      const dates = options.daterange.split('/');
      params['daterange[]'] = dates.map(d => Math.floor(new Date(d).getTime() / 1000));
    }
    
    const response = await this.makeRequestWithRetry(`${this.baseUrl}/readings/${channelId}`, {
      params,
      headers: {
        'X-Eniscope-API': this.apiKey,
        'X-Eniscope-Token': this.sessionToken,
        'Accept': 'text/json'
      }
    });

    let readings = [];
    if (Array.isArray(response.data)) {
      readings = response.data;
    } else if (response.data?.records) {
      readings = response.data.records;
    } else if (response.data?.data) {
      readings = response.data.data;
    } else if (response.data?.result) {
      readings = response.data.result;
    }

    // Skip if no readings
    if (!Array.isArray(readings) || readings.length === 0) {
      return [];
    }

    // Debug: Log first reading to see structure (first 3 channels only)
    if (readings.length > 0) {
      const firstReading = readings[0];
      console.log(`\n   API Response - First reading keys: ${Object.keys(firstReading).join(', ')}`);
    }

    // Convert units: Wh -> kWh, W -> kW
    return readings.map(r => ({
      ...r,
      t: r.ts || r.t || r.timestamp || r.time, // Normalize timestamp field (API uses 'ts')
      E: r.E != null ? r.E / 1000 : null,
      P: r.P != null ? r.P / 1000 : null
    }));
  }
}

// Database functions
async function upsertOrganization(pool, org, orgId) {
  const id = String(orgId || org.organization_id || org.id);
  const name = org.organization_name || org.name || org.organizationname || `Organization ${id}`;
  
  await pool.query(`
    INSERT INTO organizations (
      organization_id, organization_name, address, city, postcode, country, updated_at
    ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
    ON CONFLICT (organization_id) 
    DO UPDATE SET 
      organization_name = EXCLUDED.organization_name,
      updated_at = NOW()
  `, [
    id,
    name,
    org.address || null,
    org.city || null,
    org.postcode || null,
    org.country || null
  ]);
}

async function upsertChannel(pool, channel, organizationId) {
  // Extract channel ID using correct field names
  const channelId = channel.channelId || channel.dataChannelId || channel.channel_id || channel.id;
  const channelName = channel.channelName || channel.channel_name || channel.name || `Channel ${channelId}`;
  const deviceId = channel.deviceId || channel.device_id || channel.device;
  
  // Skip if no valid channel ID
  if (!channelId) {
    console.log(`   ⚠️  Skipping channel with no ID`);
    return false;
  }
  
  try {
    // Don't include device_id to avoid foreign key constraint issues
    await pool.query(`
      INSERT INTO channels (
        channel_id, channel_name, organization_id, channel_type, unit, updated_at
      ) VALUES ($1, $2, $3, $4, $5, NOW())
      ON CONFLICT (channel_id)
      DO UPDATE SET
        channel_name = EXCLUDED.channel_name,
        updated_at = NOW()
    `, [
      parseInt(channelId),
      channelName,
      String(organizationId),
      channel.type || 'energy',
      channel.unit || 'kWh'
    ]);
    
    return true;
  } catch (error) {
    console.log(`   ⚠️  Error storing channel ${channelId}: ${error.message}`);
    return false;
  }
}

async function insertReadings(pool, channelId, readings) {
  if (readings.length === 0) return 0;

  const batchSize = 1000;
  let inserted = 0;

  for (let i = 0; i < readings.length; i += batchSize) {
    const batch = readings.slice(i, Math.min(i + batchSize, readings.length));
    
    const values = batch.map((r, idx) => {
      const offset = idx * 7;
      return `($${offset+1}, $${offset+2}, $${offset+3}, $${offset+4}, $${offset+5}, $${offset+6}, $${offset+7})`;
    }).join(',');

    const params = batch.flatMap(r => {
      // Handle timestamp - could be Unix timestamp (number) or ISO string
      let timestamp;
      if (typeof r.t === 'number') {
        timestamp = new Date(r.t * 1000); // Unix timestamp in seconds
      } else if (typeof r.t === 'string') {
        timestamp = new Date(r.t); // ISO string
      } else if (r.timestamp) {
        timestamp = new Date(r.timestamp);
      } else {
        timestamp = null;
      }
      
      return [
        channelId,
        timestamp,
        r.E || null,
        r.P || null,
        r.V || null,
        r.I || null,
        r.PF || null
      ];
    });

    try {
      const result = await pool.query(`
        INSERT INTO readings (
          channel_id, timestamp, energy_kwh, power_kw, voltage_v, current_a, power_factor
        ) VALUES ${values}
        ON CONFLICT (channel_id, timestamp) DO NOTHING
      `, params);

      inserted += result.rowCount || 0;
    } catch (error) {
      console.error(`Error inserting batch: ${error.message}`);
    }
  }

  return inserted;
}

// Main ingestion function
async function ingestData() {
  console.log('🌐 Eniscope → PostgreSQL Data Ingestion\n');

  // Parse command line arguments
  const args = process.argv.slice(2);
  const siteArg = args.find(arg => arg.startsWith('--site='));
  const daysArg = args.find(arg => arg.startsWith('--days='));

  const siteId = siteArg ? siteArg.split('=')[1] : '23271'; // Default to Wilson Center
  const days = daysArg ? parseInt(daysArg.split('=')[1]) : 90;

  console.log(`📊 Site ID: ${siteId}`);
  console.log(`📅 Days to fetch: ${days}\n`);

  // Check environment
  if (!process.env.DATABASE_URL) {
    console.error('❌ DATABASE_URL not found in .env');
    process.exit(1);
  }

  // Initialize
  const client = new EniscopeClient();
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false },
    max: 10
  });

  try {
    // Test connection
    await pool.query('SELECT NOW()');
    console.log('✅ Connected to PostgreSQL\n');

    // Authenticate with Eniscope
    await client.authenticate();
    console.log('✅ Authenticated with Eniscope\n');

    // Get organization info
    console.log('📋 Fetching organization...');
    let orgsData = await client.getOrganizations();
    
    // Handle various response formats
    let orgs = [];
    if (Array.isArray(orgsData)) {
      orgs = orgsData;
    } else if (orgsData && typeof orgsData === 'object') {
      orgs = orgsData.organizations || orgsData.data || orgsData.items || [orgsData];
    }
    
    const org = orgs.find(o => (o.organization_id || o.id) == siteId) || orgs[0];
    
    if (!org) {
      throw new Error(`Organization ${siteId} not found`);
    }

    await upsertOrganization(pool, org, siteId);
    console.log(`✅ Organization: ${org.organization_name || org.name || `Site ${siteId}`}\n`);

    // Get channels
    console.log('🔌 Fetching channels...');
    const allChannels = await client.getChannels(siteId);
    console.log(`✅ Found ${allChannels.length} channels\n`);

    // Store channels (filter out invalid ones)
    const validChannels = [];
    for (const channel of allChannels) {
      const success = await upsertChannel(pool, channel, siteId);
      if (success) {
        validChannels.push(channel);
      }
    }
    console.log(`✅ ${validChannels.length} valid channels stored\n`);
    
    // Use only valid channels for data fetching
    const channels = validChannels;

    // Calculate date range
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    const dateRange = `${startDate.toISOString().split('T')[0]}/${endDate.toISOString().split('T')[0]}`;
    
    console.log(`📅 Date range: ${dateRange}\n`);
    console.log('📥 Fetching readings...\n');

    // Fetch and store readings for each channel
    let totalReadings = 0;
    const startTime = Date.now();

    for (let i = 0; i < channels.length; i++) {
      const channel = channels[i];
      const channelId = channel.channelId || channel.dataChannelId || channel.channel_id || channel.id;
      const channelName = channel.channelName || channel.channel_name || channel.name || `Channel ${channelId}`;

      process.stdout.write(`   [${i+1}/${channels.length}] ${channelName}... `);

      try {
        const readings = await client.getReadings(channelId, {
          fields: ['E', 'P', 'V', 'I', 'PF'],
          daterange: dateRange,
          resolution: '900' // 15 minutes in seconds
        });

        const inserted = await insertReadings(pool, channelId, readings);
        totalReadings += inserted;

        console.log(`✅ ${inserted.toLocaleString()} readings`);

        // Delay to avoid rate limiting (1-2 seconds per channel)
        await new Promise(resolve => setTimeout(resolve, 1500));

      } catch (error) {
        console.log(`❌ ${error.message}`);
      }
    }

    const duration = ((Date.now() - startTime) / 1000).toFixed(1);

    console.log(`\n✅ Ingestion complete!`);
    console.log(`   Total readings: ${totalReadings.toLocaleString()}`);
    console.log(`   Duration: ${duration}s\n`);

    // Verify
    const countResult = await pool.query('SELECT COUNT(*) FROM readings');
    console.log(`📊 Total readings in database: ${parseInt(countResult.rows[0].count).toLocaleString()}\n`);

    console.log('💡 Next steps:');
    console.log('   1. Generate report: npm run report:weekly -- --site 23271 --db postgres');
    console.log('   2. Set up daily sync: Add to crontab\n');

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    console.error(error.stack);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

ingestData();
