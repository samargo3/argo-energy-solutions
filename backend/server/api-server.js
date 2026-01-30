#!/usr/bin/env node

/**
 * Express API Server for SQLite Database Access
 * 
 * Provides REST API endpoints to access the SQLite database from the React app
 * 
 * Usage:
 *   node server/api-server.js
 * 
 * Or with nodemon for development:
 *   npx nodemon server/api-server.js
 */

import express from 'express';
import cors from 'cors';
import axios from 'axios';
import crypto from 'crypto';
import { dataQueryService } from '../src/services/data/queryService.js';

const app = express();
const PORT = process.env.API_PORT || 3001;

// Eniscope API configuration
const ENISCOPE_API_URL = process.env.VITE_ENISCOPE_API_URL || process.env.ENISCOPE_API_URL || 'https://core.eniscope.com';
const ENISCOPE_API_KEY = process.env.VITE_ENISCOPE_API_KEY || process.env.ENISCOPE_API_KEY || '';
const ENISCOPE_EMAIL = process.env.VITE_ENISCOPE_EMAIL || process.env.ENISCOPE_EMAIL || '';
const ENISCOPE_PASSWORD = process.env.VITE_ENISCOPE_PASSWORD || process.env.ENISCOPE_PASSWORD || '';

// Middleware
app.use(cors());
app.use(express.json());

// Eniscope API client helper
class EniscopeProxy {
  constructor() {
    this.sessionToken = null;
    this.apiKey = ENISCOPE_API_KEY;
    this.email = ENISCOPE_EMAIL;
    this.passwordMd5 = crypto.createHash('md5').update(ENISCOPE_PASSWORD).digest('hex');
    this.baseUrl = ENISCOPE_API_URL.replace(/\/$/, '');
  }

  async authenticate() {
    const authString = `${this.email}:${this.passwordMd5}`;
    const authB64 = Buffer.from(authString).toString('base64');

    try {
      const response = await axios.get(`${this.baseUrl}/v1/1/organizations`, {
        headers: {
          'Authorization': `Basic ${authB64}`,
          'X-Eniscope-API': this.apiKey,
          'Accept': 'text/json',
        },
      });

      this.sessionToken = response.headers['x-eniscope-token'] || response.headers['X-Eniscope-Token'] || null;
      return this.sessionToken;
    } catch (error) {
      console.error('Eniscope authentication failed:', error.response?.data || error.message);
      throw error;
    }
  }

  async makeRequest(endpoint, params = {}, retries = 3) {
    const headers = {
      'X-Eniscope-API': this.apiKey,
      'Accept': 'text/json',
    };

    if (!this.sessionToken) {
      await this.authenticate();
    }

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
        if (error.response?.status === 401 || error.response?.status === 419) {
          // Token expired, re-authenticate
          this.sessionToken = null;
          await this.authenticate();
          if (attempt < retries - 1) continue;
        }
        
        if (error.response?.status === 429 && attempt < retries - 1) {
          const delay = Math.pow(2, attempt) * 1000;
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
        
        throw error;
      }
    }
  }
}

const eniscopeProxy = new EniscopeProxy();

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Get channels
app.get('/api/channels', async (req, res) => {
  try {
    const organizationId = req.query.organizationId 
      ? parseInt(req.query.organizationId) 
      : undefined;
    
    await dataQueryService.initialize();
    const channels = await dataQueryService.getChannels(organizationId);
    res.json(channels);
  } catch (error) {
    console.error('Error fetching channels:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get channel readings
app.get('/api/channels/:channelId/readings', async (req, res) => {
  try {
    const channelId = parseInt(req.params.channelId);
    const { startDate, endDate, limit } = req.query;

    if (!startDate || !endDate) {
      return res.status(400).json({ 
        error: 'startDate and endDate query parameters are required' 
      });
    }

    await dataQueryService.initialize();
    const readings = await dataQueryService.getChannelReadings(
      channelId,
      startDate,
      endDate,
      limit ? parseInt(limit) : undefined
    );
    res.json(readings);
  } catch (error) {
    console.error('Error fetching readings:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get aggregated readings
app.get('/api/channels/:channelId/readings/aggregated', async (req, res) => {
  try {
    const channelId = parseInt(req.params.channelId);
    const { startDate, endDate, resolution = 'hour' } = req.query;

    if (!startDate || !endDate) {
      return res.status(400).json({ 
        error: 'startDate and endDate query parameters are required' 
      });
    }

    if (!['hour', 'day', 'week', 'month'].includes(resolution)) {
      return res.status(400).json({ 
        error: 'resolution must be one of: hour, day, week, month' 
      });
    }

    await dataQueryService.initialize();
    const readings = await dataQueryService.getAggregatedReadings(
      channelId,
      startDate,
      endDate,
      resolution
    );
    res.json(readings);
  } catch (error) {
    console.error('Error fetching aggregated readings:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get energy statistics
app.get('/api/channels/:channelId/statistics', async (req, res) => {
  try {
    const channelId = parseInt(req.params.channelId);
    const { startDate, endDate } = req.query;

    if (!startDate || !endDate) {
      return res.status(400).json({ 
        error: 'startDate and endDate query parameters are required' 
      });
    }

    await dataQueryService.initialize();
    const statistics = await dataQueryService.getEnergyStatistics(
      channelId,
      startDate,
      endDate
    );
    res.json(statistics);
  } catch (error) {
    console.error('Error fetching statistics:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get organization summary
app.get('/api/organizations/:organizationId/summary', async (req, res) => {
  try {
    const organizationId = parseInt(req.params.organizationId);
    const { startDate, endDate } = req.query;

    if (!startDate || !endDate) {
      return res.status(400).json({ 
        error: 'startDate and endDate query parameters are required' 
      });
    }

    await dataQueryService.initialize();
    const summary = await dataQueryService.getOrganizationSummary(
      organizationId,
      startDate,
      endDate
    );
    res.json(summary);
  } catch (error) {
    console.error('Error fetching organization summary:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get latest reading for a channel
app.get('/api/channels/:channelId/readings/latest', async (req, res) => {
  try {
    const channelId = parseInt(req.params.channelId);

    await dataQueryService.initialize();
    const reading = await dataQueryService.getLatestReading(channelId);
    res.json(reading);
  } catch (error) {
    console.error('Error fetching latest reading:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get data range for a channel
app.get('/api/channels/:channelId/range', async (req, res) => {
  try {
    const channelId = parseInt(req.params.channelId);

    await dataQueryService.initialize();
    const range = await dataQueryService.getDataRange(channelId);
    res.json(range);
  } catch (error) {
    console.error('Error fetching data range:', error);
    res.status(500).json({ error: error.message });
  }
});

// ===== ENISCOPE API PROXY ENDPOINTS =====

// Get Eniscope channel readings
app.get('/api/eniscope/readings/:channelId', async (req, res) => {
  try {
    const { channelId } = req.params;
    const { fields, daterange, res: resolution, action } = req.query;

    if (!channelId) {
      return res.status(400).json({ error: 'channelId is required' });
    }

    const params = {
      res: resolution || '3600',
      action: action || 'summarize',
      showCounters: '0',
    };

    // Handle fields array
    if (fields) {
      const fieldsArray = Array.isArray(fields) ? fields : [fields];
      fieldsArray.forEach((field) => {
        if (!params['fields[]']) params['fields[]'] = [];
        params['fields[]'].push(field);
      });
    } else {
      // Default fields
      params['fields[]'] = ['E', 'P', 'V', 'I', 'PF'];
    }

    // Handle daterange
    if (daterange) {
      if (Array.isArray(daterange)) {
        params['daterange[]'] = daterange;
      } else {
        params.daterange = daterange;
      }
    }

    const readings = await eniscopeProxy.makeRequest(`/v1/1/readings/${channelId}`, params);
    
    // Handle different response formats
    const readingList = readings.records || readings.data || readings.result || readings;
    res.json(readingList);
  } catch (error) {
    console.error('Error fetching Eniscope readings:', error.response?.data || error.message);
    res.status(error.response?.status || 500).json({ 
      error: error.message,
      details: error.response?.data 
    });
  }
});

// Get Eniscope channels
app.get('/api/eniscope/channels', async (req, res) => {
  try {
    const { organization, deviceId, name, page, limit } = req.query;
    
    const params = {};
    if (organization) params.organization = organization;
    if (deviceId) params.deviceId = deviceId;
    if (name) params.name = name;
    if (page) params.page = page;
    if (limit) params.limit = limit;

    const channels = await eniscopeProxy.makeRequest('/v1/1/channels', params);
    res.json(channels);
  } catch (error) {
    console.error('Error fetching Eniscope channels:', error.response?.data || error.message);
    res.status(error.response?.status || 500).json({ 
      error: error.message,
      details: error.response?.data 
    });
  }
});

// Get Eniscope devices
app.get('/api/eniscope/devices', async (req, res) => {
  try {
    const { organization, uuid, deviceType, name, page, limit } = req.query;
    
    const params = {};
    if (organization) params.organization = organization;
    if (uuid) params.uuid = uuid;
    if (deviceType) params.deviceType = deviceType;
    if (name) params.name = name;
    if (page) params.page = page;
    if (limit) params.limit = limit;

    const devices = await eniscopeProxy.makeRequest('/v1/1/devices', params);
    res.json(devices);
  } catch (error) {
    console.error('Error fetching Eniscope devices:', error.response?.data || error.message);
    res.status(error.response?.status || 500).json({ 
      error: error.message,
      details: error.response?.data 
    });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 API Server running on http://localhost:${PORT}`);
  console.log(`📊 Endpoints available:`);
  console.log(`   GET /health`);
  console.log(`   GET /api/channels`);
  console.log(`   GET /api/channels/:channelId/readings`);
  console.log(`   GET /api/channels/:channelId/readings/aggregated`);
  console.log(`   GET /api/channels/:channelId/statistics`);
  console.log(`   GET /api/organizations/:organizationId/summary`);
  console.log(`   GET /api/channels/:channelId/readings/latest`);
  console.log(`   GET /api/channels/:channelId/range`);
  console.log(`\n🔌 Eniscope API Proxy Endpoints:`);
  console.log(`   GET /api/eniscope/readings/:channelId`);
  console.log(`   GET /api/eniscope/channels`);
  console.log(`   GET /api/eniscope/devices`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, closing database connections...');
  await dataQueryService.close();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('SIGINT received, closing database connections...');
  await dataQueryService.close();
  process.exit(0);
});
