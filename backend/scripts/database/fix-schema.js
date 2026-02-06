#!/usr/bin/env node

import pg from 'pg';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.join(__dirname, '..', '..', '..', '.env') });

const { Client } = pg;

async function fixSchema() {
  console.log('🔧 Fixing database schema...\n');

  const client = new Client({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false }
  });

  try {
    await client.connect();
    console.log('✅ Connected to database\n');

    // Make device_id nullable (channels can exist without devices for now)
    console.log('Making device_id nullable in channels table...');
    await client.query('ALTER TABLE channels ALTER COLUMN device_id DROP NOT NULL');
    console.log('✅ device_id is now nullable\n');

    // Drop the foreign key constraint temporarily
    console.log('Dropping foreign key constraint on device_id...');
    await client.query('ALTER TABLE channels DROP CONSTRAINT IF EXISTS channels_device_id_fkey');
    console.log('✅ Foreign key constraint removed\n');

    console.log('✅ Schema fixed! You can now run ingestion.\n');

  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  } finally {
    await client.end();
  }
}

fixSchema();
