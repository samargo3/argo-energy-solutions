#!/usr/bin/env node

/**
 * Test Neon PostgreSQL Connection
 * 
 * Quick script to verify your DATABASE_URL is configured correctly
 * and you can connect to Neon.
 */

import pg from 'pg';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables
dotenv.config({ path: path.join(__dirname, '..', '..', '..', '.env') });

const { Client } = pg;

async function testConnection() {
  console.log('🔌 Testing Neon PostgreSQL Connection...\n');

  // Check if DATABASE_URL is set
  if (!process.env.DATABASE_URL) {
    console.error('❌ DATABASE_URL not found in environment variables');
    console.error('   Add it to your .env file:');
    console.error('   DATABASE_URL=postgresql://user:pass@host/db\n');
    process.exit(1);
  }

  // Mask password in connection string for display
  const maskedUrl = process.env.DATABASE_URL.replace(
    /:(.*?)@/,
    ':****@'
  );
  console.log(`📡 Connecting to: ${maskedUrl}\n`);

  const client = new Client({
    connectionString: process.env.DATABASE_URL,
    ssl: {
      rejectUnauthorized: false // Neon requires SSL
    }
  });

  try {
    // Connect
    await client.connect();
    console.log('✅ Connected to Neon PostgreSQL!\n');

    // Get server info
    const timeResult = await client.query('SELECT NOW() as server_time');
    console.log(`⏰ Server time: ${timeResult.rows[0].server_time}`);

    const versionResult = await client.query('SELECT version()');
    const version = versionResult.rows[0].version;
    console.log(`🐘 PostgreSQL version: ${version.split(',')[0]}`);

    const dbResult = await client.query('SELECT current_database()');
    console.log(`📊 Database: ${dbResult.rows[0].current_database}`);

    // Check for TimescaleDB
    const tsResult = await client.query(`
      SELECT COUNT(*) as count 
      FROM pg_extension 
      WHERE extname = 'timescaledb'
    `);
    const hasTimescale = tsResult.rows[0].count > 0;
    
    if (hasTimescale) {
      console.log('⚡ TimescaleDB: Enabled ✨');
    } else {
      console.log('⚡ TimescaleDB: Not enabled (optional)');
    }

    // Check if tables exist
    const tablesResult = await client.query(`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public' 
      ORDER BY table_name
    `);

    if (tablesResult.rows.length > 0) {
      console.log('\n📋 Existing tables:');
      tablesResult.rows.forEach(row => {
        console.log(`   - ${row.table_name}`);
      });

      // Count data in each table
      console.log('\n📊 Row counts:');
      for (const row of tablesResult.rows) {
        const countResult = await client.query(
          `SELECT COUNT(*) as count FROM ${row.table_name}`
        );
        const count = parseInt(countResult.rows[0].count);
        console.log(`   - ${row.table_name}: ${count.toLocaleString()} rows`);
      }
    } else {
      console.log('\n📋 No tables found (run schema setup)');
    }

    console.log('\n✅ Connection test successful!\n');

  } catch (error) {
    console.error('\n❌ Connection failed:');
    console.error(`   ${error.message}\n`);
    
    if (error.message.includes('password authentication failed')) {
      console.error('💡 Check your DATABASE_URL credentials');
    } else if (error.message.includes('timeout')) {
      console.error('💡 Check your network connection');
    } else if (error.message.includes('SSL')) {
      console.error('💡 Neon requires SSL - make sure ssl: true in config');
    }
    
    process.exit(1);
  } finally {
    await client.end();
  }
}

testConnection();
