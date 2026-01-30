#!/usr/bin/env node
/**
 * Export Wilson Center analysis to Tableau-friendly CSV format
 * 
 * Usage:
 *   node scripts/export-to-csv.js [analysis-file] [output-name]
 *   node scripts/export-to-csv.js wilson-center-analysis.json wilson-center
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function exportToCSV(analysisFile, outputName) {
  console.log(`📊 Exporting ${analysisFile} to CSV format...\n`);

  // Read the analysis JSON
  const dataPath = path.join(__dirname, '..', 'data', analysisFile);
  if (!fs.existsSync(dataPath)) {
    console.error(`❌ File not found: ${dataPath}`);
    process.exit(1);
  }

  const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));

  // Export 1: Channel Summary CSV
  console.log('1️⃣  Generating channel summary...');
  const channelRows = data.channels
    .filter(ch => ch.status === 'success')
    .map(ch => ({
      'Channel ID': ch.channelId,
      'Channel Name': ch.channel,
      'Device Type': ch.deviceType || '',
      'Category': categorizeChannel(ch.channel),
      'Total Energy (kWh)': ch.energy?.sum?.toFixed(2) || 0,
      'Average Power (kW)': ch.power?.avg?.toFixed(2) || 0,
      'Peak Power (kW)': ch.power?.max?.toFixed(2) || 0,
      'Minimum Power (kW)': ch.power?.min?.toFixed(2) || 0,
      'Operating Hours': ch.operatingHours?.toFixed(1) || 0,
      'Average Voltage (V)': ch.voltage?.avg?.toFixed(1) || '',
      'Power Factor': ch.powerFactor?.avg?.toFixed(3) || '',
      'Peak Timestamp': ch.peakPowerTimestamp || '',
      'Status': ch.status
    }));

  const channelCSV = objectArrayToCSV(channelRows);
  const channelFile = path.join(__dirname, '..', 'data', `${outputName}-channels.csv`);
  fs.writeFileSync(channelFile, channelCSV);
  console.log(`   ✓ ${outputName}-channels.csv (${channelRows.length} channels)`);

  // Export 2: Time Series CSV (all readings)
  console.log('2️⃣  Generating time series data...');
  const timeSeriesRows = [];
  data.channels
    .filter(ch => ch.status === 'success' && ch.rawReadings)
    .forEach(ch => {
      ch.rawReadings.forEach(reading => {
        timeSeriesRows.push({
          'Timestamp': new Date(reading.ts * 1000).toISOString(),
          'Date': new Date(reading.ts * 1000).toISOString().split('T')[0],
          'Time': new Date(reading.ts * 1000).toTimeString().split(' ')[0],
          'Channel ID': ch.channelId,
          'Channel Name': ch.channel,
          'Category': categorizeChannel(ch.channel),
          'Energy (kWh)': (reading.E / 1000).toFixed(3),
          'Power (kW)': (reading.P / 1000).toFixed(3),
          'Voltage (V)': reading.V?.toFixed(2) || '',
          'Current (A)': reading.I?.toFixed(2) || '',
          'Power Factor': reading.PF?.toFixed(3) || ''
        });
      });
    });

  const timeSeriesCSV = objectArrayToCSV(timeSeriesRows);
  const timeSeriesFile = path.join(__dirname, '..', 'data', `${outputName}-timeseries.csv`);
  fs.writeFileSync(timeSeriesFile, timeSeriesCSV);
  console.log(`   ✓ ${outputName}-timeseries.csv (${timeSeriesRows.length} readings)`);

  // Export 3: Summary Statistics CSV
  console.log('3️⃣  Generating summary statistics...');
  const summaryRow = {
    'Report Date': new Date().toISOString().split('T')[0],
    'Date Range': data.dateRange,
    'Total Channels': data.summary.totalChannels,
    'Channels with Data': data.summary.channelsWithData,
    'Channels with Errors': data.summary.channelsWithErrors || 0,
    'Total Data Points': data.summary.totalDataPoints,
    'Total Energy (kWh)': data.summary.totalEnergy.toFixed(2),
    'Estimated Cost ($)': data.summary.estimatedCost.toFixed(2),
    'Carbon Footprint (lbs CO2)': data.summary.carbonFootprint.toFixed(2),
    'Carbon Footprint (tons CO2)': (data.summary.carbonFootprint / 2000).toFixed(2),
    'Average Power (kW)': data.summary.avgPower.toFixed(2),
    'Peak Power (kW)': data.summary.peakPower.toFixed(2),
    'Peak Power Channel': data.summary.peakPowerChannel || '',
    'Peak Power Timestamp': data.summary.peakPowerTimestamp || '',
    'Average Power Factor': data.summary.avgPowerFactor.toFixed(3),
    'PF Correction Savings ($)': data.summary.pfCorrectionSavings?.toFixed(2) || 0,
    'Electricity Rate ($/kWh)': data.summary.electricityRate?.toFixed(3) || 0.12,
    'Carbon Factor (lbs/kWh)': data.summary.carbonFactor?.toFixed(2) || 0.92
  };

  const summaryCSV = objectArrayToCSV([summaryRow]);
  const summaryFile = path.join(__dirname, '..', 'data', `${outputName}-summary.csv`);
  fs.writeFileSync(summaryFile, summaryCSV);
  console.log(`   ✓ ${outputName}-summary.csv (summary stats)`);

  // Export 4: Category Aggregation CSV (useful for pie charts)
  console.log('4️⃣  Generating category breakdown...');
  const categories = {};
  data.channels
    .filter(ch => ch.status === 'success')
    .forEach(ch => {
      const cat = categorizeChannel(ch.channel);
      if (!categories[cat]) {
        categories[cat] = {
          category: cat,
          channels: 0,
          totalEnergy: 0,
          avgPower: 0,
          peakPower: 0
        };
      }
      categories[cat].channels++;
      categories[cat].totalEnergy += ch.energy?.sum || 0;
      categories[cat].avgPower += ch.power?.avg || 0;
      categories[cat].peakPower = Math.max(categories[cat].peakPower, ch.power?.max || 0);
    });

  const categoryRows = Object.values(categories).map(cat => ({
    'Category': cat.category,
    'Number of Channels': cat.channels,
    'Total Energy (kWh)': cat.totalEnergy.toFixed(2),
    'Total Average Power (kW)': cat.avgPower.toFixed(2),
    'Peak Power (kW)': cat.peakPower.toFixed(2),
    'Percentage of Total': ((cat.totalEnergy / data.summary.totalEnergy) * 100).toFixed(1) + '%'
  }));

  const categoryCSV = objectArrayToCSV(categoryRows);
  const categoryFile = path.join(__dirname, '..', 'data', `${outputName}-categories.csv`);
  fs.writeFileSync(categoryFile, categoryCSV);
  console.log(`   ✓ ${outputName}-categories.csv (${categoryRows.length} categories)`);

  console.log('\n✅ Export complete! Files ready for Tableau import.');
  console.log('\n📁 Files created:');
  console.log(`   ${channelFile}`);
  console.log(`   ${timeSeriesFile}`);
  console.log(`   ${summaryFile}`);
  console.log(`   ${categoryFile}`);
  console.log('\n💡 Next steps:');
  console.log('   1. Open Tableau Desktop');
  console.log('   2. Connect → Text File');
  console.log(`   3. Select ${outputName}-timeseries.csv for detailed analysis`);
  console.log(`   4. Or select ${outputName}-channels.csv for channel summary`);
}

function categorizeChannel(channelName) {
  if (!channelName) return 'Other';
  if (channelName.includes('RTU')) return 'HVAC - RTU';
  if (channelName.includes('AHU')) return 'HVAC - AHU';
  if (channelName.includes('Kitchen') && channelName.includes('Main')) return 'Electrical - Kitchen Main';
  if (channelName.includes('Kitchen')) return 'Electrical - Kitchen';
  if (channelName.includes('Panel')) return 'Electrical - Panel';
  if (channelName.includes('Sense') || channelName.includes('Sensor')) return 'Sensors';
  return 'Other';
}

function objectArrayToCSV(data) {
  if (data.length === 0) return '';
  
  const headers = Object.keys(data[0]);
  const csvRows = [headers.join(',')];
  
  data.forEach(row => {
    const values = headers.map(header => {
      let value = row[header];
      
      // Handle null/undefined
      if (value === null || value === undefined) {
        value = '';
      }
      
      // Convert to string
      value = String(value);
      
      // Escape commas and quotes
      if (value.includes(',') || value.includes('"') || value.includes('\n')) {
        value = `"${value.replace(/"/g, '""')}"`;
      }
      
      return value;
    });
    csvRows.push(values.join(','));
  });
  
  return csvRows.join('\n');
}

// Run export
const analysisFile = process.argv[2] || 'wilson-center-analysis.json';
const outputName = process.argv[3] || 'wilson-center';

try {
  exportToCSV(analysisFile, outputName);
} catch (error) {
  console.error('\n❌ Export failed:', error.message);
  process.exit(1);
}

