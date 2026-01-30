#!/usr/bin/env node
/**
 * Data Access Diagnostic Tool
 * 
 * Tests various API parameters to help retrieve Wilson Center data
 * that's visible on the Best.Energy analytics portal
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

const ENISCOPE_API_URL = (process.env.VITE_ENISCOPE_API_URL || process.env.VITE_BEST_ENERGY_API_URL || 'https://core.eniscope.com').replace(/\/$/, '');
const ENISCOPE_API_KEY = process.env.VITE_ENISCOPE_API_KEY || process.env.VITE_BEST_ENERGY_API_KEY || '';
const ENISCOPE_EMAIL = process.env.VITE_ENISCOPE_EMAIL || '';
const ENISCOPE_PASSWORD = process.env.VITE_ENISCOPE_PASSWORD || '';

class DiagnosticClient {
  constructor() {
    this.sessionToken = null;
    this.apiKey = ENISCOPE_API_KEY;
    this.email = ENISCOPE_EMAIL;
    this.passwordMd5 = crypto.createHash('md5').update(ENISCOPE_PASSWORD).digest('hex');
    this.baseUrl = ENISCOPE_API_URL;
  }

  async authenticate() {
    const authString = `${this.email}:${this.passwordMd5}`;
    const authB64 = Buffer.from(authString).toString('base64');

    const response = await axios.get(`${this.baseUrl}/organizations`, {
      headers: {
        'Authorization': `Basic ${authB64}`,
        'X-Eniscope-API': this.apiKey,
        'Accept': 'text/json',
      },
    });

    this.sessionToken = response.headers['x-eniscope-token'] || response.headers['X-Eniscope-Token'];
    return true;
  }

  async testReadings(channelId, testConfig) {
    const headers = {
      'X-Eniscope-API': this.apiKey,
      'Accept': 'text/json',
    };

    if (this.sessionToken) {
      headers['X-Eniscope-Token'] = this.sessionToken;
    }

    const params = { ...testConfig };

    try {
      const url = `${this.baseUrl}/readings/${channelId}`;
      const response = await axios.get(url, { headers, params });
      
      return {
        success: true,
        status: response.status,
        dataPoints: response.data?.data?.length || response.data?.result?.length || 0,
        data: response.data,
        headers: response.headers,
      };
    } catch (error) {
      return {
        success: false,
        status: error.response?.status || 'ERROR',
        error: error.message,
        data: error.response?.data,
      };
    }
  }

  async getChannelMetadata(channelId) {
    const headers = {
      'X-Eniscope-API': this.apiKey,
      'Accept': 'text/json',
    };

    if (this.sessionToken) {
      headers['X-Eniscope-Token'] = this.sessionToken;
    }

    try {
      const response = await axios.get(`${this.baseUrl}/channels/${channelId}`, { headers });
      return response.data;
    } catch (error) {
      return { error: error.message };
    }
  }
}

function formatTimestamp(unixTimestamp) {
  const date = new Date(parseInt(unixTimestamp) * 1000);
  return date.toISOString().split('T')[0]; // YYYY-MM-DD format
}

async function main() {
  console.log('🔍 Data Access Diagnostic Tool\n');
  console.log('Testing various API parameters to access Wilson Center data...\n');
  console.log('='.repeat(70));

  const client = new DiagnosticClient();

  try {
    // Authenticate
    console.log('\n🔐 Authenticating...');
    await client.authenticate();
    console.log('✓ Authentication successful');

    // Load Wilson Center channels
    const channelsPath = path.join(__dirname, '..', 'data', 'channels-org-23271.json');
    const channelsData = JSON.parse(fs.readFileSync(channelsPath, 'utf8'));
    const wilsonChannels = channelsData.channels.filter(c => 
      c.channelName && c.channelName.includes('Wilson') && c.status === '1'
    );

    if (wilsonChannels.length === 0) {
      console.error('❌ No Wilson Center channels found');
      process.exit(1);
    }

    // Pick first active channel for testing
    const testChannel = wilsonChannels[0];
    const channelId = testChannel.dataChannelId;
    const channelName = testChannel.channelName;
    const registeredDate = testChannel.registered;

    console.log(`\n📊 Test Channel: ${channelName}`);
    console.log(`   ID: ${channelId}`);
    console.log(`   Registered: ${formatTimestamp(registeredDate)} (${registeredDate})`);
    console.log(`   Device: ${testChannel.deviceName}`);
    console.log(`   Type: ${testChannel.deviceTypeName}`);

    // Get channel metadata
    console.log('\n📋 Fetching channel metadata...');
    const metadata = await client.getChannelMetadata(channelId);
    if (!metadata.error) {
      console.log('✓ Channel metadata retrieved');
      if (metadata.lastReading) {
        console.log(`   Last Reading: ${metadata.lastReading}`);
      }
    }

    console.log('\n' + '='.repeat(70));
    console.log('\n🧪 Running diagnostic tests...\n');

    // Test configurations
    const tests = [
      // Test 1: Simple test with pre-defined ranges
      { name: 'Today (no fields)', params: { daterange: 'today', res: '900', action: 'summarize' } },
      { name: 'Yesterday (no fields)', params: { daterange: 'yesterday', res: '900', action: 'summarize' } },
      { name: '7 days (no fields)', params: { daterange: '7days', res: '3600', action: 'summarize' } },
      
      // Test 2: With basic fields
      { name: 'Today with E field', params: { 'fields[]': 'E', daterange: 'today', res: '900', action: 'summarize' } },
      { name: 'Yesterday with E,P,V', params: { 'fields[]': ['E', 'P', 'V'], daterange: 'yesterday', res: '900', action: 'summarize' } },
      
      // Test 3: Different resolutions
      { name: 'Today (1-min resolution)', params: { 'fields[]': 'E', daterange: 'today', res: '60', action: 'summarize' } },
      { name: 'Yesterday (hourly)', params: { 'fields[]': 'E', daterange: 'yesterday', res: '3600', action: 'summarize' } },
      
      // Test 4: Different actions
      { name: 'Today (total)', params: { 'fields[]': 'E', daterange: 'today', res: '900', action: 'total' } },
      { name: '7 days (averageday)', params: { 'fields[]': 'E', daterange: '7days', res: '3600', action: 'averageday' } },
      
      // Test 5: Custom date ranges (since registration)
      { name: 'Since May 1 2025', params: { 'fields[]': 'E', 'daterange[]': ['2025-05-01', '2025-05-07'], res: '3600', action: 'summarize' } },
      { name: 'Since registration', params: { 'fields[]': 'E', 'daterange[]': [registeredDate, Math.floor(Date.now() / 1000).toString()], res: '3600', action: 'summarize' } },
      
      // Test 6: Last 30 days
      { name: '30 days', params: { 'fields[]': 'E', daterange: '30days', res: '86400', action: 'summarize' } },
      { name: 'This month', params: { 'fields[]': 'E', daterange: 'thismonth', res: '3600', action: 'summarize' } },
      
      // Test 7: showCounters parameter
      { name: 'Today (with counters)', params: { 'fields[]': 'E', daterange: 'today', res: '900', action: 'summarize', showCounters: '1' } },
      { name: 'Today (without counters)', params: { 'fields[]': 'E', daterange: 'today', res: '900', action: 'summarize', showCounters: '0' } },
      
      // Test 8: December 2024 (current month)
      { name: 'December 2024', params: { 'fields[]': 'E', 'daterange[]': ['2024-12-01', '2024-12-29'], res: '3600', action: 'summarize' } },
      { name: 'Last 7 days (custom)', params: { 'fields[]': 'E', 'daterange[]': ['2024-12-22', '2024-12-29'], res: '900', action: 'summarize' } },
    ];

    const results = [];

    for (let i = 0; i < tests.length; i++) {
      const test = tests[i];
      process.stdout.write(`${i + 1}. ${test.name.padEnd(35)} ... `);
      
      const result = await client.testReadings(channelId, test.params);
      results.push({ ...test, ...result });
      
      if (result.success) {
        if (result.dataPoints > 0) {
          console.log(`✅ ${result.dataPoints} data points`);
        } else {
          console.log(`⚠️  Success but 0 data points`);
        }
      } else {
        console.log(`❌ ${result.status} - ${result.error}`);
      }
      
      // Small delay to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 400));
    }

    // Summary
    console.log('\n' + '='.repeat(70));
    console.log('\n📈 Diagnostic Summary\n');

    const successful = results.filter(r => r.success);
    const withData = results.filter(r => r.success && r.dataPoints > 0);
    const errors = results.filter(r => !r.success);

    console.log(`Total Tests: ${results.length}`);
    console.log(`Successful API Calls: ${successful.length}`);
    console.log(`Calls with Data: ${withData.length}`);
    console.log(`Errors: ${errors.length}`);

    if (withData.length > 0) {
      console.log('\n✅ Data Retrieved! Working configurations:\n');
      withData.forEach((r, idx) => {
        console.log(`${idx + 1}. ${r.name}`);
        console.log(`   Data Points: ${r.dataPoints}`);
        console.log(`   Parameters: ${JSON.stringify(r.params)}`);
        
        // Show sample data
        if (r.data?.data && r.data.data.length > 0) {
          console.log(`   Sample: ${JSON.stringify(r.data.data[0])}`);
        }
        console.log('');
      });

      // Save successful results
      const savePath = path.join(__dirname, '..', 'data', 'diagnostic-results.json');
      fs.writeFileSync(savePath, JSON.stringify({ 
        testChannel: { channelId, channelName },
        results,
        successfulConfigs: withData.map(r => ({ name: r.name, params: r.params, dataPoints: r.dataPoints }))
      }, null, 2));
      console.log(`📁 Results saved to: data/diagnostic-results.json\n`);
    } else {
      console.log('\n⚠️  No data retrieved in any test configuration');
      console.log('\nPossible reasons:');
      console.log('1. Data transmission recently started - may need more time');
      console.log('2. Data stored under different channel IDs');
      console.log('3. API access permissions may be limited');
      console.log('4. Data available on portal but API lag');
      
      console.log('\n📋 Next steps:');
      console.log('1. Check Best.Energy portal for the exact date range with data');
      console.log('2. Verify channel IDs match between portal and API');
      console.log('3. Try the portal\'s date range in a custom query');
      console.log('4. Contact Best.Energy support about API data access');
      
      // Save diagnostic info anyway
      const savePath = path.join(__dirname, '..', 'data', 'diagnostic-results.json');
      fs.writeFileSync(savePath, JSON.stringify({ 
        testChannel: { channelId, channelName },
        results,
        note: 'No data found - see console output for troubleshooting steps'
      }, null, 2));
      console.log(`\n📁 Diagnostic results saved to: data/diagnostic-results.json`);
    }

    // Show errors if any
    if (errors.length > 0) {
      console.log('\n❌ Errors encountered:\n');
      errors.forEach(e => {
        console.log(`- ${e.name}: ${e.status} - ${e.error}`);
        if (e.data) {
          console.log(`  Response: ${JSON.stringify(e.data)}`);
        }
      });
    }

  } catch (error) {
    console.error('\n❌ Fatal error:', error.message);
    if (error.response) {
      console.error('Status:', error.response.status);
      console.error('Data:', error.response.data);
    }
    process.exit(1);
  }
}

main();

