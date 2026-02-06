#!/usr/bin/env node
/**
 * Wilson Center – First readings from Eniscope/Best.Energy API
 *
 * Fetches the earliest available readings for each Wilson Center channel
 * from the Eniscope API (Best.Energy portal). Use this to confirm API
 * has data as early as April 29, 2025.
 *
 * Usage (from project root):
 *   node backend/scripts/data-collection/wilson-first-readings.js
 *
 * Requires .env with VITE_ENISCOPE_API_KEY, VITE_ENISCOPE_EMAIL, VITE_ENISCOPE_PASSWORD
 * (or VITE_BEST_ENERGY_* / ENISCOPE_* equivalents).
 */

import axios from 'axios';
import crypto from 'crypto';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.join(__dirname, '..', '..', '..', '.env') });

const ENISCOPE_API_URL = process.env.VITE_ENISCOPE_API_URL || process.env.VITE_BEST_ENERGY_API_URL || 'https://core.eniscope.com';
const ENISCOPE_API_KEY = process.env.VITE_ENISCOPE_API_KEY || process.env.VITE_BEST_ENERGY_API_KEY || '';
const ENISCOPE_EMAIL = process.env.VITE_ENISCOPE_EMAIL || '';
const ENISCOPE_PASSWORD = process.env.VITE_ENISCOPE_PASSWORD || '';

const WILSON_CENTER_CHANNELS = [
  { id: '162320', name: 'RTU-1_WCDS_Wilson Ctr' },
  { id: '162119', name: 'RTU-2_WCDS_Wilson Ctr' },
  { id: '162120', name: 'RTU-3_WCDS_Wilson Ctr' },
  { id: '162122', name: 'AHU-1A_WCDS_Wilson Ctr' },
  { id: '162123', name: 'AHU-1B_WCDS_Wilson Ctr' },
  { id: '162121', name: 'AHU-2_WCDS_Wilson Ctr' },
  { id: '162285', name: 'CDPK_Kitchen Main Panel(s)_WCDS_Wilson Ctr' },
  { id: '162319', name: 'CDKH_Kitchen Panel(small)_WCDS_Wilson Ctr' },
  { id: '162277', name: 'Air Sense_Main Kitchen_WCDS_Wilson' },
];

class EniscopeAPIClient {
  constructor() {
    this.sessionToken = null;
    this.apiKey = ENISCOPE_API_KEY;
    this.email = ENISCOPE_EMAIL;
    this.passwordMd5 = crypto.createHash('md5').update(ENISCOPE_PASSWORD || '').digest('hex');
    this.baseUrl = ENISCOPE_API_URL.replace(/\/$/, '');

    if (!this.apiKey || !this.email || !ENISCOPE_PASSWORD) {
      throw new Error(
        'Missing env: set VITE_ENISCOPE_API_KEY, VITE_ENISCOPE_EMAIL, VITE_ENISCOPE_PASSWORD (or VITE_BEST_ENERGY_* / ENISCOPE_*)'
      );
    }
  }

  async authenticate() {
    const authString = `${this.email}:${this.passwordMd5}`;
    const authB64 = Buffer.from(authString).toString('base64');

    const response = await axios.get(`${this.baseUrl}/organizations`, {
      headers: {
        Authorization: `Basic ${authB64}`,
        'X-Eniscope-API': this.apiKey,
        Accept: 'text/json',
      },
    });

    this.sessionToken =
      response.headers['x-eniscope-token'] || response.headers['X-Eniscope-Token'] || null;
    return true;
  }

  async getReadings(channelId, options = {}) {
    const params = {
      action: options.action || 'summarize',
      res: options.res || options.resolution || '900',
    };

    if (options.fields && Array.isArray(options.fields)) {
      params['fields[]'] = options.fields;
    }

    if (options.daterange) {
      if (Array.isArray(options.daterange)) {
        params['daterange[]'] = options.daterange;
      } else {
        params.daterange = options.daterange;
      }
    }

    const headers = {
      'X-Eniscope-API': this.apiKey,
      Accept: 'text/json',
    };
    if (this.sessionToken) {
      headers['X-Eniscope-Token'] = this.sessionToken;
    } else {
      const authString = `${this.email}:${this.passwordMd5}`;
      headers['Authorization'] = `Basic ${Buffer.from(authString).toString('base64')}`;
    }

    const maxRetries = 3;
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        const response = await axios.get(`${this.baseUrl}/readings/${channelId}`, {
          headers,
          params,
        });
        return response.data;
      } catch (err) {
        if (err.response?.status === 429 && attempt < maxRetries - 1) {
          const delay = (attempt + 1) * 2000;
          await new Promise((r) => setTimeout(r, delay));
          continue;
        }
        throw err;
      }
    }
  }
}

function toUnixSeconds(dateStr) {
  return Math.floor(new Date(dateStr).getTime() / 1000);
}

function formatTs(ts) {
  if (ts == null) return 'N/A';
  return new Date(parseInt(ts, 10) * 1000).toISOString();
}

async function main() {
  console.log('\n🏢 Wilson Center – First readings (Eniscope/Best.Energy API)\n');
  console.log('Date range: 2025-04-29 → 2025-05-15 (UTC)\n');

  const client = new EniscopeAPIClient();

  await client.authenticate();
  console.log('✓ Authenticated\n');

  const startTs = toUnixSeconds('2025-04-29T00:00:00Z');
  const endTs = toUnixSeconds('2025-05-15T23:59:59Z');

  const results = [];
  let overallFirstTs = null;
  let overallFirstChannel = null;

  for (const ch of WILSON_CENTER_CHANNELS) {
    try {
      const data = await client.getReadings(ch.id, {
        fields: ['E', 'P', 'V', 'I', 'PF', 'kW', 'kWh'],
        daterange: [startTs, endTs],
        res: '900',
        action: 'summarize',
      });

      const list = data.records || data.data || data.result || [];
      await new Promise((r) => setTimeout(r, 500));

      if (list.length === 0) {
        results.push({
          id: ch.id,
          name: ch.name,
          firstTs: null,
          firstIso: null,
          count: 0,
        });
        console.log(`   ${ch.name} (${ch.id}): no readings in range`);
        continue;
      }

      const timestamps = list.map((r) => r.ts ?? r.t ?? r.timestamp ?? r.time).filter((t) => t != null);
      const firstTs = timestamps.length ? Math.min(...timestamps.map((t) => parseInt(String(t), 10))) : null;

      if (firstTs != null && (overallFirstTs == null || firstTs < overallFirstTs)) {
        overallFirstTs = firstTs;
        overallFirstChannel = ch.name;
      }

      results.push({
        id: ch.id,
        name: ch.name,
        firstTs,
        firstIso: formatTs(firstTs),
        count: list.length,
      });

      console.log(`   ${ch.name} (${ch.id}): first ${formatTs(firstTs)} (${list.length} points)`);
    } catch (err) {
      const msg = err.response?.data ? JSON.stringify(err.response.data) : err.message;
      console.log(`   ${ch.name} (${ch.id}): error – ${msg}`);
      results.push({
        id: ch.id,
        name: ch.name,
        firstTs: null,
        firstIso: null,
        count: 0,
        error: msg,
      });
    }
  }

  console.log('\n' + '─'.repeat(60));
  if (overallFirstTs != null) {
    console.log(`\n📅 First reading (any Wilson Center channel): ${formatTs(overallFirstTs)}`);
    console.log(`   Channel: ${overallFirstChannel}`);
  } else {
    const withData = results.filter((r) => r.firstTs != null);
    if (withData.length === 0) {
      console.log('\n⚠️  No readings returned in range. Check API credentials and that Best.Energy has data for April 29 – May 15, 2025.');
    }
  }
  console.log('');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
