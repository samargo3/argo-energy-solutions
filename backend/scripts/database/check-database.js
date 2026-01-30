#!/usr/bin/env node

/**
 * Database Status Check Script
 * 
 * Checks the status of the SQLite database and shows statistics
 * 
 * Usage:
 *   node scripts/check-database.js
 */

import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { existsSync, statSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const DB_PATH = join(__dirname, '../data/eniscope.db');

async function checkDatabase() {
  console.log('🔍 Checking database status...\n');

  // Check if database exists
  if (!existsSync(DB_PATH)) {
    console.log('❌ Database file not found at:', DB_PATH);
    console.log('💡 Run "npm run ingest:data" to create the database\n');
    return;
  }

  // Get file size
  const stats = statSync(DB_PATH);
  const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
  console.log(`✅ Database file found: ${DB_PATH}`);
  console.log(`   Size: ${fileSizeMB} MB\n`);

  try {
    // Open database
    const db = await open({
      filename: DB_PATH,
      driver: sqlite3.Database,
    });

    console.log('📊 Database Statistics:\n');

    // Check tables
    const tables = await db.all(`
      SELECT name FROM sqlite_master 
      WHERE type='table' AND name NOT LIKE 'sqlite_%'
      ORDER BY name
    `);

    console.log(`Tables found: ${tables.length}`);
    for (const table of tables) {
      const count = await db.get(`SELECT COUNT(*) as count FROM ${table.name}`);
      console.log(`  - ${table.name}: ${count.count} records`);
    }

    console.log('');

    // Get detailed statistics
    if (tables.some(t => t.name === 'organizations')) {
      const orgCount = await db.get('SELECT COUNT(*) as count FROM organizations');
      console.log(`📁 Organizations: ${orgCount.count}`);
    }

    if (tables.some(t => t.name === 'devices')) {
      const deviceCount = await db.get('SELECT COUNT(*) as count FROM devices');
      console.log(`📱 Devices: ${deviceCount.count}`);
    }

    if (tables.some(t => t.name === 'channels')) {
      const channelCount = await db.get('SELECT COUNT(*) as count FROM channels');
      console.log(`📡 Channels: ${channelCount.count}`);
    }

    if (tables.some(t => t.name === 'readings')) {
      const readingCount = await db.get('SELECT COUNT(*) as count FROM readings');
      const dateRange = await db.get(`
        SELECT 
          MIN(timestamp) as earliest,
          MAX(timestamp) as latest
        FROM readings
      `);
      
      console.log(`📈 Readings: ${readingCount.count.toLocaleString()}`);
      
      if (dateRange.earliest && dateRange.latest) {
        console.log(`   Date Range: ${dateRange.earliest} to ${dateRange.latest}`);
        
        // Calculate days of data
        const days = Math.ceil(
          (new Date(dateRange.latest) - new Date(dateRange.earliest)) / (1000 * 60 * 60 * 24)
        );
        console.log(`   Days of data: ${days}`);
      }

      // Get readings per channel
      const channelStats = await db.all(`
        SELECT 
          channel_id,
          COUNT(*) as count,
          MIN(timestamp) as earliest,
          MAX(timestamp) as latest
        FROM readings
        GROUP BY channel_id
        ORDER BY count DESC
        LIMIT 10
      `);

      if (channelStats.length > 0) {
        console.log('\n📊 Top Channels by Reading Count:');
        for (const stat of channelStats) {
          console.log(`   Channel ${stat.channel_id}: ${stat.count.toLocaleString()} readings`);
        }
      }
    }

    // Check for recent data
    if (tables.some(t => t.name === 'readings')) {
      const recentCount = await db.get(`
        SELECT COUNT(*) as count 
        FROM readings 
        WHERE timestamp >= datetime('now', '-24 hours')
      `);
      
      console.log(`\n🕐 Recent data (last 24 hours): ${recentCount.count.toLocaleString()} readings`);
      
      if (recentCount.count === 0) {
        console.log('   ⚠️  No recent data found. Consider running: npm run ingest:incremental');
      }
    }

    // Check indexes
    const indexes = await db.all(`
      SELECT name FROM sqlite_master 
      WHERE type='index' AND name NOT LIKE 'sqlite_%'
    `);
    
    console.log(`\n🔍 Indexes: ${indexes.length}`);
    for (const idx of indexes) {
      console.log(`   - ${idx.name}`);
    }

    await db.close();
    
    console.log('\n✅ Database check complete!');
    
  } catch (error) {
    console.error('❌ Error checking database:', error.message);
    process.exit(1);
  }
}

checkDatabase();
