#!/usr/bin/env node
/**
 * Export Wilson Center Raw Monthly Data to CSV
 * 
 * Pulls raw energy data from the Eniscope API for Wilson Center
 * for a specified month and exports to CSV format suitable for:
 * - Tableau visualization and analysis
 * - AI tools and custom analysis scripts
 * - Excel/spreadsheet analysis
 * 
 * Usage:
 *   # Export data for a specific month
 *   node scripts/data-collection/export-wilson-raw-monthly.js 2025 1
 *   node scripts/data-collection/export-wilson-raw-monthly.js 2026 2
 *   
 *   # Export for last month
 *   node scripts/data-collection/export-wilson-raw-monthly.js
 *   
 *   # With custom resolution (default is 900 = 15 minutes)
 *   node scripts/data-collection/export-wilson-raw-monthly.js 2025 12 --resolution=3600
 * 
 * Output:
 *   Creates CSV files in backend/data/exports/:
 *   - wilson-center-raw-YYYY-MM.csv (all data in one file)
 *   - wilson-center-raw-YYYY-MM-channels.csv (channel metadata)
 */

import axios from 'axios';
import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from project root
// Script is in backend/scripts/data-collection/, so go up 3 levels to project root
dotenv.config({ path: path.join(__dirname, '..', '..', '..', '.env') });

const ENISCOPE_API_URL = process.env.VITE_ENISCOPE_API_URL || process.env.VITE_BEST_ENERGY_API_URL || 'https://core.eniscope.com';
const ENISCOPE_API_KEY = process.env.VITE_ENISCOPE_API_KEY || process.env.VITE_BEST_ENERGY_API_KEY || '';
const ENISCOPE_EMAIL = process.env.VITE_ENISCOPE_EMAIL || '';
const ENISCOPE_PASSWORD = process.env.VITE_ENISCOPE_PASSWORD || '';

// Eniscope API Client
class EniscopeAPIClient {
  constructor() {
    this.sessionToken = null;
    this.apiKey = ENISCOPE_API_KEY;
    this.email = ENISCOPE_EMAIL;
    this.passwordMd5 = crypto.createHash('md5').update(ENISCOPE_PASSWORD).digest('hex');
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
      return true;
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
          const delay = Math.pow(2, attempt) * 1000;
          console.log(`   ⏳ Rate limited. Retrying in ${delay/1000}s...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        } else {
          throw error;
        }
      }
    }
  }

  async getReadings(channelId, options = {}) {
    const params = {
      action: options.action || 'summarize',
      res: options.res || options.resolution || '900',
    };

    if (options.fields && Array.isArray(options.fields)) {
      options.fields.forEach(field => {
        if (!params['fields[]']) params['fields[]'] = [];
        params['fields[]'].push(field);
      });
    }

    if (options.daterange) {
      if (Array.isArray(options.daterange)) {
        params['daterange[]'] = options.daterange;
      } else {
        params.daterange = options.daterange;
      }
    }

    return this.makeRequest(`/readings/${channelId}`, params);
  }
}

// CSV Helper Functions
function escapeCSVValue(value) {
  if (value === null || value === undefined) {
    return '';
  }
  
  const str = String(value);
  
  // If contains comma, quote, or newline, wrap in quotes and escape quotes
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  
  return str;
}

function arrayToCSV(headers, rows) {
  const csvRows = [headers.map(escapeCSVValue).join(',')];
  
  rows.forEach(row => {
    const values = headers.map(header => escapeCSVValue(row[header]));
    csvRows.push(values.join(','));
  });
  
  return csvRows.join('\n');
}

// Date Helper Functions
function getMonthDateRange(year, month) {
  // Create start date (first day of month at 00:00:00)
  const startDate = new Date(Date.UTC(year, month - 1, 1, 0, 0, 0));
  
  // Create end date (first day of next month at 00:00:00)
  const endDate = new Date(Date.UTC(year, month, 1, 0, 0, 0));
  
  return {
    start: startDate.toISOString(),
    end: endDate.toISOString(),
    startTimestamp: Math.floor(startDate.getTime() / 1000),
    endTimestamp: Math.floor(endDate.getTime() / 1000),
  };
}

function formatTimestamp(ts) {
  const date = new Date(parseInt(ts) * 1000);
  return date.toISOString();
}

// Main Export Function
async function exportWilsonRawData(year, month, resolution = '900') {
  console.log('\n🏢 Wilson Center Raw Data Export\n');
  console.log('=' .repeat(60));
  console.log(`📅 Year: ${year}`);
  console.log(`📅 Month: ${month}`);
  console.log(`⏱️  Resolution: ${resolution} seconds (${resolution/60} minutes)\n`);

  const client = new EniscopeAPIClient();

  try {
    // Authenticate
    console.log('🔐 Authenticating...');
    await client.authenticate();
    console.log('✓ Authentication successful\n');

    // Load Wilson Center channels
    console.log('📊 Loading Wilson Center channels...');
    // Go up 3 levels to project root, then into data folder
    const channelsPath = path.join(__dirname, '..', '..', '..', 'data', 'channels-org-23271.json');
    
    if (!fs.existsSync(channelsPath)) {
      console.error('❌ Channels data not found.');
      console.error('   Please run: npm run explore:channels');
      process.exit(1);
    }

    const channelsData = JSON.parse(fs.readFileSync(channelsPath, 'utf8'));
    const allChannels = channelsData.channels || [];

    // Filter active Wilson Center channels
    const wilsonChannels = allChannels.filter(c => 
      c.channelName && 
      c.channelName.includes('Wilson') &&
      c.status === '1' &&
      c.in_tsdb === 'Y'
    );

    console.log(`✓ Found ${wilsonChannels.length} active Wilson Center channels\n`);

    // Get date range for the month
    const dateRange = getMonthDateRange(year, month);
    console.log(`📅 Date Range: ${dateRange.start} to ${dateRange.end}\n`);

    // Prepare to collect all data
    const allReadings = [];
    const channelMetadata = [];
    let totalDataPoints = 0;

    // Fetch data for each channel
    console.log('🔄 Fetching data from Eniscope API...\n');
    
    for (let i = 0; i < wilsonChannels.length; i++) {
      const channel = wilsonChannels[i];
      const channelId = channel.dataChannelId;
      const channelName = channel.channelName || channel.deviceName;
      
      console.log(`   [${i + 1}/${wilsonChannels.length}] ${channelName}`);

      try {
        const readings = await client.getReadings(channelId, {
          fields: ['E', 'P', 'V', 'I', 'PF', 'T', 'kW', 'kWh'],
          daterange: [dateRange.start, dateRange.end],
          res: resolution,
          action: 'summarize',
        });

        // Add delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 300));

        const readingList = readings.records || readings.data || readings.result || [];
        
        if (readingList.length > 0) {
          // Process each reading and add to collection
          readingList.forEach(reading => {
            allReadings.push({
              'Timestamp': formatTimestamp(reading.ts),
              'Unix_Timestamp': reading.ts,
              'Date': formatTimestamp(reading.ts).split('T')[0],
              'Time': formatTimestamp(reading.ts).split('T')[1].split('.')[0],
              'Year': new Date(reading.ts * 1000).getUTCFullYear(),
              'Month': new Date(reading.ts * 1000).getUTCMonth() + 1,
              'Day': new Date(reading.ts * 1000).getUTCDate(),
              'Hour': new Date(reading.ts * 1000).getUTCHours(),
              'Day_of_Week': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][new Date(reading.ts * 1000).getUTCDay()],
              'Channel_ID': channelId,
              'Channel_Name': channelName,
              'Device_Type': channel.deviceTypeName || '',
              'Data_Type': channel.dataType || '',
              'Energy_Wh': reading.E || reading.kWh ? (reading.kWh * 1000) : null,
              'Energy_kWh': reading.E ? (reading.E / 1000) : reading.kWh || null,
              'Power_W': reading.P || reading.kW ? (reading.kW * 1000) : null,
              'Power_kW': reading.P ? (reading.P / 1000) : reading.kW || null,
              'Voltage_V': reading.V || null,
              'Current_A': reading.I || null,
              'Power_Factor': reading.PF || null,
              'Temperature_C': reading.T || null,
            });
          });

          totalDataPoints += readingList.length;
          console.log(`      ✓ ${readingList.length} readings`);
        } else {
          console.log(`      ⚠️  No data available`);
        }

        // Store channel metadata
        channelMetadata.push({
          'Channel_ID': channelId,
          'Channel_Name': channelName,
          'Device_ID': channel.deviceId || '',
          'Device_Name': channel.deviceName || '',
          'Device_Type': channel.deviceTypeName || '',
          'Data_Type': channel.dataType || '',
          'Organization_ID': channel.organizationId || '',
          'Status': channel.status || '',
          'In_TSDB': channel.in_tsdb || '',
          'Tariff_ID': channel.tariffId || '',
          'Data_Points': readingList.length,
        });

      } catch (error) {
        console.log(`      ❌ Error: ${error.message}`);
        
        // Still add channel metadata even on error
        channelMetadata.push({
          'Channel_ID': channelId,
          'Channel_Name': channelName,
          'Device_ID': channel.deviceId || '',
          'Device_Name': channel.deviceName || '',
          'Device_Type': channel.deviceTypeName || '',
          'Data_Type': channel.dataType || '',
          'Organization_ID': channel.organizationId || '',
          'Status': channel.status || '',
          'In_TSDB': channel.in_tsdb || '',
          'Tariff_ID': channel.tariffId || '',
          'Data_Points': 0,
          'Error': error.message,
        });
      }
    }

    // Create exports directory if it doesn't exist
    // Go up 3 levels to project root, then into backend/data/exports
    const exportDir = path.join(__dirname, '..', '..', '..', 'backend', 'data', 'exports');
    if (!fs.existsSync(exportDir)) {
      fs.mkdirSync(exportDir, { recursive: true });
    }

    // Generate filename with year-month
    const monthStr = String(month).padStart(2, '0');
    const baseFilename = `wilson-center-raw-${year}-${monthStr}`;

    // Sort readings by timestamp for better analysis
    allReadings.sort((a, b) => a.Unix_Timestamp - b.Unix_Timestamp);

    // Export main data CSV
    console.log('\n📊 Exporting to CSV...\n');
    
    const dataHeaders = [
      'Timestamp', 'Unix_Timestamp', 'Date', 'Time', 
      'Year', 'Month', 'Day', 'Hour', 'Day_of_Week',
      'Channel_ID', 'Channel_Name', 'Device_Type', 'Data_Type',
      'Energy_Wh', 'Energy_kWh', 'Power_W', 'Power_kW',
      'Voltage_V', 'Current_A', 'Power_Factor', 'Temperature_C'
    ];
    
    const dataCSV = arrayToCSV(dataHeaders, allReadings);
    const dataFile = path.join(exportDir, `${baseFilename}.csv`);
    fs.writeFileSync(dataFile, dataCSV);
    console.log(`✓ Data exported: ${baseFilename}.csv`);
    console.log(`  ${allReadings.length.toLocaleString()} rows`);

    // Export channel metadata CSV
    const metadataHeaders = [
      'Channel_ID', 'Channel_Name', 'Device_ID', 'Device_Name',
      'Device_Type', 'Data_Type', 'Organization_ID',
      'Status', 'In_TSDB', 'Tariff_ID', 'Data_Points', 'Error'
    ];
    
    const metadataCSV = arrayToCSV(metadataHeaders, channelMetadata);
    const metadataFile = path.join(exportDir, `${baseFilename}-channels.csv`);
    fs.writeFileSync(metadataFile, metadataCSV);
    console.log(`✓ Channel metadata: ${baseFilename}-channels.csv`);
    console.log(`  ${channelMetadata.length} channels`);

    // Export summary info as JSON
    const summary = {
      year,
      month,
      monthName: new Date(year, month - 1).toLocaleString('en-US', { month: 'long' }),
      resolution: resolution,
      resolutionMinutes: parseInt(resolution) / 60,
      dateRange: {
        start: dateRange.start,
        end: dateRange.end,
      },
      totalChannels: wilsonChannels.length,
      totalDataPoints: totalDataPoints,
      averageDataPointsPerChannel: Math.round(totalDataPoints / wilsonChannels.length),
      exportDate: new Date().toISOString(),
      files: {
        data: `${baseFilename}.csv`,
        metadata: `${baseFilename}-channels.csv`,
      },
    };

    const summaryFile = path.join(exportDir, `${baseFilename}-summary.json`);
    fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2));
    console.log(`✓ Summary: ${baseFilename}-summary.json\n`);

    // Print summary
    console.log('=' .repeat(60));
    console.log('📈 Export Complete!\n');
    console.log(`✓ Total Channels: ${summary.totalChannels}`);
    console.log(`✓ Total Data Points: ${summary.totalDataPoints.toLocaleString()}`);
    console.log(`✓ Average per Channel: ${summary.averageDataPointsPerChannel.toLocaleString()}`);
    console.log(`\n📁 Files saved to: backend/data/exports/`);
    console.log(`   - ${baseFilename}.csv`);
    console.log(`   - ${baseFilename}-channels.csv`);
    console.log(`   - ${baseFilename}-summary.json`);
    
    console.log('\n💡 Next Steps:');
    console.log('   • Import the CSV into Tableau Desktop');
    console.log('   • Use the data with AI analysis tools');
    console.log('   • Open in Excel for custom analysis');
    console.log('   • Join with channel metadata for enhanced analysis\n');

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    process.exit(1);
  }
}

// Parse command line arguments
function parseArgs() {
  const args = process.argv.slice(2);
  
  // Parse resolution option
  let resolution = '900'; // Default 15 minutes
  const resArg = args.find(arg => arg.startsWith('--resolution='));
  if (resArg) {
    resolution = resArg.split('=')[1];
    args.splice(args.indexOf(resArg), 1);
  }

  // Parse year and month
  let year, month;
  
  if (args.length >= 2) {
    // Use provided year and month
    year = parseInt(args[0]);
    month = parseInt(args[1]);
  } else {
    // Use last month
    const lastMonth = new Date();
    lastMonth.setMonth(lastMonth.getMonth() - 1);
    year = lastMonth.getFullYear();
    month = lastMonth.getMonth() + 1;
    console.log(`\n⚠️  No year/month specified. Using last month: ${year}-${month}\n`);
  }

  // Validate
  if (isNaN(year) || year < 2020 || year > 2030) {
    console.error('❌ Invalid year. Must be between 2020 and 2030.');
    process.exit(1);
  }

  if (isNaN(month) || month < 1 || month > 12) {
    console.error('❌ Invalid month. Must be between 1 and 12.');
    process.exit(1);
  }

  return { year, month, resolution };
}

// Main execution
const { year, month, resolution } = parseArgs();
exportWilsonRawData(year, month, resolution);
