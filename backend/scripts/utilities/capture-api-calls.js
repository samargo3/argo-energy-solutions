#!/usr/bin/env node
/**
 * API Call Capture Tool
 * 
 * Makes API calls and captures the exact HTTP requests/responses
 * for troubleshooting with Best.Energy support
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

// Add request/response interceptor to capture everything
function createTrackedClient() {
  const client = axios.create();
  const log = [];

  client.interceptors.request.use(request => {
    const entry = {
      timestamp: new Date().toISOString(),
      method: request.method?.toUpperCase(),
      url: request.url,
      baseURL: request.baseURL,
      fullURL: axios.getUri(request),
      headers: { ...request.headers },
      params: request.params,
      data: request.data,
    };
    
    // Hide sensitive data in log
    if (entry.headers.Authorization) {
      entry.headers.Authorization = 'Basic [REDACTED]';
    }
    if (entry.headers['X-Eniscope-API']) {
      entry.headers['X-Eniscope-API'] = '[REDACTED]';
    }
    
    log.push({ type: 'REQUEST', ...entry });
    return request;
  });

  client.interceptors.response.use(
    response => {
      const entry = {
        timestamp: new Date().toISOString(),
        status: response.status,
        statusText: response.statusText,
        headers: { ...response.headers },
        data: response.data,
      };
      log.push({ type: 'RESPONSE', ...entry });
      return response;
    },
    error => {
      const entry = {
        timestamp: new Date().toISOString(),
        status: error.response?.status,
        statusText: error.response?.statusText,
        headers: error.response?.headers,
        data: error.response?.data,
        error: error.message,
      };
      log.push({ type: 'ERROR', ...entry });
      throw error;
    }
  );

  return { client, log };
}

async function main() {
  console.log('🔍 Capturing API Calls for Best.Energy Support\n');
  console.log('='.repeat(70));

  const { client, log } = createTrackedClient();

  try {
    const passwordMd5 = crypto.createHash('md5').update(ENISCOPE_PASSWORD).digest('hex');
    const authString = `${ENISCOPE_EMAIL}:${passwordMd5}`;
    const authB64 = Buffer.from(authString).toString('base64');

    console.log('\n📋 Configuration:');
    console.log(`   Base URL: ${ENISCOPE_API_URL}`);
    console.log(`   API Key: ${ENISCOPE_API_KEY.substring(0, 8)}...`);
    console.log(`   Email: ${ENISCOPE_EMAIL}`);
    console.log(`   Auth: Basic ${authB64.substring(0, 20)}...[REDACTED]`);

    // Test 1: Authenticate and get organizations
    console.log('\n1️⃣  Authenticating...');
    const authResponse = await client.get(`${ENISCOPE_API_URL}/organizations`, {
      headers: {
        'Authorization': `Basic ${authB64}`,
        'X-Eniscope-API': ENISCOPE_API_KEY,
        'Accept': 'text/json',
      },
    });
    const sessionToken = authResponse.headers['x-eniscope-token'];
    console.log(`   ✓ Status: ${authResponse.status}`);
    console.log(`   ✓ Session Token: ${sessionToken ? sessionToken.substring(0, 20) + '...' : 'None'}`);

    // Get a Wilson Center channel
    const channelsPath = path.join(__dirname, '..', 'data', 'channels-org-23271.json');
    const channelsData = JSON.parse(fs.readFileSync(channelsPath, 'utf8'));
    const testChannel = channelsData.channels.find(c => c.channelName?.includes('RTU-1'));
    const channelId = testChannel.dataChannelId;

    console.log(`\n2️⃣  Test Channel: ${testChannel.channelName}`);
    console.log(`   Channel ID: ${channelId}`);

    // Test 2: Simple readings call with E field
    console.log('\n3️⃣  Test 1: Simple GET with E field, today, 15-min resolution');
    try {
      const response1 = await client.get(`${ENISCOPE_API_URL}/readings/${channelId}`, {
        headers: {
          'X-Eniscope-API': ENISCOPE_API_KEY,
          'X-Eniscope-Token': sessionToken,
          'Accept': 'text/json',
        },
        params: {
          'fields[]': 'E',
          'daterange': 'today',
          'res': '900',
          'action': 'summarize',
        },
      });
      console.log(`   ✓ Status: ${response1.status}`);
      console.log(`   ✓ Data Points: ${response1.data?.data?.length || 0}`);
      if (response1.data?.data?.length > 0) {
        console.log(`   ✓ First Record: ${JSON.stringify(response1.data.data[0])}`);
      } else {
        console.log(`   ⚠️  Response: ${JSON.stringify(response1.data)}`);
      }
    } catch (error) {
      console.log(`   ❌ Error: ${error.message}`);
      console.log(`   ❌ Status: ${error.response?.status}`);
      console.log(`   ❌ Response: ${JSON.stringify(error.response?.data)}`);
    }

    // Test 3: Multiple fields
    console.log('\n4️⃣  Test 2: Multiple fields (E, P, V)');
    try {
      const response2 = await client.get(`${ENISCOPE_API_URL}/readings/${channelId}`, {
        headers: {
          'X-Eniscope-API': ENISCOPE_API_KEY,
          'X-Eniscope-Token': sessionToken,
          'Accept': 'text/json',
        },
        params: {
          'fields[]': ['E', 'P', 'V'],
          'daterange': 'today',
          'res': '900',
          'action': 'summarize',
        },
      });
      console.log(`   ✓ Status: ${response2.status}`);
      console.log(`   ✓ Data Points: ${response2.data?.data?.length || 0}`);
    } catch (error) {
      console.log(`   ❌ Error: ${error.message}`);
      console.log(`   ❌ Status: ${error.response?.status}`);
    }

    // Test 4: Different date range
    console.log('\n5️⃣  Test 3: Yesterday');
    try {
      const response3 = await client.get(`${ENISCOPE_API_URL}/readings/${channelId}`, {
        headers: {
          'X-Eniscope-API': ENISCOPE_API_KEY,
          'X-Eniscope-Token': sessionToken,
          'Accept': 'text/json',
        },
        params: {
          'fields[]': 'E',
          'daterange': 'yesterday',
          'res': '3600',
          'action': 'summarize',
        },
      });
      console.log(`   ✓ Status: ${response3.status}`);
      console.log(`   ✓ Data Points: ${response3.data?.data?.length || 0}`);
    } catch (error) {
      console.log(`   ❌ Error: ${error.message}`);
      console.log(`   ❌ Status: ${error.response?.status}`);
    }

    // Test 5: Custom date range
    console.log('\n6️⃣  Test 4: Custom date range (last 7 days)');
    const endDate = new Date();
    const startDate = new Date(endDate);
    startDate.setDate(startDate.getDate() - 7);
    
    try {
      const response4 = await client.get(`${ENISCOPE_API_URL}/readings/${channelId}`, {
        headers: {
          'X-Eniscope-API': ENISCOPE_API_KEY,
          'X-Eniscope-Token': sessionToken,
          'Accept': 'text/json',
        },
        params: {
          'fields[]': 'E',
          'daterange[]': [
            startDate.toISOString().split('T')[0],
            endDate.toISOString().split('T')[0]
          ],
          'res': '3600',
          'action': 'summarize',
        },
      });
      console.log(`   ✓ Status: ${response4.status}`);
      console.log(`   ✓ Data Points: ${response4.data?.data?.length || 0}`);
    } catch (error) {
      console.log(`   ❌ Error: ${error.message}`);
      console.log(`   ❌ Status: ${error.response?.status}`);
    }

    // Save captured log
    console.log('\n' + '='.repeat(70));
    console.log('\n📁 Saving detailed log...');
    
    const reportPath = path.join(__dirname, '..', 'data', 'api-call-capture.json');
    fs.writeFileSync(reportPath, JSON.stringify(log, null, 2));
    console.log(`   Saved to: data/api-call-capture.json`);

    // Generate support ticket text
    const supportTicket = generateSupportTicket(log, testChannel);
    const ticketPath = path.join(__dirname, '..', 'data', 'support-ticket.txt');
    fs.writeFileSync(ticketPath, supportTicket);
    console.log(`   Support ticket: data/support-ticket.txt`);

    console.log('\n✅ Capture complete!');
    console.log('\n📧 Copy the contents of data/support-ticket.txt');
    console.log('   and send to Best.Energy support\n');

  } catch (error) {
    console.error('\n❌ Fatal error:', error.message);
    if (error.response) {
      console.error('Status:', error.response.status);
      console.error('Data:', JSON.stringify(error.response.data, null, 2));
    }
  }
}

function generateSupportTicket(log, channel) {
  const ticket = [];
  
  ticket.push('='.repeat(70));
  ticket.push('BEST.ENERGY API SUPPORT REQUEST');
  ticket.push('='.repeat(70));
  ticket.push('');
  ticket.push('Organization: Argo Energy Solutions LLC');
  ticket.push(`API Key: ${ENISCOPE_API_KEY}`);
  ticket.push(`User Email: ${ENISCOPE_EMAIL}`);
  ticket.push(`Base URL: ${ENISCOPE_API_URL}`);
  ticket.push('');
  ticket.push('ISSUE:');
  ticket.push('------');
  ticket.push('API calls succeed (HTTP 200) but return 0 data points for all queries.');
  ticket.push('Devices are transmitting data (visible on Best.Energy portal).');
  ticket.push('All channels show in_tsdb: "Y" in metadata.');
  ticket.push('');
  ticket.push('TEST CHANNEL:');
  ticket.push('-------------');
  ticket.push(`Name: ${channel.channelName}`);
  ticket.push(`Channel ID: ${channel.dataChannelId}`);
  ticket.push(`Device ID: ${channel.deviceId}`);
  ticket.push(`UUID: ${channel.uuId}`);
  ticket.push(`Organization ID: ${channel.organizationId}`);
  ticket.push(`Status: ${channel.status === '1' ? 'Active' : 'Inactive'}`);
  ticket.push(`Registered: ${new Date(parseInt(channel.registered) * 1000).toISOString()}`);
  ticket.push(`In TSDB: ${channel.in_tsdb}`);
  ticket.push('');
  ticket.push('API CALLS TESTED:');
  ticket.push('-----------------');
  ticket.push('');

  let requestNum = 0;
  for (let i = 0; i < log.length; i++) {
    const entry = log[i];
    
    if (entry.type === 'REQUEST' && entry.url?.includes('/readings/')) {
      requestNum++;
      ticket.push(`Test ${requestNum}:`);
      ticket.push(`  Method: ${entry.method}`);
      ticket.push(`  URL: ${entry.fullURL}`);
      ticket.push(`  Headers:`);
      ticket.push(`    Accept: ${entry.headers.Accept}`);
      ticket.push(`    X-Eniscope-API: ${ENISCOPE_API_KEY}`);
      ticket.push(`    X-Eniscope-Token: ${entry.headers['X-Eniscope-Token'] ? '[SESSION_TOKEN]' : 'None'}`);
      ticket.push(`  Parameters:`);
      ticket.push(`    ${JSON.stringify(entry.params, null, 4)}`);
      ticket.push('');
      
      // Find corresponding response
      if (i + 1 < log.length && log[i + 1].type === 'RESPONSE') {
        const response = log[i + 1];
        ticket.push(`  Response:`);
        ticket.push(`    Status: ${response.status} ${response.statusText}`);
        ticket.push(`    Data Points: ${response.data?.data?.length || 0}`);
        ticket.push(`    Response Body: ${JSON.stringify(response.data, null, 4)}`);
        ticket.push('');
      } else if (i + 1 < log.length && log[i + 1].type === 'ERROR') {
        const error = log[i + 1];
        ticket.push(`  Error:`);
        ticket.push(`    Status: ${error.status} ${error.statusText}`);
        ticket.push(`    Message: ${error.error}`);
        ticket.push(`    Response: ${JSON.stringify(error.data, null, 4)}`);
        ticket.push('');
      }
      ticket.push('-'.repeat(70));
      ticket.push('');
    }
  }

  ticket.push('');
  ticket.push('QUESTION:');
  ticket.push('---------');
  ticket.push('What are we missing in our API calls? All calls return HTTP 200 but');
  ticket.push('with 0 data points. Data is visible on the Best.Energy portal for');
  ticket.push('these channels. Please advise on correct API usage.');
  ticket.push('');
  ticket.push('CURL EQUIVALENT (Test 1):');
  ticket.push('-------------------------');
  ticket.push('');
  
  // Generate curl command
  const passwordMd5 = crypto.createHash('md5').update(ENISCOPE_PASSWORD).digest('hex');
  const authString = `${ENISCOPE_EMAIL}:${passwordMd5}`;
  const authB64 = Buffer.from(authString).toString('base64');
  
  const curlCmd = `curl -X GET "${ENISCOPE_API_URL}/readings/${channel.dataChannelId}?fields%5B%5D=E&daterange=today&res=900&action=summarize" \\
  -H "Accept: text/json" \\
  -H "X-Eniscope-API: ${ENISCOPE_API_KEY}" \\
  -H "Authorization: Basic ${authB64}"`;
  
  ticket.push(curlCmd);
  ticket.push('');
  ticket.push('='.repeat(70));
  
  return ticket.join('\n');
}

main();

