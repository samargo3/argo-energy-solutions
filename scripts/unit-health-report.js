#!/usr/bin/env node
/**
 * Unit Health Report Generator
 * 
 * Generates a comprehensive health assessment report for a specific unit/channel
 * 
 * Usage:
 *   node scripts/unit-health-report.js <channelId> <startDate> <endDate> [resolution]
 * 
 * Examples:
 *   node scripts/unit-health-report.js 162320 "2025-01-01" "2025-01-31" 3600
 *   node scripts/unit-health-report.js 162119 "2025-01-15" "2025-01-22" 900
 *   node scripts/unit-health-report.js 162320 yesterday today
 */

import axios from 'axios';
import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

// Chart generation functions (inline to avoid import issues)
function generatePowerTimeSeriesChart(readings, anomalies = []) {
  if (!readings || readings.length === 0) return null;
  
  const width = 800;
  const height = 400;
  const padding = { top: 40, right: 40, bottom: 60, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const data = readings.map((r, idx) => ({
    timestamp: parseInt(r.ts),
    power: (r.P || r.kW || 0) / 1000,
    isAnomaly: anomalies.some(a => a.timestamp === r.ts),
  }));

  const powerValues = data.map(d => d.power);
  const minPower = Math.min(...powerValues);
  const maxPower = Math.max(...powerValues);
  const powerRange = maxPower - minPower || 1;

  let svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">`;
  svg += `<rect width="${width}" height="${height}" fill="#f9fafb"/>`;
  svg += `<g transform="translate(${padding.left},${padding.top})">`;
  
  for (let i = 0; i <= 5; i++) {
    const y = (chartHeight / 5) * i;
    svg += `<line x1="0" y1="${y}" x2="${chartWidth}" y2="${y}" stroke="#e5e7eb" stroke-width="1"/>`;
  }
  
  let path = '';
  data.forEach((point, idx) => {
    const x = (idx / (data.length - 1)) * chartWidth;
    const y = chartHeight - ((point.power - minPower) / powerRange) * chartHeight;
    path += idx === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
  });
  
  svg += `<path d="${path}" fill="none" stroke="#3b82f6" stroke-width="2"/>`;
  
  data.forEach((point, idx) => {
    if (point.isAnomaly) {
      const x = (idx / (data.length - 1)) * chartWidth;
      const y = chartHeight - ((point.power - minPower) / powerRange) * chartHeight;
      svg += `<circle cx="${x}" cy="${y}" r="4" fill="#ef4444"/>`;
    }
  });
  
  svg += `<text x="${chartWidth / 2}" y="${chartHeight + 40}" text-anchor="middle" font-size="12" fill="#374151">Time</text>`;
  svg += `<text x="-30" y="${chartHeight / 2}" text-anchor="middle" font-size="12" fill="#374151" transform="rotate(-90, -30, ${chartHeight / 2})">Power (kW)</text>`;
  svg += `</g></svg>`;
  
  return svg;
}

function generateVoltageStabilityChart(readings) {
  const data = readings
    .map(r => ({ timestamp: parseInt(r.ts), voltage: r.V }))
    .filter(d => d.voltage !== undefined && !isNaN(d.voltage));

  if (data.length === 0) return null;

  const width = 800;
  const height = 300;
  const padding = { top: 40, right: 40, bottom: 60, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const voltages = data.map(d => d.voltage);
  const minVoltage = Math.min(...voltages);
  const maxVoltage = Math.max(...voltages);
  const avgVoltage = voltages.reduce((a, b) => a + b, 0) / voltages.length;
  const voltageRange = maxVoltage - minVoltage || 1;

  let svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">`;
  svg += `<rect width="${width}" height="${height}" fill="#f9fafb"/>`;
  svg += `<g transform="translate(${padding.left},${padding.top})">`;
  
  const avgY = chartHeight - ((avgVoltage - minVoltage) / voltageRange) * chartHeight;
  svg += `<line x1="0" y1="${avgY}" x2="${chartWidth}" y2="${avgY}" stroke="#10b981" stroke-width="2" stroke-dasharray="5,5"/>`;
  
  let path = '';
  data.forEach((point, idx) => {
    const x = (idx / (data.length - 1)) * chartWidth;
    const y = chartHeight - ((point.voltage - minVoltage) / voltageRange) * chartHeight;
    path += idx === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
  });
  
  svg += `<path d="${path}" fill="none" stroke="#8b5cf6" stroke-width="2"/>`;
  svg += `<text x="${chartWidth / 2}" y="${chartHeight + 40}" text-anchor="middle" font-size="12" fill="#374151">Time</text>`;
  svg += `<text x="-30" y="${chartHeight / 2}" text-anchor="middle" font-size="12" fill="#374151" transform="rotate(-90, -30, ${chartHeight / 2})">Voltage (V)</text>`;
  svg += `<text x="${chartWidth - 10}" y="${avgY - 5}" text-anchor="end" font-size="10" fill="#10b981">Avg: ${avgVoltage.toFixed(1)}V</text>`;
  svg += `</g></svg>`;
  
  return svg;
}

function generatePowerFactorChart(readings) {
  const data = readings
    .map(r => ({ timestamp: parseInt(r.ts), pf: r.PF }))
    .filter(d => d.pf !== undefined && !isNaN(d.pf));

  if (data.length === 0) return null;

  const width = 800;
  const height = 300;
  const padding = { top: 40, right: 40, bottom: 60, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const pfs = data.map(d => d.pf);
  const minPF = Math.min(...pfs);
  const maxPF = Math.max(...pfs);
  const pfRange = maxPF - minPF || 1;

  let svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">`;
  svg += `<rect width="${width}" height="${height}" fill="#f9fafb"/>`;
  svg += `<g transform="translate(${padding.left},${padding.top})">`;
  
  const targetY = chartHeight - ((0.85 - minPF) / pfRange) * chartHeight;
  svg += `<line x1="0" y1="${targetY}" x2="${chartWidth}" y2="${targetY}" stroke="#f59e0b" stroke-width="2" stroke-dasharray="5,5"/>`;
  
  let path = '';
  data.forEach((point, idx) => {
    const x = (idx / (data.length - 1)) * chartWidth;
    const y = chartHeight - ((point.pf - minPF) / pfRange) * chartHeight;
    path += idx === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
  });
  
  svg += `<path d="${path}" fill="none" stroke="#ef4444" stroke-width="2"/>`;
  svg += `<text x="${chartWidth / 2}" y="${chartHeight + 40}" text-anchor="middle" font-size="12" fill="#374151">Time</text>`;
  svg += `<text x="-30" y="${chartHeight / 2}" text-anchor="middle" font-size="12" fill="#374151" transform="rotate(-90, -30, ${chartHeight / 2})">Power Factor</text>`;
  svg += `<text x="${chartWidth - 10}" y="${targetY - 5}" text-anchor="end" font-size="10" fill="#f59e0b">Target: 0.85</text>`;
  svg += `</g></svg>`;
  
  return svg;
}

function generateDailyPatternChart(readings) {
  if (!readings || readings.length === 0) return null;
  
  const hourlyData = {};
  readings.forEach(r => {
    const date = new Date(parseInt(r.ts) * 1000);
    const hour = date.getHours();
    if (!hourlyData[hour]) {
      hourlyData[hour] = { count: 0, total: 0 };
    }
    hourlyData[hour].total += (r.P || r.kW || 0) / 1000;
    hourlyData[hour].count++;
  });

  const hours = Array.from({ length: 24 }, (_, i) => i);
  const avgPowerByHour = hours.map(h => {
    const data = hourlyData[h];
    return data ? data.total / data.count : 0;
  });

  const maxPower = Math.max(...avgPowerByHour) || 1;

  const width = 800;
  const height = 300;
  const padding = { top: 40, right: 40, bottom: 60, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const barWidth = chartWidth / 24;

  let svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">`;
  svg += `<rect width="${width}" height="${height}" fill="#f9fafb"/>`;
  svg += `<g transform="translate(${padding.left},${padding.top})">`;
  
  avgPowerByHour.forEach((power, hour) => {
    const barHeight = (power / maxPower) * chartHeight;
    const x = hour * barWidth;
    const y = chartHeight - barHeight;
    svg += `<rect x="${x}" y="${y}" width="${barWidth - 2}" height="${barHeight}" fill="#3b82f6" opacity="0.8"/>`;
    if (hour % 3 === 0) {
      svg += `<text x="${x + barWidth / 2}" y="${chartHeight + 20}" text-anchor="middle" font-size="10" fill="#374151">${hour}:00</text>`;
    }
  });
  
  svg += `<text x="${chartWidth / 2}" y="${chartHeight + 40}" text-anchor="middle" font-size="12" fill="#374151">Hour of Day</text>`;
  svg += `<text x="-30" y="${chartHeight / 2}" text-anchor="middle" font-size="12" fill="#374151" transform="rotate(-90, -30, ${chartHeight / 2})">Average Power (kW)</text>`;
  svg += `</g></svg>`;
  
  return svg;
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load .env file
const envPath = path.join(__dirname, '..', '.env');
dotenv.config({ path: envPath });

// Check if .env file exists
if (!fs.existsSync(envPath)) {
  console.warn(`⚠️  Warning: .env file not found at ${envPath}`);
  console.warn('   Trying to load from environment variables...\n');
}

const ENISCOPE_API_URL = process.env.VITE_ENISCOPE_API_URL || process.env.VITE_BEST_ENERGY_API_URL || process.env.ENISCOPE_API_URL || 'https://core.eniscope.com';
const ENISCOPE_API_KEY = process.env.VITE_ENISCOPE_API_KEY || process.env.VITE_BEST_ENERGY_API_KEY || process.env.ENISCOPE_API_KEY || '';
const ENISCOPE_EMAIL = process.env.VITE_ENISCOPE_EMAIL || process.env.ENISCOPE_EMAIL || '';
const ENISCOPE_PASSWORD = process.env.VITE_ENISCOPE_PASSWORD || process.env.ENISCOPE_PASSWORD || '';

// Wilson Center channel names for reference
const CHANNEL_NAMES = {
  '162320': 'RTU-1_WCDS_Wilson Ctr',
  '162119': 'RTU-2_WCDS_Wilson Ctr',
  '162120': 'RTU-3_WCDS_Wilson Ctr',
  '162122': 'AHU-1A_WCDS_Wilson Ctr',
  '162123': 'AHU-1B_WCDS_Wilson Ctr',
  '162121': 'AHU-2_WCDS_Wilson Ctr',
  '162285': 'CDPK_Kitchen Main Panel(s)_WCDS_Wilson Ctr',
  '162319': 'CDKH_Kitchen Panel(small)_WCDS_Wilson Ctr',
  '162277': 'Air Sense_Main Kitchen_WCDS_Wilson',
};

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

  async authenticate(retries = 3) {
    const authString = `${this.email}:${this.passwordMd5}`;
    const authB64 = Buffer.from(authString).toString('base64');

    // Try the endpoint that works in other scripts first
    const endpoint = `${this.baseUrl}/organizations`;
    
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        if (attempt > 0) {
          const delay = Math.pow(2, attempt) * 1000; // Exponential backoff: 2s, 4s, 8s
          console.log(`   ⏳ Rate limited. Retrying in ${delay/1000}s... (attempt ${attempt + 1}/${retries})`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }

        const response = await axios.get(endpoint, {
          headers: {
            'Authorization': `Basic ${authB64}`,
            'X-Eniscope-API': this.apiKey,
            'Accept': 'text/json',
          },
        });

        this.sessionToken = response.headers['x-eniscope-token'] || response.headers['X-Eniscope-Token'] || null;
        return true;
      } catch (error) {
        // If 429 (rate limit), retry
        if (error.response?.status === 429 && attempt < retries - 1) {
          continue; // Will retry with backoff
        }
        
        // If 404, try alternative endpoint format (only on first attempt)
        if (error.response?.status === 404 && attempt === 0) {
          console.log('   ⚠️  Trying alternative endpoint format...');
          try {
            const altEndpoint = `${this.baseUrl}/v1/1/organizations`;
            const response = await axios.get(altEndpoint, {
              headers: {
                'Authorization': `Basic ${authB64}`,
                'X-Eniscope-API': this.apiKey,
                'Accept': 'text/json',
              },
            });
            this.sessionToken = response.headers['x-eniscope-token'] || response.headers['X-Eniscope-Token'] || null;
            return true;
          } catch (altError) {
            // If alt endpoint also fails, continue with original error handling
            if (altError.response?.status === 429 && attempt < retries - 1) {
              continue;
            }
          }
        }
        
        // If we've exhausted retries or it's not a retryable error, throw
        if (attempt === retries - 1 || error.response?.status !== 429) {
          console.error('❌ Authentication failed');
          console.error(`   Endpoint: ${endpoint}`);
          console.error(`   Status: ${error.response?.status} - ${error.response?.statusText || error.message}`);
          if (error.response?.status === 429) {
            console.error('   💡 Tip: Wait a few minutes and try again, or reduce concurrent API calls');
          }
          throw error;
        }
      }
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
        
        // Update session token if provided
        const token = response.headers['x-eniscope-token'] || response.headers['X-Eniscope-Token'];
        if (token) {
          this.sessionToken = token;
        }
        
        return response.data;
      } catch (error) {
        // Handle 429 (rate limit) with exponential backoff
        if (error.response?.status === 429 && attempt < retries - 1) {
          const delay = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s
          console.log(`   ⏳ Rate limited. Retrying in ${delay/1000}s... (attempt ${attempt + 1}/${retries})`);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
        
        // Handle 401/419 (unauthorized) - try to re-authenticate
        if ((error.response?.status === 401 || error.response?.status === 419) && attempt < retries - 1) {
          console.log(`   🔄 Session expired. Re-authenticating...`);
          this.sessionToken = null;
          await this.authenticate();
          if (this.sessionToken) {
            headers['X-Eniscope-Token'] = this.sessionToken;
            continue; // Retry the request
          }
        }
        
        // If we've exhausted retries or it's not a retryable error, throw
        throw error;
      }
    }
  }

  async getChannelInfo(channelId) {
    try {
      // Try v1/1 format first, fallback to direct format
      try {
        return await this.makeRequest(`/v1/1/channels/${channelId}`);
      } catch (error) {
        if (error.response?.status === 404) {
          return await this.makeRequest(`/channels/${channelId}`);
        }
        throw error;
      }
    } catch (error) {
      console.warn(`   ⚠️  Could not fetch channel info: ${error.message}`);
      return null;
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
    } else {
      params['fields[]'] = ['E', 'P', 'V', 'I', 'PF', 'kW', 'kWh'];
    }

    if (options.daterange) {
      if (Array.isArray(options.daterange)) {
        params['daterange[]'] = options.daterange;
      } else {
        params.daterange = options.daterange;
      }
    }

    // Try v1/1 format first, fallback to direct format
    try {
      return await this.makeRequest(`/v1/1/readings/${channelId}`, params);
    } catch (error) {
      if (error.response?.status === 404) {
        console.log('   ⚠️  Trying alternative endpoint format for readings...');
        return await this.makeRequest(`/readings/${channelId}`, params);
      }
      throw error;
    }
  }
}

function parseDate(dateStr) {
  const lower = dateStr.toLowerCase();
  const now = new Date();
  
  if (lower === 'today') {
    return new Date(now.setHours(0, 0, 0, 0));
  } else if (lower === 'yesterday') {
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    yesterday.setHours(0, 0, 0, 0);
    return yesterday;
  } else if (lower.startsWith('last')) {
    const match = lower.match(/last\s*(\d+)\s*(day|days|week|weeks|month|months)/);
    if (match) {
      const num = parseInt(match[1]);
      const unit = match[2];
      const date = new Date(now);
      if (unit.startsWith('day')) date.setDate(date.getDate() - num);
      else if (unit.startsWith('week')) date.setDate(date.getDate() - (num * 7));
      else if (unit.startsWith('month')) date.setMonth(date.getMonth() - num);
      date.setHours(0, 0, 0, 0);
      return date;
    }
  }
  
  // Try parsing as ISO date
  const parsed = new Date(dateStr);
  if (isNaN(parsed.getTime())) {
    throw new Error(`Invalid date format: ${dateStr}`);
  }
  return parsed;
}

function formatDate(timestamp) {
  if (!timestamp) return 'N/A';
  const date = new Date(parseInt(timestamp) * 1000);
  return date.toLocaleString();
}

function calculateStats(values) {
  if (!values || values.length === 0) return null;
  
  const validValues = values.filter(v => v != null && !isNaN(v) && isFinite(v));
  if (validValues.length === 0) return null;
  
  const sum = validValues.reduce((a, b) => a + b, 0);
  const avg = sum / validValues.length;
  const sorted = [...validValues].sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)];
  const max = Math.max(...validValues);
  const min = Math.min(...validValues);
  const variance = validValues.reduce((sum, val) => sum + Math.pow(val - avg, 2), 0) / validValues.length;
  const stdDev = Math.sqrt(variance);
  
  return { sum, avg, median, max, min, stdDev, count: validValues.length };
}

function detectAnomalies(readings) {
  const anomalies = [];
  
  if (!readings || readings.length === 0) {
    return { anomalies: [], summary: { total: 0, critical: 0, high: 0, medium: 0, low: 0 } };
  }

  // Convert readings to standardized format
  const data = readings.map(r => ({
    ts: r.ts,
    energy: r.E ? r.E / 1000 : 0, // Wh to kWh
    power: r.P ? r.P / 1000 : 0, // W to kW
    voltage: r.V,
    current: r.I,
    powerFactor: r.PF,
  }));

  const powerValues = data.map(d => d.power).filter(p => p !== undefined && !isNaN(p) && p > 0);
  const voltageValues = data.map(d => d.voltage).filter(v => v !== undefined && !isNaN(v));
  const pfValues = data.map(d => d.powerFactor).filter(pf => pf !== undefined && !isNaN(pf));

  if (powerValues.length === 0) {
    return { anomalies: [], summary: { total: 0, critical: 0, high: 0, medium: 0, low: 0 } };
  }

  const powerStats = calculateStats(powerValues);
  const voltageStats = voltageValues.length > 0 ? calculateStats(voltageValues) : null;
  const pfStats = pfValues.length > 0 ? calculateStats(pfValues) : null;

  // Detect power spikes (3+ standard deviations)
  data.forEach((reading, index) => {
    if (reading.power !== undefined && !isNaN(reading.power) && powerStats) {
      const zScore = Math.abs((reading.power - powerStats.avg) / (powerStats.stdDev || 1));
      
      if (zScore > 4) {
        anomalies.push({
          type: 'power_spike',
          severity: 'critical',
          timestamp: reading.ts,
          value: reading.power,
          expectedValue: powerStats.avg,
          description: `Critical power spike: ${reading.power.toFixed(2)} kW (expected ~${powerStats.avg.toFixed(2)} kW, ${zScore.toFixed(1)}σ)`,
        });
      } else if (zScore > 3) {
        anomalies.push({
          type: 'power_spike',
          severity: 'high',
          timestamp: reading.ts,
          value: reading.power,
          expectedValue: powerStats.avg,
          description: `Significant power spike: ${reading.power.toFixed(2)} kW (${zScore.toFixed(1)}σ above average)`,
        });
      }
    }
  });

  // Detect power drops
  data.forEach((reading, index) => {
    if (index > 0 && reading.power !== undefined && !isNaN(reading.power)) {
      const prevPower = data[index - 1].power || 0;
      if (prevPower > 0.1 && reading.power < prevPower * 0.5 && reading.power < 0.1) {
        anomalies.push({
          type: 'power_drop',
          severity: 'medium',
          timestamp: reading.ts,
          value: reading.power,
          expectedValue: prevPower,
          description: `Sudden power drop: ${reading.power.toFixed(2)} kW (from ${prevPower.toFixed(2)} kW)`,
        });
      }
    }
  });

  // Detect zero readings when equipment should be running
  const avgNonZeroPower = powerValues.length > 0 ? powerValues.reduce((sum, p) => sum + p, 0) / powerValues.length : 0;
  data.forEach((reading, index) => {
    if (reading.power < 0.01 && avgNonZeroPower > 0.1) {
      const contextWindow = data.slice(Math.max(0, index - 3), Math.min(data.length, index + 4));
      const contextAvg = contextWindow
        .map(r => r.power || 0)
        .filter(p => p > 0.01)
        .reduce((sum, p, _, arr) => sum + p / arr.length, 0);

      if (contextAvg > 0.1) {
        anomalies.push({
          type: 'zero_reading',
          severity: 'medium',
          timestamp: reading.ts,
          value: reading.power,
          expectedValue: contextAvg,
          description: `Unexpected zero power reading (equipment may be offline)`,
        });
      }
    }
  });

  // Detect voltage anomalies
  if (voltageStats) {
    data.forEach(reading => {
      if (reading.voltage !== undefined && !isNaN(reading.voltage)) {
        const voltageDeviation = Math.abs(reading.voltage - voltageStats.avg);
        const voltagePercentDeviation = (voltageDeviation / voltageStats.avg) * 100;

        if (voltagePercentDeviation > 15) {
          anomalies.push({
            type: 'voltage_anomaly',
            severity: 'high',
            timestamp: reading.ts,
            value: reading.voltage,
            expectedValue: voltageStats.avg,
            description: `Voltage anomaly: ${reading.voltage.toFixed(1)} V (expected ~${voltageStats.avg.toFixed(1)} V, ${voltagePercentDeviation.toFixed(1)}% deviation)`,
          });
        } else if (voltagePercentDeviation > 10) {
          anomalies.push({
            type: 'voltage_anomaly',
            severity: 'medium',
            timestamp: reading.ts,
            value: reading.voltage,
            expectedValue: voltageStats.avg,
            description: `Voltage deviation: ${reading.voltage.toFixed(1)} V (${voltagePercentDeviation.toFixed(1)}% from average)`,
          });
        }
      }
    });
  }

  // Detect power factor issues
  if (pfStats) {
    data.forEach(reading => {
      if (reading.powerFactor !== undefined && !isNaN(reading.powerFactor)) {
        if (reading.powerFactor < 0.5 && reading.power > 0.1) {
          anomalies.push({
            type: 'power_factor_issue',
            severity: 'high',
            timestamp: reading.ts,
            value: reading.powerFactor,
            expectedValue: 0.85,
            description: `Very low power factor: ${reading.powerFactor.toFixed(3)} (target: >0.85)`,
          });
        } else if (reading.powerFactor < 0.7 && reading.power > 0.1) {
          anomalies.push({
            type: 'power_factor_issue',
            severity: 'medium',
            timestamp: reading.ts,
            value: reading.powerFactor,
            expectedValue: 0.85,
            description: `Low power factor: ${reading.powerFactor.toFixed(3)}`,
          });
        }
      }
    });
  }

  const summary = {
    total: anomalies.length,
    critical: anomalies.filter(a => a.severity === 'critical').length,
    high: anomalies.filter(a => a.severity === 'high').length,
    medium: anomalies.filter(a => a.severity === 'medium').length,
    low: anomalies.filter(a => a.severity === 'low').length,
  };

  return { anomalies: anomalies.sort((a, b) => {
    const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
    return severityOrder[b.severity] - severityOrder[a.severity];
  }), summary };
}

function determineHealthStatus(anomalySummary, stats) {
  if (anomalySummary.critical > 0 || anomalySummary.high > 5) {
    return { status: 'critical', color: '🔴', description: 'Immediate attention required' };
  } else if (anomalySummary.high > 2 || anomalySummary.medium > 10) {
    return { status: 'poor', color: '🟠', description: 'Maintenance recommended' };
  } else if (anomalySummary.medium > 5 || anomalySummary.total > 15) {
    return { status: 'fair', color: '🟡', description: 'Some issues detected' };
  } else if (anomalySummary.total > 5) {
    return { status: 'good', color: '🟢', description: 'Minor issues only' };
  } else {
    return { status: 'excellent', color: '✅', description: 'Operating normally' };
  }
}

function generateReport(channelId, channelName, channelInfo, readings, stats, anomalyAnalysis, healthStatus, dateRange, resolution, generateHTML = false) {
  const timestamp = new Date().toLocaleString();
  const startDate = formatDate(dateRange.startTs);
  const endDate = formatDate(dateRange.endTs);
  
  // Get anomaly timestamps for chart highlighting
  const anomalyTimestamps = new Set(anomalyAnalysis.anomalies.map(a => a.timestamp));
  
  if (generateHTML) {
    return generateHTMLReport(channelId, channelName, channelInfo, readings, stats, anomalyAnalysis, healthStatus, dateRange, resolution, anomalyTimestamps, timestamp, startDate, endDate);
  }
  
  let report = `# Unit Health Assessment Report\n\n`;
  report += `**Generated:** ${timestamp}\n`;
  report += `**Unit:** ${channelName || `Channel ${channelId}`}\n`;
  report += `**Channel ID:** ${channelId}\n`;
  if (channelInfo) {
    report += `**Device Type:** ${channelInfo.deviceTypeName || 'N/A'}\n`;
    report += `**Organization:** ${channelInfo.organizationId || 'N/A'}\n`;
  }
  report += `**Date Range:** ${startDate} - ${endDate}\n`;
  report += `**Resolution:** ${resolution} seconds (${resolution/60} minutes)\n`;
  report += `\n---\n\n`;

  // Equipment Health Status
  report += `## ${healthStatus.color} Equipment Health: ${healthStatus.status.toUpperCase()}\n\n`;
  report += `${healthStatus.description}\n\n`;
  report += `---\n\n`;

  // Executive Summary
  report += `## Executive Summary\n\n`;
  
  if (stats && stats.energy) {
    report += `| Metric | Value |\n`;
    report += `|--------|-------|\n`;
    report += `| **Total Energy Consumption** | ${stats.energy.sum.toFixed(2)} kWh |\n`;
    report += `| **Average Power** | ${stats.power.avg.toFixed(2)} kW |\n`;
    report += `| **Peak Power** | ${stats.power.max.toFixed(2)} kW |\n`;
    report += `| **Minimum Power** | ${stats.power.min.toFixed(2)} kW |\n`;
    if (stats.voltage) {
      report += `| **Average Voltage** | ${stats.voltage.avg.toFixed(1)} V |\n`;
      const voltageRange = stats.voltage.max - stats.voltage.min;
      const voltageStability = voltageRange < 3 ? '✅ Stable' : voltageRange < 6 ? '⚠️ Moderate' : '❌ Unstable';
      report += `| **Voltage Stability** | ${voltageStability} (${voltageRange.toFixed(1)}V range) |\n`;
    }
    if (stats.powerFactor) {
      const pf = stats.powerFactor.avg;
      const pfStatus = pf >= 0.95 ? '✅ Excellent' : pf >= 0.85 ? '⚠️ Acceptable' : '❌ Poor';
      report += `| **Average Power Factor** | ${pf.toFixed(3)} ${pfStatus} |\n`;
    }
    report += `| **Data Points** | ${readings.length.toLocaleString()} |\n`;
    report += `\n`;
  }

  // Anomaly Summary
  if (anomalyAnalysis.summary.total > 0) {
    report += `## Anomaly Detection Summary\n\n`;
    report += `| Severity | Count |\n`;
    report += `|----------|-------|\n`;
    report += `| 🔴 Critical | ${anomalyAnalysis.summary.critical} |\n`;
    report += `| 🟠 High | ${anomalyAnalysis.summary.high} |\n`;
    report += `| 🟡 Medium | ${anomalyAnalysis.summary.medium} |\n`;
    report += `| 🔵 Low | ${anomalyAnalysis.summary.low} |\n`;
    report += `| **Total** | **${anomalyAnalysis.summary.total}** |\n`;
    report += `\n---\n\n`;
  }

  // Detailed Anomalies
  if (anomalyAnalysis.anomalies.length > 0) {
    report += `## Detected Anomalies\n\n`;
    
    anomalyAnalysis.anomalies.forEach((anomaly, idx) => {
      const severityEmoji = {
        critical: '🔴',
        high: '🟠',
        medium: '🟡',
        low: '🔵',
      }[anomaly.severity] || '⚪';
      
      report += `### ${severityEmoji} ${idx + 1}. ${anomaly.type.replace(/_/g, ' ').toUpperCase()} (${anomaly.severity.toUpperCase()})\n\n`;
      report += `- **Timestamp:** ${formatDate(anomaly.timestamp)}\n`;
      report += `- **Value:** ${anomaly.value.toFixed(2)} ${anomaly.type.includes('power') ? 'kW' : anomaly.type.includes('voltage') ? 'V' : ''}\n`;
      if (anomaly.expectedValue !== undefined) {
        report += `- **Expected:** ${anomaly.expectedValue.toFixed(2)}\n`;
      }
      report += `- **Description:** ${anomaly.description}\n\n`;
    });
    
    report += `---\n\n`;
  } else {
    report += `## ✅ No Anomalies Detected\n\n`;
    report += `Equipment appears to be operating normally during the selected time period.\n\n`;
    report += `---\n\n`;
  }

  // Recommendations
  report += `## Recommendations & Action Items\n\n`;
  
  const recommendations = [];
  
  if (anomalyAnalysis.summary.critical > 0) {
    recommendations.push('🔴 **CRITICAL:** Immediate equipment inspection required. Schedule maintenance immediately.');
  }
  
  if (anomalyAnalysis.summary.high > 0) {
    recommendations.push('🟠 **HIGH PRIORITY:** Schedule maintenance check within 24-48 hours.');
  }
  
  const pfIssues = anomalyAnalysis.anomalies.filter(a => a.type === 'power_factor_issue').length;
  if (pfIssues > 0 && stats.powerFactor && stats.powerFactor.avg < 0.85) {
    recommendations.push('💡 **Power Factor Correction:** Consider installing capacitor banks or upgrading motor controllers to improve power factor.');
  }
  
  const voltageIssues = anomalyAnalysis.anomalies.filter(a => a.type === 'voltage_anomaly').length;
  if (voltageIssues > 0) {
    recommendations.push('⚡ **Power Quality Review:** Investigate voltage fluctuations. Check electrical supply and equipment connections.');
  }
  
  const powerSpikes = anomalyAnalysis.anomalies.filter(a => a.type === 'power_spike').length;
  if (powerSpikes > 0) {
    recommendations.push('📈 **Load Analysis:** Review equipment schedules and identify causes of power spikes. Consider load balancing.');
  }
  
  if (anomalyAnalysis.summary.total === 0) {
    recommendations.push('✅ **No Action Required:** Equipment is operating within normal parameters.');
  }
  
  if (recommendations.length === 0) {
    recommendations.push('✅ Continue monitoring. No immediate action required.');
  }
  
  recommendations.forEach((rec, idx) => {
    report += `${idx + 1}. ${rec}\n\n`;
  });

  // Statistical Details
  report += `---\n\n`;
  report += `## Statistical Details\n\n`;
  
  if (stats) {
    if (stats.power) {
      report += `### Power Statistics\n\n`;
      report += `- Average: ${stats.power.avg.toFixed(2)} kW\n`;
      report += `- Median: ${stats.power.median.toFixed(2)} kW\n`;
      report += `- Peak: ${stats.power.max.toFixed(2)} kW\n`;
      report += `- Minimum: ${stats.power.min.toFixed(2)} kW\n`;
      report += `- Standard Deviation: ${stats.power.stdDev.toFixed(2)} kW\n`;
      report += `\n`;
    }
    
    if (stats.energy) {
      report += `### Energy Consumption\n\n`;
      report += `- Total: ${stats.energy.sum.toFixed(2)} kWh\n`;
      report += `- Average per Reading: ${stats.energy.avg.toFixed(2)} kWh\n`;
      report += `\n`;
    }
  }

  report += `---\n\n`;
  report += `*Report generated by Argo Energy Solutions Unit Health Assessment Tool*\n`;

  return report;
}

function generateHTMLReport(channelId, channelName, channelInfo, readings, stats, anomalyAnalysis, healthStatus, dateRange, resolution, anomalyTimestamps, timestamp, startDate, endDate) {
  // Generate charts
  const powerChart = generatePowerTimeSeriesChart(readings, Array.from(anomalyTimestamps).map(ts => ({ timestamp: ts })));
  const voltageChart = generateVoltageStabilityChart(readings);
  const pfChart = generatePowerFactorChart(readings);
  const dailyPatternChart = generateDailyPatternChart(readings);

  let html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Unit Health Assessment - ${channelName}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      line-height: 1.6;
      color: #1f2937;
      background: #f9fafb;
      padding: 2rem;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      padding: 2rem;
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    h1 {
      color: #1f2937;
      border-bottom: 3px solid #3b82f6;
      padding-bottom: 0.5rem;
      margin-bottom: 1.5rem;
    }
    h2 {
      color: #374151;
      margin-top: 2rem;
      margin-bottom: 1rem;
      padding-bottom: 0.5rem;
      border-bottom: 2px solid #e5e7eb;
    }
    h3 {
      color: #4b5563;
      margin-top: 1.5rem;
      margin-bottom: 0.75rem;
    }
    .health-status {
      padding: 1rem;
      border-radius: 8px;
      margin: 1rem 0;
      font-size: 1.25rem;
      font-weight: 600;
    }
    .health-critical { background: #fee2e2; color: #991b1b; }
    .health-poor { background: #fed7aa; color: #92400e; }
    .health-fair { background: #fef3c7; color: #78350f; }
    .health-good { background: #d1fae5; color: #065f46; }
    .health-excellent { background: #dbeafe; color: #1e40af; }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 1rem 0;
    }
    th, td {
      padding: 0.75rem;
      text-align: left;
      border-bottom: 1px solid #e5e7eb;
    }
    th {
      background: #f9fafb;
      font-weight: 600;
      color: #374151;
    }
    .chart-container {
      margin: 2rem 0;
      padding: 1rem;
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
    }
    .chart-title {
      font-size: 1.1rem;
      font-weight: 600;
      margin-bottom: 1rem;
      color: #374151;
    }
    .anomaly-list {
      list-style: none;
      padding: 0;
    }
    .anomaly-item {
      padding: 1rem;
      margin: 0.5rem 0;
      border-left: 4px solid;
      border-radius: 4px;
      background: #f9fafb;
    }
    .anomaly-critical { border-color: #dc2626; }
    .anomaly-high { border-color: #ef4444; }
    .anomaly-medium { border-color: #f59e0b; }
    .anomaly-low { border-color: #3b82f6; }
    .recommendations {
      background: #eff6ff;
      padding: 1.5rem;
      border-radius: 8px;
      border-left: 4px solid #3b82f6;
      margin: 1rem 0;
    }
    .recommendations li {
      margin: 0.5rem 0;
      padding-left: 0.5rem;
    }
    .summary-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin: 1.5rem 0;
    }
    .summary-card {
      padding: 1rem;
      background: #f9fafb;
      border-radius: 8px;
      border: 1px solid #e5e7eb;
    }
    .summary-card h4 {
      font-size: 0.875rem;
      color: #6b7280;
      margin-bottom: 0.5rem;
      text-transform: uppercase;
    }
    .summary-card .value {
      font-size: 1.5rem;
      font-weight: 700;
      color: #1f2937;
    }
    .footer {
      margin-top: 3rem;
      padding-top: 1rem;
      border-top: 1px solid #e5e7eb;
      text-align: center;
      color: #6b7280;
      font-size: 0.875rem;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Unit Health Assessment Report</h1>
    
    <div style="margin-bottom: 1.5rem;">
      <p><strong>Generated:</strong> ${timestamp}</p>
      <p><strong>Unit:</strong> ${channelName || `Channel ${channelId}`}</p>
      <p><strong>Channel ID:</strong> ${channelId}</p>
      ${channelInfo ? `<p><strong>Device Type:</strong> ${channelInfo.deviceTypeName || 'N/A'}</p>` : ''}
      <p><strong>Date Range:</strong> ${startDate} - ${endDate}</p>
      <p><strong>Resolution:</strong> ${resolution} seconds (${resolution/60} minutes)</p>
    </div>

    <div class="health-status health-${healthStatus.status}">
      ${healthStatus.color} Equipment Health: ${healthStatus.status.toUpperCase()}<br>
      <small>${healthStatus.description}</small>
    </div>

    <h2>Executive Summary</h2>
    <div class="summary-cards">
      ${stats.energy ? `<div class="summary-card">
        <h4>Total Energy</h4>
        <div class="value">${stats.energy.sum.toFixed(2)} kWh</div>
      </div>` : ''}
      ${stats.power ? `<div class="summary-card">
        <h4>Average Power</h4>
        <div class="value">${stats.power.avg.toFixed(2)} kW</div>
      </div>` : ''}
      ${stats.power ? `<div class="summary-card">
        <h4>Peak Power</h4>
        <div class="value">${stats.power.max.toFixed(2)} kW</div>
      </div>` : ''}
      ${stats.voltage ? `<div class="summary-card">
        <h4>Avg Voltage</h4>
        <div class="value">${stats.voltage.avg.toFixed(1)} V</div>
      </div>` : ''}
      ${stats.powerFactor ? `<div class="summary-card">
        <h4>Power Factor</h4>
        <div class="value">${stats.powerFactor.avg.toFixed(3)}</div>
      </div>` : ''}
    </div>

    <h2>Power Consumption Over Time</h2>
    <div class="chart-container">
      <div class="chart-title">Power Consumption with Anomaly Markers</div>
      ${powerChart || '<p>Chart data not available</p>'}
      <p style="margin-top: 1rem; font-size: 0.875rem; color: #6b7280;">
        Red dots indicate detected anomalies. Power spikes and drops are highlighted.
      </p>
    </div>

    ${voltageChart ? `<h2>Voltage Stability</h2>
    <div class="chart-container">
      <div class="chart-title">Voltage Over Time</div>
      ${voltageChart}
      <p style="margin-top: 1rem; font-size: 0.875rem; color: #6b7280;">
        Green dashed line shows average voltage. Deviations indicate power quality issues.
      </p>
    </div>` : ''}

    ${pfChart ? `<h2>Power Factor Trends</h2>
    <div class="chart-container">
      <div class="chart-title">Power Factor Over Time</div>
      ${pfChart}
      <p style="margin-top: 1rem; font-size: 0.875rem; color: #6b7280;">
        Orange dashed line shows target (0.85). Values below indicate efficiency issues.
      </p>
    </div>` : ''}

    ${dailyPatternChart ? `<h2>Daily Operating Patterns</h2>
    <div class="chart-container">
      <div class="chart-title">Average Power by Hour of Day</div>
      ${dailyPatternChart}
      <p style="margin-top: 1rem; font-size: 0.875rem; color: #6b7280;">
        Shows typical operating patterns. Helps identify unusual operating hours.
      </p>
    </div>` : ''}

    <h2>Anomaly Detection Summary</h2>
    <table>
      <tr>
        <th>Severity</th>
        <th>Count</th>
      </tr>
      <tr>
        <td>🔴 Critical</td>
        <td>${anomalyAnalysis.summary.critical}</td>
      </tr>
      <tr>
        <td>🟠 High</td>
        <td>${anomalyAnalysis.summary.high}</td>
      </tr>
      <tr>
        <td>🟡 Medium</td>
        <td>${anomalyAnalysis.summary.medium}</td>
      </tr>
      <tr>
        <td>🔵 Low</td>
        <td>${anomalyAnalysis.summary.low}</td>
      </tr>
      <tr style="font-weight: 600;">
        <td>Total</td>
        <td>${anomalyAnalysis.summary.total}</td>
      </tr>
    </table>

    ${anomalyAnalysis.anomalies.length > 0 ? `<h2>Detected Anomalies</h2>
    <ul class="anomaly-list">
      ${anomalyAnalysis.anomalies.slice(0, 20).map((anomaly, idx) => `
        <li class="anomaly-item anomaly-${anomaly.severity}">
          <strong>${idx + 1}. ${anomaly.type.replace(/_/g, ' ').toUpperCase()} (${anomaly.severity.toUpperCase()})</strong><br>
          <small>Timestamp: ${formatDate(anomaly.timestamp)}</small><br>
          ${anomaly.description}
        </li>
      `).join('')}
      ${anomalyAnalysis.anomalies.length > 20 ? `<li style="padding: 1rem; color: #6b7280;">
        ... and ${anomalyAnalysis.anomalies.length - 20} more anomalies (see full report for details)
      </li>` : ''}
    </ul>` : '<h2>✅ No Anomalies Detected</h2><p>Equipment appears to be operating normally.</p>'}

    <h2>Recommendations</h2>
    <div class="recommendations">
      <ul>
        ${anomalyAnalysis.summary.critical > 0 ? '<li>🔴 <strong>CRITICAL:</strong> Immediate equipment inspection required. Schedule maintenance immediately.</li>' : ''}
        ${anomalyAnalysis.summary.high > 0 ? '<li>🟠 <strong>HIGH PRIORITY:</strong> Schedule maintenance check within 24-48 hours.</li>' : ''}
        ${anomalyAnalysis.anomalies.filter(a => a.type === 'power_factor_issue').length > 0 && stats.powerFactor && stats.powerFactor.avg < 0.85 ? '<li>💡 <strong>Power Factor Correction:</strong> Consider installing capacitor banks or upgrading motor controllers.</li>' : ''}
        ${anomalyAnalysis.anomalies.filter(a => a.type === 'voltage_anomaly').length > 0 ? '<li>⚡ <strong>Power Quality Review:</strong> Investigate voltage fluctuations. Check electrical supply.</li>' : ''}
        ${anomalyAnalysis.summary.total === 0 ? '<li>✅ <strong>No Action Required:</strong> Equipment is operating within normal parameters.</li>' : ''}
      </ul>
    </div>

    <div class="footer">
      <p>Report generated by Argo Energy Solutions Unit Health Assessment Tool</p>
      <p>${timestamp}</p>
    </div>
  </div>
</body>
</html>`;

  return html;
}

function generateJSONReport(channelId, channelName, channelInfo, readings, stats, anomalyAnalysis, healthStatus, dateRange, resolution, timestamp) {
  // Create a structured JSON report optimized for AI consumption
  const report = {
    metadata: {
      generatedAt: timestamp,
      reportType: 'Unit Health Assessment',
      unit: {
        channelId: channelId,
        channelName: channelName,
        deviceType: channelInfo?.deviceTypeName || null,
        organizationId: channelInfo?.organizationId || null,
      },
      analysisPeriod: {
        start: formatDate(dateRange.startTs),
        end: formatDate(dateRange.endTs),
        startTimestamp: dateRange.startTs,
        endTimestamp: dateRange.endTs,
        resolution: `${resolution} seconds (${resolution/60} minutes)`,
      },
    },
    equipmentHealth: {
      status: healthStatus.status,
      description: healthStatus.description,
      severity: healthStatus.status === 'critical' ? 5 :
                healthStatus.status === 'poor' ? 4 :
                healthStatus.status === 'fair' ? 3 :
                healthStatus.status === 'good' ? 2 : 1,
    },
    summary: {
      totalEnergyConsumption: stats.energy ? stats.energy.sum : null,
      averagePower: stats.power ? stats.power.avg : null,
      peakPower: stats.power ? stats.power.max : null,
      minimumPower: stats.power ? stats.power.min : null,
      averageVoltage: stats.voltage ? stats.voltage.avg : null,
      voltageStability: stats.voltage ? {
        average: stats.voltage.avg,
        min: stats.voltage.min,
        max: stats.voltage.max,
        range: stats.voltage.max - stats.voltage.min,
        stability: (stats.voltage.max - stats.voltage.min) < 3 ? 'stable' :
                   (stats.voltage.max - stats.voltage.min) < 6 ? 'moderate' : 'unstable',
      } : null,
      averagePowerFactor: stats.powerFactor ? stats.powerFactor.avg : null,
      powerFactorStatus: stats.powerFactor ? 
        (stats.powerFactor.avg >= 0.95 ? 'excellent' :
         stats.powerFactor.avg >= 0.85 ? 'acceptable' : 'poor') : null,
      dataPoints: readings.length,
    },
    anomalySummary: {
      total: anomalyAnalysis.summary.total,
      bySeverity: {
        critical: anomalyAnalysis.summary.critical,
        high: anomalyAnalysis.summary.high,
        medium: anomalyAnalysis.summary.medium,
        low: anomalyAnalysis.summary.low,
      },
      requiresImmediateAction: anomalyAnalysis.summary.critical > 0 || anomalyAnalysis.summary.high > 5,
    },
    anomalies: anomalyAnalysis.anomalies.map(a => ({
      type: a.type,
      severity: a.severity,
      timestamp: a.timestamp,
      formattedTimestamp: formatDate(a.timestamp),
      value: a.value,
      expectedValue: a.expectedValue,
      description: a.description,
      recommendation: a.recommendation || null,
    })),
    statistics: {
      power: stats.power ? {
        average: stats.power.avg,
        median: stats.power.median,
        peak: stats.power.max,
        minimum: stats.power.min,
        standardDeviation: stats.power.stdDev,
      } : null,
      energy: stats.energy ? {
        total: stats.energy.sum,
        averagePerReading: stats.energy.avg,
      } : null,
      voltage: stats.voltage ? {
        average: stats.voltage.avg,
        median: stats.voltage.median,
        min: stats.voltage.min,
        max: stats.voltage.max,
        standardDeviation: stats.voltage.stdDev,
      } : null,
      powerFactor: stats.powerFactor ? {
        average: stats.powerFactor.avg,
        median: stats.powerFactor.median,
        min: stats.powerFactor.min,
        max: stats.powerFactor.max,
      } : null,
    },
    recommendations: {
      immediateActions: [],
      maintenanceItems: [],
      optimizationOpportunities: [],
      generalNotes: [],
    },
  };

  // Categorize recommendations
  if (anomalyAnalysis.summary.critical > 0) {
    report.recommendations.immediateActions.push({
      priority: 'critical',
      action: 'Immediate equipment inspection required',
      reason: `${anomalyAnalysis.summary.critical} critical anomaly(ies) detected`,
    });
  }
  
  if (anomalyAnalysis.summary.high > 0) {
    report.recommendations.maintenanceItems.push({
      priority: 'high',
      action: 'Schedule maintenance check within 24-48 hours',
      reason: `${anomalyAnalysis.summary.high} high-priority anomaly(ies) detected`,
    });
  }
  
  const pfIssues = anomalyAnalysis.anomalies.filter(a => a.type === 'power_factor_issue').length;
  if (pfIssues > 0 && stats.powerFactor && stats.powerFactor.avg < 0.85) {
    report.recommendations.optimizationOpportunities.push({
      priority: 'medium',
      action: 'Consider power factor correction equipment',
      reason: `Average power factor is ${stats.powerFactor.avg.toFixed(3)} (target: >0.85)`,
      potentialSavings: 'Reduced reactive power penalties from utility',
    });
  }
  
  const voltageIssues = anomalyAnalysis.anomalies.filter(a => a.type === 'voltage_anomaly').length;
  if (voltageIssues > 0) {
    report.recommendations.maintenanceItems.push({
      priority: 'medium',
      action: 'Review power quality and electrical supply',
      reason: `${voltageIssues} voltage anomaly(ies) detected`,
    });
  }
  
  if (anomalyAnalysis.summary.total === 0) {
    report.recommendations.generalNotes.push({
      status: 'normal',
      message: 'Equipment is operating within normal parameters. No immediate action required.',
    });
  }

  // Add top anomalies for quick reference
  report.topAnomalies = anomalyAnalysis.anomalies
    .slice(0, 10)
    .map(a => ({
      type: a.type,
      severity: a.severity,
      timestamp: formatDate(a.timestamp),
      description: a.description,
    }));

  return report;
}

async function main() {
  const args = process.argv.slice(2);
  
  if (args.length < 3) {
    console.error('Usage: node scripts/unit-health-report.js <channelId> <startDate> <endDate> [resolution]');
    console.error('');
    console.error('Examples:');
    console.error('  node scripts/unit-health-report.js 162320 "2025-01-01" "2025-01-31" 3600');
    console.error('  node scripts/unit-health-report.js 162119 "2025-01-15" "2025-01-22" 900');
    console.error('  node scripts/unit-health-report.js 162320 yesterday today');
    console.error('');
    console.error('Date formats:');
    console.error('  - ISO dates: "2025-01-15", "2025-01-15T10:00:00"');
    console.error('  - Relative: "today", "yesterday", "last 7 days", "last 2 weeks"');
    console.error('');
    console.error('Resolution (seconds):');
    console.error('  60 = 1 minute, 900 = 15 minutes, 3600 = 1 hour (default), 86400 = 1 day');
    process.exit(1);
  }

  const channelId = args[0];
  // Handle dates that might have commas (remove them)
  const startDateStr = args[1].replace(/,/g, '').trim();
  const endDateStr = args[2].replace(/,/g, '').trim();
  const resolution = args[3] || '3600';
  
  // Check environment variables before proceeding
  console.log('\n🔍 Checking environment variables...');
  
  // Debug: Show what we're reading from process.env
  console.log('\n📋 Environment variable check:');
  console.log(`  VITE_ENISCOPE_API_KEY: ${process.env.VITE_ENISCOPE_API_KEY ? '✓ Set (' + process.env.VITE_ENISCOPE_API_KEY.substring(0, 8) + '...)' : '✗ Not found'}`);
  console.log(`  VITE_BEST_ENERGY_API_KEY: ${process.env.VITE_BEST_ENERGY_API_KEY ? '✓ Set (' + process.env.VITE_BEST_ENERGY_API_KEY.substring(0, 8) + '...)' : '✗ Not found'}`);
  console.log(`  ENISCOPE_API_KEY: ${process.env.ENISCOPE_API_KEY ? '✓ Set (' + process.env.ENISCOPE_API_KEY.substring(0, 8) + '...)' : '✗ Not found'}`);
  console.log(`  VITE_ENISCOPE_EMAIL: ${process.env.VITE_ENISCOPE_EMAIL ? '✓ Set' : '✗ Not found'}`);
  console.log(`  VITE_ENISCOPE_PASSWORD: ${process.env.VITE_ENISCOPE_PASSWORD ? '✓ Set' : '✗ Not found'}`);
  
  const missingVars = [];
  if (!ENISCOPE_API_KEY) {
    missingVars.push('VITE_ENISCOPE_API_KEY, VITE_BEST_ENERGY_API_KEY, or ENISCOPE_API_KEY');
  }
  if (!ENISCOPE_EMAIL) missingVars.push('VITE_ENISCOPE_EMAIL or ENISCOPE_EMAIL');
  if (!ENISCOPE_PASSWORD) missingVars.push('VITE_ENISCOPE_PASSWORD or ENISCOPE_PASSWORD');
  
  if (missingVars.length > 0) {
    console.error('\n❌ Missing required environment variables!');
    console.error('\nPlease add these to your .env file:');
    missingVars.forEach(v => console.error(`  - ${v}`));
    console.error('\nExample .env file:');
    console.error('  VITE_ENISCOPE_API_URL=https://core.eniscope.com');
    console.error('  VITE_ENISCOPE_API_KEY=your_api_key_here');
    console.error('  # OR use: VITE_BEST_ENERGY_API_KEY=your_api_key_here');
    console.error('  VITE_ENISCOPE_EMAIL=your_email@example.com');
    console.error('  VITE_ENISCOPE_PASSWORD=your_password_here');
    console.error(`\n.env file location: ${envPath}`);
    console.error(`\n.env file exists: ${fs.existsSync(envPath) ? '✓ Yes' : '✗ No'}`);
    
    // Check which API key variable is set
    const apiKeySource = process.env.VITE_ENISCOPE_API_KEY ? 'VITE_ENISCOPE_API_KEY' :
                        process.env.VITE_BEST_ENERGY_API_KEY ? 'VITE_BEST_ENERGY_API_KEY' :
                        process.env.ENISCOPE_API_KEY ? 'ENISCOPE_API_KEY' : null;
    
    if (ENISCOPE_API_KEY) {
      console.error(`\n  API_KEY: ✓ Set from ${apiKeySource} (${ENISCOPE_API_KEY.substring(0, 8)}...)`);
    } else {
      console.error(`\n  API_KEY: ✗ Missing`);
      console.error(`    Checked: VITE_ENISCOPE_API_KEY, VITE_BEST_ENERGY_API_KEY, ENISCOPE_API_KEY`);
      console.error(`\n💡 Tip: Make sure there are no spaces around the = sign in your .env file`);
      console.error(`   Correct: VITE_ENISCOPE_API_KEY=your_key`);
      console.error(`   Wrong:   VITE_ENISCOPE_API_KEY = your_key  (spaces will cause issues)`);
    }
    
    console.error(`  EMAIL: ${ENISCOPE_EMAIL ? '✓ Set' : '✗ Missing'}`);
    console.error(`  PASSWORD: ${ENISCOPE_PASSWORD ? '✓ Set' : '✗ Missing'}`);
    process.exit(1);
  }
  console.log('✅ Environment variables loaded\n');

  const channelName = CHANNEL_NAMES[channelId] || `Channel ${channelId}`;

  console.log('🏥 Unit Health Assessment Report Generator\n');
  console.log('='.repeat(60));
  console.log(`\n📊 Unit: ${channelName}`);
  console.log(`🆔 Channel ID: ${channelId}`);
  console.log(`📅 Date Range: ${startDateStr} to ${endDateStr}`);
  console.log(`⏱️  Resolution: ${resolution} seconds (${resolution/60} minutes)\n`);

  try {
    const startDate = parseDate(startDateStr);
    const endDate = parseDate(endDateStr);
    
    if (endDate < startDate) {
      throw new Error('End date must be after start date');
    }

    const startTs = Math.floor(startDate.getTime() / 1000);
    const endTs = Math.floor(endDate.getTime() / 1000);

    const client = new EniscopeAPIClient();

    // Authenticate (with initial delay to avoid rate limits)
    console.log('🔐 Authenticating...');
    // Small delay to avoid hitting rate limits if script was just run
    await new Promise(resolve => setTimeout(resolve, 500));
    await client.authenticate();
    console.log('✅ Authentication successful\n');

    // Get channel info
    console.log('📋 Fetching channel information...');
    const channelInfo = await client.getChannelInfo(channelId);
    if (channelInfo) {
      console.log(`✅ Channel found: ${channelInfo.channelName || channelName}\n`);
    }

    // Get readings
    console.log('📊 Fetching readings...');
    const readings = await client.getReadings(channelId, {
      fields: ['E', 'P', 'V', 'I', 'PF'],
      daterange: [startTs.toString(), endTs.toString()],
      res: resolution,
      action: 'summarize',
    });

    const readingList = readings.records || readings.data || readings.result || readings;
    
    if (!readingList || readingList.length === 0) {
      console.error('❌ No data available for the selected time period.');
      console.error('   Try a different date range or check that the unit is actively collecting data.');
      process.exit(1);
    }

    console.log(`✅ Collected ${readingList.length.toLocaleString()} readings\n`);

    // Calculate statistics
    console.log('📈 Calculating statistics...');
    const energyValues = readingList.map(r => r.E).filter(v => v != null && !isNaN(v)).map(v => v / 1000);
    const powerValues = readingList.map(r => r.P || r.kW).filter(v => v != null && !isNaN(v)).map(v => v / 1000);
    const voltageValues = readingList.map(r => r.V).filter(v => v != null && !isNaN(v));
    const currentValues = readingList.map(r => r.I).filter(v => v != null && !isNaN(v));
    const pfValues = readingList.map(r => r.PF).filter(v => v != null && !isNaN(v));

    const stats = {
      energy: calculateStats(energyValues),
      power: calculateStats(powerValues),
      voltage: voltageValues.length > 0 ? calculateStats(voltageValues) : null,
      current: currentValues.length > 0 ? calculateStats(currentValues) : null,
      powerFactor: pfValues.length > 0 ? calculateStats(pfValues) : null,
    };

    console.log('✅ Statistics calculated\n');

    // Detect anomalies
    console.log('🔍 Analyzing for anomalies...');
    const anomalyAnalysis = detectAnomalies(readingList);
    console.log(`✅ Found ${anomalyAnalysis.summary.total} anomalies\n`);

    // Determine health status
    const healthStatus = determineHealthStatus(anomalyAnalysis.summary, stats);

    // Generate reports (Markdown, HTML, and JSON)
    console.log('📝 Generating reports...');
    
    const dataDir = path.join(__dirname, '..', 'data');
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    
    // Generate Markdown report
    const mdReport = generateReport(
      channelId,
      channelName,
      channelInfo,
      readingList,
      stats,
      anomalyAnalysis,
      healthStatus,
      { startTs, endTs },
      resolution,
      false
    );
    const mdFilename = `unit-health-${channelId}-${timestamp}.md`;
    const mdFilepath = path.join(dataDir, mdFilename);
    fs.writeFileSync(mdFilepath, mdReport);
    console.log(`✅ Markdown report saved: ${mdFilepath}`);
    
    // Generate HTML report with charts
    const htmlReport = generateReport(
      channelId,
      channelName,
      channelInfo,
      readingList,
      stats,
      anomalyAnalysis,
      healthStatus,
      { startTs, endTs },
      resolution,
      true
    );
    const htmlFilename = `unit-health-${channelId}-${timestamp}.html`;
    const htmlFilepath = path.join(dataDir, htmlFilename);
    fs.writeFileSync(htmlFilepath, htmlReport);
    console.log(`✅ HTML report with charts saved: ${htmlFilepath}`);
    
    // Generate JSON report (AI-friendly format)
    const jsonReport = generateJSONReport(
      channelId,
      channelName,
      channelInfo,
      readingList,
      stats,
      anomalyAnalysis,
      healthStatus,
      { startTs, endTs },
      resolution,
      timestamp
    );
    const jsonFilename = `unit-health-${channelId}-${timestamp}.json`;
    const jsonFilepath = path.join(dataDir, jsonFilename);
    fs.writeFileSync(jsonFilepath, JSON.stringify(jsonReport, null, 2));
    console.log(`✅ JSON report (AI-friendly) saved: ${jsonFilepath}\n`);

    // Print summary
    console.log('='.repeat(60));
    console.log('\n📋 Report Summary\n');
    console.log(`Equipment Health: ${healthStatus.color} ${healthStatus.status.toUpperCase()}`);
    console.log(`Total Anomalies: ${anomalyAnalysis.summary.total}`);
    console.log(`  - Critical: ${anomalyAnalysis.summary.critical}`);
    console.log(`  - High: ${anomalyAnalysis.summary.high}`);
    console.log(`  - Medium: ${anomalyAnalysis.summary.medium}`);
    console.log(`  - Low: ${anomalyAnalysis.summary.low}`);
    
    if (stats.energy) {
      console.log(`\nTotal Energy: ${stats.energy.sum.toFixed(2)} kWh`);
    }
    if (stats.power) {
      console.log(`Average Power: ${stats.power.avg.toFixed(2)} kW`);
      console.log(`Peak Power: ${stats.power.max.toFixed(2)} kW`);
    }
    
    console.log(`\n📄 Reports generated:`);
    console.log(`   - Markdown: ${mdFilepath}`);
    console.log(`   - HTML (with charts): ${htmlFilepath}`);
    console.log(`   - JSON (AI-friendly): ${jsonFilepath}`);
    console.log(`\n💡 Tips:`);
    console.log(`   - Open HTML file in browser to view charts`);
    console.log(`   - Upload JSON file to Gemini for AI analysis`);
    console.log(`   - Markdown file works great with Gemini too!\n`);

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
