#!/usr/bin/env node

/**
 * Setup PostgreSQL Schema for Argo Energy Solutions
 * 
 * Creates all necessary tables and indexes for storing Eniscope energy data
 */

import pg from 'pg';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.join(__dirname, '..', '..', '..', '.env') });

const { Client } = pg;

const SCHEMA_SQL = `
-- Organizations (Sites/Customers)
CREATE TABLE IF NOT EXISTS organizations (
  organization_id TEXT PRIMARY KEY,
  organization_name TEXT NOT NULL,
  address TEXT,
  city TEXT,
  postcode TEXT,
  country TEXT,
  timezone TEXT DEFAULT 'America/New_York',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Devices (Gateway units)
CREATE TABLE IF NOT EXISTS devices (
  device_id INTEGER PRIMARY KEY,
  device_name TEXT,
  organization_id TEXT REFERENCES organizations(organization_id),
  device_type TEXT,
  serial_number TEXT,
  firmware_version TEXT,
  last_seen TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Channels (Meters/Monitoring Points)
CREATE TABLE IF NOT EXISTS channels (
  channel_id INTEGER PRIMARY KEY,
  channel_name TEXT NOT NULL,
  device_id INTEGER REFERENCES devices(device_id),
  organization_id TEXT REFERENCES organizations(organization_id),
  channel_type TEXT,
  unit TEXT,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Readings (Time-Series Data) - This will be the largest table
CREATE TABLE IF NOT EXISTS readings (
  id BIGSERIAL PRIMARY KEY,
  channel_id INTEGER NOT NULL REFERENCES channels(channel_id),
  timestamp TIMESTAMP NOT NULL,
  energy_kwh REAL,
  power_kw REAL,
  voltage_v REAL,
  current_a REAL,
  power_factor REAL,
  reactive_power_kvar REAL,
  temperature_c REAL,
  relative_humidity REAL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_readings_channel_timestamp 
  ON readings(channel_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_readings_timestamp 
  ON readings(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_channels_org 
  ON channels(organization_id);

CREATE INDEX IF NOT EXISTS idx_devices_org 
  ON devices(organization_id);

-- Unique constraint to prevent duplicate readings
CREATE UNIQUE INDEX IF NOT EXISTS idx_readings_unique 
  ON readings(channel_id, timestamp);

-- Metadata table for tracking data freshness
CREATE TABLE IF NOT EXISTS data_sync_status (
  id SERIAL PRIMARY KEY,
  organization_id TEXT NOT NULL,
  channel_id INTEGER,
  last_sync_timestamp TIMESTAMP NOT NULL,
  last_reading_timestamp TIMESTAMP,
  readings_count INTEGER,
  sync_status TEXT, -- 'success', 'partial', 'failed'
  error_message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sync_status_org 
  ON data_sync_status(organization_id, last_sync_timestamp DESC);
`;

async function setupSchema() {
  console.log('🗄️  Setting up PostgreSQL schema for Argo Energy Solutions...\n');

  if (!process.env.DATABASE_URL) {
    console.error('❌ DATABASE_URL not found in environment variables');
    process.exit(1);
  }

  const client = new Client({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false }
  });

  try {
    await client.connect();
    console.log('✅ Connected to database\n');

    // Execute schema
    console.log('📋 Creating tables...');
    await client.query(SCHEMA_SQL);
    console.log('✅ Tables created successfully\n');

    // Verify tables
    const tablesResult = await client.query(`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public' 
      ORDER BY table_name
    `);

    console.log('📊 Tables created:');
    tablesResult.rows.forEach(row => {
      console.log(`   ✓ ${row.table_name}`);
    });

    // Verify indexes
    const indexesResult = await client.query(`
      SELECT indexname 
      FROM pg_indexes 
      WHERE schemaname = 'public' 
        AND indexname LIKE 'idx_%'
      ORDER BY indexname
    `);

    console.log('\n🔍 Indexes created:');
    indexesResult.rows.forEach(row => {
      console.log(`   ✓ ${row.indexname}`);
    });

    console.log('\n✅ Schema setup complete!\n');
    console.log('💡 Next steps:');
    console.log('   1. Run: npm run ingest:full -- --db postgres --days 90');
    console.log('   2. Or migrate from SQLite: npm run db:migrate:sqlite-to-postgres\n');

  } catch (error) {
    console.error('\n❌ Schema setup failed:');
    console.error(`   ${error.message}\n`);
    process.exit(1);
  } finally {
    await client.end();
  }
}

setupSchema();
