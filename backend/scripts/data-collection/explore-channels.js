#!/usr/bin/env node
/**
 * Channel Explorer Script
 * 
 * Lists all available channels and checks which ones have recent data
 * 
 * Usage:
 *   node scripts/explore-channels.js
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function readJsonFile(filename) {
  const filepath = path.join(__dirname, '..', 'data', filename);
  try {
    const content = fs.readFileSync(filepath, 'utf8');
    return JSON.parse(content);
  } catch (error) {
    console.error(`Error reading ${filename}:`, error.message);
    return null;
  }
}

function formatDate(timestamp) {
  if (!timestamp) return 'N/A';
  const date = new Date(parseInt(timestamp) * 1000);
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function main() {
  console.log('🔍 Exploring Available Channels...\n');

  // Read channels data
  const channelsData = readJsonFile('channels-org-23271.json');
  
  if (!channelsData || !channelsData.channels) {
    console.error('❌ Could not load channels data. Have you run the analysis script first?');
    console.log('\nRun: node scripts/analyze-energy-data.js');
    process.exit(1);
  }

  const channels = channelsData.channels;
  console.log(`Found ${channels.length} channels:\n`);
  console.log('=' .repeat(100));

  channels.forEach((channel, index) => {
    const isActive = channel.status === '1';
    const statusIcon = isActive ? '✅' : '❌';
    const expiresDate = new Date(parseInt(channel.expires) * 1000);
    const isExpired = expiresDate < new Date();
    const expiryIcon = isExpired ? '⚠️' : '✓';

    console.log(`\n${index + 1}. ${statusIcon} ${channel.channelName || 'Unnamed'}`);
    console.log(`   ID: ${channel.dataChannelId}`);
    console.log(`   Device: ${channel.deviceName}`);
    console.log(`   Type: ${channel.deviceTypeName}`);
    console.log(`   Organization: ${channel.organizationName}`);
    console.log(`   Data Type: ${channel.dataType}`);
    console.log(`   Phase: ${channel.displayedPhase}`);
    console.log(`   Status: ${isActive ? 'Active' : 'Inactive'}`);
    console.log(`   ${expiryIcon} Registered: ${formatDate(channel.registered)}`);
    console.log(`   ${expiryIcon} Expires: ${formatDate(channel.expires)} ${isExpired ? '(EXPIRED)' : ''}`);
    console.log(`   In TSDB: ${channel.in_tsdb}`);
    console.log(`   Device ID: ${channel.deviceId}`);
    console.log(`   UUID: ${channel.uuId}`);
  });

  console.log('\n' + '='.repeat(100));
  
  // Summary statistics
  const activeChannels = channels.filter(c => c.status === '1');
  const expiredChannels = channels.filter(c => {
    const expiresDate = new Date(parseInt(c.expires) * 1000);
    return expiresDate < new Date();
  });
  const channelsInTSDB = channels.filter(c => c.in_tsdb === 'Y');

  console.log('\n📊 Summary:');
  console.log(`   Total Channels: ${channels.length}`);
  console.log(`   Active: ${activeChannels.length}`);
  console.log(`   Inactive: ${channels.length - activeChannels.length}`);
  console.log(`   Expired: ${expiredChannels.length}`);
  console.log(`   In Time-Series DB: ${channelsInTSDB.length}`);

  // Unique device types
  const deviceTypes = [...new Set(channels.map(c => c.deviceTypeName))];
  console.log(`\n   Device Types:`);
  deviceTypes.forEach(type => {
    const count = channels.filter(c => c.deviceTypeName === type).length;
    console.log(`     - ${type}: ${count} channel(s)`);
  });

  // Data types
  const dataTypes = [...new Set(channels.map(c => c.dataType))];
  console.log(`\n   Data Types:`);
  dataTypes.forEach(type => {
    const count = channels.filter(c => c.dataType === type).length;
    console.log(`     - ${type}: ${count} channel(s)`);
  });

  console.log('\n💡 Tip: Try fetching data for active channels with recent expiration dates');
  console.log('    These are most likely to have current data available.\n');

  // Suggest channels to try
  const goodChannels = activeChannels
    .filter(c => {
      const expiresDate = new Date(parseInt(c.expires) * 1000);
      return expiresDate > new Date() && c.in_tsdb === 'Y';
    })
    .slice(0, 5);

  if (goodChannels.length > 0) {
    console.log('🎯 Recommended channels to try first:');
    goodChannels.forEach((channel, idx) => {
      console.log(`   ${idx + 1}. "${channel.channelName}" (ID: ${channel.dataChannelId}) - ${channel.dataType}`);
    });
  }

  console.log('');
}

main();

