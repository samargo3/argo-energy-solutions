#!/usr/bin/env node
/**
 * Wilson Center Energy Analysis Script
 * 
 * Fetches and analyzes energy data from all Wilson Center channels
 * Generates a comprehensive summary report
 * 
 * Usage:
 *   node scripts/wilson-center-analysis.js
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
      res: options.res || options.resolution || '3600',
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

function saveToFile(data, filename) {
  const dataDir = path.join(__dirname, '..', 'data');
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  
  const filepath = path.join(dataDir, filename);
  fs.writeFileSync(filepath, JSON.stringify(data, null, 2));
  return filepath;
}

function formatDate(timestamp) {
  if (!timestamp) return 'N/A';
  const date = new Date(parseInt(timestamp) * 1000);
  return date.toLocaleString();
}

function calculateStats(values) {
  if (!values || values.length === 0) return null;
  
  const sum = values.reduce((a, b) => a + b, 0);
  const avg = sum / values.length;
  const max = Math.max(...values);
  const min = Math.min(...values);
  
  return { sum, avg, max, min, count: values.length };
}

async function analyzeChannel(client, channel, dateRange, resolution) {
  const channelId = channel.dataChannelId;
  const channelName = channel.channelName || channel.deviceName;
  
  console.log(`   📊 Analyzing: ${channelName} (ID: ${channelId})`);
  
  try {
    const readings = await client.getReadings(channelId, {
      fields: ['E', 'P', 'V', 'I', 'PF', 'kW', 'kWh'],
      daterange: dateRange,
      res: resolution,
      action: 'summarize',
    });

    // Add small delay to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 300));

    const readingList = readings.records || readings.data || readings.result || [];
    
    if (!readingList || readingList.length === 0) {
      console.log(`      ⚠️  No data available`);
      return {
        channel: channelName,
        channelId: channelId,
        status: 'no_data',
        dataPoints: 0
      };
    }

    // Extract values for analysis
    // API returns Wh and W, convert to kWh and kW by dividing by 1000
    const energyValues = readingList.map(r => r.E).filter(v => v != null && !isNaN(v)).map(v => v / 1000);
    const powerValues = readingList.map(r => r.P || r.kW).filter(v => v != null && !isNaN(v)).map(v => v / 1000);
    const voltageValues = readingList.map(r => r.V).filter(v => v != null && !isNaN(v));
    const currentValues = readingList.map(r => r.I).filter(v => v != null && !isNaN(v));
    const pfValues = readingList.map(r => r.PF).filter(v => v != null && !isNaN(v));

    // Find peak power timestamp
    let peakPowerTimestamp = null;
    if (powerValues.length > 0) {
      const maxPower = Math.max(...powerValues);
      const maxIndex = powerValues.findIndex((_, idx) => {
        const originalPower = readingList[idx]?.P || readingList[idx]?.kW || 0;
        return Math.abs((originalPower / 1000) - maxPower) < 0.01;
      });
      if (maxIndex >= 0 && readingList[maxIndex]?.ts) {
        peakPowerTimestamp = readingList[maxIndex].ts;
      }
    }

    // Calculate operating hours (non-zero power readings)
    const operatingReadings = powerValues.filter(p => p > 0.01); // >10W threshold
    const operatingHours = (operatingReadings.length * parseInt(resolution)) / 3600;

    const analysis = {
      channel: channelName,
      channelId: channelId,
      deviceType: channel.deviceTypeName,
      dataType: channel.dataType,
      status: 'success',
      dataPoints: readingList.length,
      operatingHours: operatingHours,
      timeRange: {
        start: readingList[0]?.ts ? formatDate(readingList[0].ts) : 'N/A',
        end: readingList[readingList.length - 1]?.ts ? formatDate(readingList[readingList.length - 1].ts) : 'N/A',
      },
      energy: calculateStats(energyValues),
      power: calculateStats(powerValues),
      voltage: calculateStats(voltageValues),
      current: calculateStats(currentValues),
      powerFactor: calculateStats(pfValues),
      peakPowerTimestamp: peakPowerTimestamp ? formatDate(peakPowerTimestamp) : null,
      rawReadings: readingList,
    };

    console.log(`      ✓ ${readingList.length} readings collected`);
    if (analysis.energy) {
      console.log(`      ⚡ Total Energy: ${analysis.energy.sum.toFixed(2)} kWh`);
    }
    if (analysis.power) {
      console.log(`      💡 Avg Power: ${analysis.power.avg.toFixed(2)} kW, Peak: ${analysis.power.max.toFixed(2)} kW`);
    }

    return analysis;
  } catch (error) {
    console.log(`      ❌ Error: ${error.message}`);
    return {
      channel: channelName,
      channelId: channelId,
      status: 'error',
      error: error.message,
      dataPoints: 0
    };
  }
}

function generateMarkdownReport(summary, analyses, dateRange) {
  const timestamp = new Date().toLocaleString();
  
  let report = `# Wilson Center Energy Analysis Report\n\n`;
  report += `**Generated:** ${timestamp}\n`;
  report += `**Date Range:** ${dateRange}\n`;
  report += `**Organization:** Argo Energy Solutions LLC\n\n`;
  report += `---\n\n`;

  // Maintenance Alerts (if any errors)
  if (summary.channelsWithErrors > 0) {
    report += `## ⚠️ MAINTENANCE ALERTS\n\n`;
    report += `**${summary.channelsWithErrors} channel(s) require attention:**\n\n`;
    const errorChannels = analyses.filter(a => a.status === 'error');
    errorChannels.forEach(ch => {
      report += `- **${ch.channel}** (ID: ${ch.channelId}): ${ch.error}\n`;
    });
    report += `\n⚠️ **Action Required:** These sensors may be offline or malfunctioning. Data completeness may be affected.\n\n`;
    report += `---\n\n`;
  }

  // Executive Summary
  report += `## Executive Summary\n\n`;
  
  if (summary.totalEnergy > 0) {
    // Financial and environmental impact
    report += `### Financial & Environmental Impact\n\n`;
    report += `| Metric | Value |\n`;
    report += `|--------|-------|\n`;
    report += `| **Total Energy Consumption** | ${Math.round(summary.totalEnergy).toLocaleString()} kWh |\n`;
    report += `| **Estimated Cost** | $${Math.round(summary.estimatedCost).toLocaleString()} |\n`;
    report += `| **Carbon Footprint** | ${Math.round(summary.carbonFootprint).toLocaleString()} lbs CO₂ (${(summary.carbonFootprint/2000).toFixed(1)} tons) |\n`;
    report += `| **Average Facility Load** | ${summary.avgPower.toFixed(1)} kW |\n`;
    report += `| **Peak Demand** | ${summary.peakPower.toFixed(1)} kW |\n`;
    if (summary.peakPowerTimestamp) {
      report += `| **Peak Occurred** | ${summary.peakPowerTimestamp} |\n`;
      report += `| **Peak Source** | ${summary.peakPowerChannel} |\n`;
    }
    report += `| **Average Power Factor** | ${summary.avgPowerFactor.toFixed(3)} |\n`;
    report += `\n`;

    // Key insights
    report += `### Key Insights\n\n`;
    const costPerDay = summary.estimatedCost / 30; // Rough estimate
    report += `- Operating at **${summary.avgPower.toFixed(1)} kW average load** (equivalent to ~${Math.round(summary.avgPower * 0.33)} homes)\n`;
    report += `- Daily electricity cost: **~$${Math.round(costPerDay)}**\n`;
    report += `- Environmental impact: **${(summary.carbonFootprint/2000).toFixed(1)} tons CO₂** (equivalent to ${((summary.carbonFootprint/2000) * 0.45).toFixed(1)} cars off the road)\n`;
    
    if (summary.avgPowerFactor < 0.85) {
      report += `- ⚠️ **Low power factor (${summary.avgPowerFactor.toFixed(3)})** may result in utility penalties\n`;
      if (summary.pfCorrectionSavings) {
        report += `- 💰 **Potential savings from PF correction:** ~$${Math.round(summary.pfCorrectionSavings)}/period\n`;
      }
    } else if (summary.avgPowerFactor >= 0.95) {
      report += `- ✓ **Excellent power factor (${summary.avgPowerFactor.toFixed(3)})** - no correction needed\n`;
    }
  }
  
  report += `\n---\n\n`;

  // Channel Details
  report += `## Channel Details\n\n`;

  // HVAC Systems
  const hvacChannels = analyses.filter(a => 
    a.channel.includes('RTU') || a.channel.includes('AHU')
  );
  
  if (hvacChannels.length > 0) {
    report += `### HVAC Systems\n\n`;
    hvacChannels.forEach(analysis => {
      report += generateChannelSection(analysis);
    });
  }

  // Kitchen/Electrical Panels
  const panelChannels = analyses.filter(a => 
    a.channel.includes('Kitchen') || a.channel.includes('Panel')
  );
  
  if (panelChannels.length > 0) {
    report += `### Electrical Panels\n\n`;
    panelChannels.forEach(analysis => {
      report += generateChannelSection(analysis);
    });
  }

  // Sensors
  const sensorChannels = analyses.filter(a => 
    a.channel.includes('Sense') || a.channel.includes('Sensor')
  );
  
  if (sensorChannels.length > 0) {
    report += `### Sensors\n\n`;
    sensorChannels.forEach(analysis => {
      report += generateChannelSection(analysis);
    });
  }

  // Recommendations
  report += `\n---\n\n`;
  report += `## Recommendations & Action Items\n\n`;
  
  if (summary.channelsWithData === 0) {
    report += `⚠️ **No data available for the selected date range.**\n\n`;
    report += `**Action Items:**\n`;
    report += `- Try a more recent date range (e.g., 'today', 'yesterday')\n`;
    report += `- Verify that devices are actively collecting data\n`;
    report += `- Check device registration and expiration dates\n\n`;
  } else {
    // Priority recommendations based on data
    report += `### Priority 1: Immediate Actions\n\n`;
    
    // Power factor issues
    const poorPFChannels = analyses.filter(a => a.powerFactor && a.powerFactor.avg < 0.50);
    if (poorPFChannels.length > 0) {
      report += `**🔴 Critical Power Factor Issues:**\n`;
      poorPFChannels.forEach(ch => {
        report += `- **${ch.channel}**: PF = ${ch.powerFactor.avg.toFixed(3)} - Investigate for motor/sensor issues\n`;
      });
      report += `\n*Action:* These extremely low power factors may indicate equipment malfunction or sensor errors.\n\n`;
    }
    
    // Maintenance alerts
    if (summary.channelsWithErrors > 0) {
      report += `**🔴 Equipment Maintenance:**\n`;
      report += `- ${summary.channelsWithErrors} sensor(s) offline - Schedule maintenance immediately\n\n`;
    }
    
    report += `### Priority 2: Efficiency Improvements\n\n`;
    
    // Power factor correction
    if (summary.avgPowerFactor < 0.85 && summary.pfCorrectionSavings) {
      report += `**💰 Power Factor Correction:**\n`;
      report += `- Current facility PF: ${summary.avgPowerFactor.toFixed(3)}\n`;
      report += `- Target PF: 0.95\n`;
      report += `- **Estimated annual savings:** ~$${Math.round(summary.pfCorrectionSavings * 12).toLocaleString()}\n`;
      report += `- *Action:* Install capacitor banks or upgrade motor controllers\n\n`;
    }
    
    // Peak demand management  
    if (summary.peakPowerTimestamp) {
      report += `**⚡ Peak Demand Management:**\n`;
      report += `- Peak of ${summary.peakPower.toFixed(1)} kW occurred at ${summary.peakPowerTimestamp}\n`;
      report += `- Peak source: ${summary.peakPowerChannel}\n`;
      report += `- *Action:* Review equipment schedules to shift/reduce peak demand\n\n`;
    }
    
    report += `### Priority 3: Long-term Optimization\n\n`;
    report += `**Energy Efficiency:**\n`;
    // Find highest consumers
    const withEnergy = analyses.filter(a => a.energy && a.energy.sum > 0)
      .sort((a, b) => b.energy.sum - a.energy.sum);
    
    if (withEnergy.length > 0) {
      report += `### Top Energy Consumers\n\n`;
      withEnergy.slice(0, 5).forEach((analysis, idx) => {
        report += `${idx + 1}. **${analysis.channel}**: ${analysis.energy.sum.toFixed(2)} kWh\n`;
      });
      report += `\n`;
    }

    // Peak demand analysis
    const withPower = analyses.filter(a => a.power && a.power.max > 0)
      .sort((a, b) => b.power.max - a.power.max);
    
    if (withPower.length > 0) {
      report += `### Peak Demand\n\n`;
      withPower.slice(0, 5).forEach((analysis, idx) => {
        report += `${idx + 1}. **${analysis.channel}**: ${analysis.power.max.toFixed(2)} kW peak\n`;
      });
      report += `\n`;
    }

    // Power quality
    const withPF = analyses.filter(a => a.powerFactor && a.powerFactor.avg > 0);
    if (withPF.length > 0) {
      const avgPF = withPF.reduce((sum, a) => sum + a.powerFactor.avg, 0) / withPF.length;
      report += `### Power Quality\n\n`;
      report += `- **Average Power Factor:** ${avgPF.toFixed(3)}\n`;
      if (avgPF < 0.90) {
        report += `- ⚠️ Power factor below optimal range (< 0.90). Consider power factor correction.\n`;
      } else if (avgPF >= 0.95) {
        report += `- ✓ Excellent power factor (≥ 0.95)\n`;
      }
      report += `\n`;
    }
  }

  report += `---\n\n`;
  report += `## Data Files\n\n`;
  report += `Detailed data has been saved to:\n`;
  report += `- \`data/wilson-center-analysis.json\` - Complete analysis with all readings\n`;
  report += `- \`data/wilson-center-summary.json\` - Summary statistics\n`;
  report += `- \`data/wilson-center-report.md\` - This report\n\n`;

  return report;
}

function generateChannelSection(analysis) {
  let section = `#### ${analysis.channel}\n\n`;
  
  if (analysis.status === 'success' && analysis.dataPoints > 0) {
    // Create a summary table
    section += `| Metric | Value |\n`;
    section += `|--------|-------|\n`;
    section += `| Channel ID | ${analysis.channelId} |\n`;
    section += `| Status | ✅ Active |\n`;
    section += `| Data Points | ${analysis.dataPoints.toLocaleString()} |\n`;
    
    if (analysis.operatingHours) {
      section += `| Operating Hours | ${analysis.operatingHours.toFixed(1)} hrs |\n`;
    }
    
    if (analysis.energy) {
      section += `| **Total Energy** | **${Math.round(analysis.energy.sum)} kWh** |\n`;
      section += `| Average per Reading | ${analysis.energy.avg.toFixed(2)} kWh |\n`;
    }
    
    if (analysis.power) {
      section += `| **Average Load** | **${analysis.power.avg.toFixed(2)} kW** |\n`;
      section += `| Peak Load | ${analysis.power.max.toFixed(2)} kW |\n`;
      section += `| Minimum Load | ${analysis.power.min.toFixed(2)} kW |\n`;
      if (analysis.peakPowerTimestamp) {
        section += `| Peak Occurred | ${analysis.peakPowerTimestamp} |\n`;
      }
    }
    
    if (analysis.voltage) {
      section += `| Average Voltage | ${analysis.voltage.avg.toFixed(1)} V |\n`;
      const voltageRange = analysis.voltage.max - analysis.voltage.min;
      const voltageHealth = voltageRange < 3 ? '✅ Stable' : voltageRange < 6 ? '⚠️ Moderate' : '❌ Unstable';
      section += `| Voltage Stability | ${voltageHealth} (${voltageRange.toFixed(1)}V range) |\n`;
    }
    
    if (analysis.powerFactor) {
      const pf = analysis.powerFactor.avg;
      let pfStatus = pf >= 0.95 ? '✅ Excellent' : pf >= 0.85 ? '⚠️ Acceptable' : '❌ Poor';
      section += `| **Power Factor** | **${pf.toFixed(3)}** ${pfStatus} |\n`;
    }
    
    section += `\n`;
    
    // Add observations if power factor is problematic
    if (analysis.powerFactor && analysis.powerFactor.avg < 0.85) {
      section += `**⚠️ Power Quality Issue:** Power factor of ${analysis.powerFactor.avg.toFixed(3)} indicates reactive power draw. `;
      section += `Consider capacitor banks or motor controllers to improve efficiency.\n\n`;
    }
    
  } else if (analysis.status === 'no_data') {
    section += `- ⚠️ No data available for this period\n`;
  } else if (analysis.status === 'error') {
    section += `- ❌ Error: ${analysis.error}\n`;
  }
  
  section += `\n`;
  return section;
}

async function main() {
  console.log('🏢 Wilson Center Energy Analysis\n');
  console.log('=' .repeat(60));

  // Configuration
  const dateRange = process.argv[2] || 'yesterday'; // Can be 'today', 'yesterday', 'lastweek', etc.
  const resolution = process.argv[3] || '900'; // 15 minutes default
  const electricityRate = parseFloat(process.argv[4]) || 0.12; // $/kWh, default $0.12
  const carbonFactor = parseFloat(process.argv[5]) || 0.92; // lbs CO2/kWh, US avg
  
  console.log(`\n📅 Date Range: ${dateRange}`);
  console.log(`⏱️  Resolution: ${resolution} seconds (${resolution/60} minutes)`);
  console.log(`💰 Electricity Rate: $${electricityRate}/kWh`);
  console.log(`🌍 Carbon Factor: ${carbonFactor} lbs CO2/kWh\n`);

  const client = new EniscopeAPIClient();

  try {
    // Authenticate
    console.log('🔐 Authenticating...');
    await client.authenticate();
    console.log('✓ Authentication successful\n');

    // Load channels from saved data
    const channelsPath = path.join(__dirname, '..', 'data', 'channels-org-23271.json');
    
    if (!fs.existsSync(channelsPath)) {
      console.error('❌ Channels data not found. Run: npm run analyze:energy');
      process.exit(1);
    }

    const channelsData = JSON.parse(fs.readFileSync(channelsPath, 'utf8'));
    const allChannels = channelsData.channels || [];

    // Filter Wilson Center channels
    const wilsonChannels = allChannels.filter(c => 
      c.channelName && 
      c.channelName.includes('Wilson') &&
      c.status === '1' &&
      c.in_tsdb === 'Y'
    );

    console.log(`📊 Found ${wilsonChannels.length} active Wilson Center channels\n`);
    console.log('Starting analysis...\n');

    // Analyze each channel
    const analyses = [];
    for (const channel of wilsonChannels) {
      const analysis = await analyzeChannel(client, channel, dateRange, resolution);
      analyses.push(analysis);
    }

    // Calculate summary statistics
    const totalEnergy = analyses.reduce((sum, a) => sum + (a.energy?.sum || 0), 0);
    const summary = {
      totalChannels: wilsonChannels.length,
      channelsWithData: analyses.filter(a => a.status === 'success' && a.dataPoints > 0).length,
      channelsWithErrors: analyses.filter(a => a.status === 'error').length,
      totalDataPoints: analyses.reduce((sum, a) => sum + (a.dataPoints || 0), 0),
      totalEnergy: totalEnergy,
      estimatedCost: totalEnergy * electricityRate,
      carbonFootprint: totalEnergy * carbonFactor, // lbs CO2
      avgPower: 0,
      peakPower: 0,
      peakPowerChannel: null,
      peakPowerTimestamp: null,
      avgPowerFactor: 0,
      electricityRate: electricityRate,
      carbonFactor: carbonFactor,
    };

    const powerAnalyses = analyses.filter(a => a.power);
    if (powerAnalyses.length > 0) {
      // Average Power should be the SUM of all channel averages (total facility load)
      summary.avgPower = powerAnalyses.reduce((sum, a) => sum + a.power.avg, 0);
      
      // Find peak power and its channel
      const peakAnalysis = powerAnalyses.reduce((max, a) => 
        a.power.max > max.power.max ? a : max
      );
      summary.peakPower = peakAnalysis.power.max;
      summary.peakPowerChannel = peakAnalysis.channel;
      summary.peakPowerTimestamp = peakAnalysis.peakPowerTimestamp;
    }

    // Calculate average power factor
    const pfAnalyses = analyses.filter(a => a.powerFactor);
    if (pfAnalyses.length > 0) {
      summary.avgPowerFactor = pfAnalyses.reduce((sum, a) => sum + a.powerFactor.avg, 0) / pfAnalyses.length;
      
      // Calculate potential savings from PF correction
      const targetPF = 0.95;
      if (summary.avgPowerFactor < targetPF) {
        // Estimate additional kVA demand charges (typically 5-15% penalty for low PF)
        const pfPenaltyPercent = (targetPF - summary.avgPowerFactor) * 20; // Rough estimate
        summary.pfCorrectionSavings = summary.estimatedCost * (pfPenaltyPercent / 100);
      }
    }

    // Save detailed analysis
    const analysisData = {
      summary,
      dateRange,
      resolution,
      generatedAt: new Date().toISOString(),
      channels: analyses,
    };

    saveToFile(analysisData, 'wilson-center-analysis.json');
    saveToFile(summary, 'wilson-center-summary.json');

    // Generate markdown report
    const report = generateMarkdownReport(summary, analyses, dateRange);
    const reportPath = path.join(__dirname, '..', 'data', 'wilson-center-report.md');
    fs.writeFileSync(reportPath, report);

    // Print summary
    console.log('\n' + '='.repeat(60));
    console.log('\n📈 Analysis Complete!\n');
    console.log(`✓ Analyzed ${summary.totalChannels} channels`);
    console.log(`✓ Collected ${summary.totalDataPoints.toLocaleString()} data points`);
    
    if (summary.channelsWithData > 0) {
      console.log(`✓ Total Energy: ${summary.totalEnergy.toFixed(2)} kWh`);
      if (summary.avgPower > 0) {
        console.log(`✓ Average Power: ${summary.avgPower.toFixed(2)} kW`);
        console.log(`✓ Peak Power: ${summary.peakPower.toFixed(2)} kW`);
      }
    } else {
      console.log(`\n⚠️  No data found for date range: ${dateRange}`);
      console.log(`   Try: 'today' or 'yesterday' instead`);
    }

    console.log('\n📁 Reports saved:');
    console.log(`   - data/wilson-center-analysis.json`);
    console.log(`   - data/wilson-center-summary.json`);
    console.log(`   - data/wilson-center-report.md`);
    console.log('');

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    process.exit(1);
  }
}

main();

