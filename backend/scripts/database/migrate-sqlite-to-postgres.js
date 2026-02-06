#!/usr/bin/env node

/**
 * Migrate Data from SQLite to PostgreSQL (Neon)
 * 
 * Transfers all data from local SQLite database to cloud PostgreSQL
 */

import pg from 'pg';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.join(__dirname, '..', '..', '..', '.env') });

const { Pool } = pg;

const BATCH_SIZE = 1000; // Insert readings in batches

async function openSqliteDb() {
  const dbPath = process.env.SQLITE_DB_PATH || './backend/data/eniscope.db';
  const fullPath = path.resolve(process.cwd(), dbPath);
  
  console.log(`📂 Opening SQLite database: ${fullPath}`);
  
  return open({
    filename: fullPath,
    driver: sqlite3.Database
  });
}

async function migrateTable(sqliteDb, pgPool, tableName, keyColumn = 'id') {
  console.log(`\n📊 Migrating ${tableName}...`);
  
  // Get row count from SQLite
  const countResult = await sqliteDb.get(`SELECT COUNT(*) as count FROM ${tableName}`);
  const totalRows = countResult.count;
  
  if (totalRows === 0) {
    console.log(`   ⚠️  No data in ${tableName}, skipping`);
    return;
  }
  
  console.log(`   Found ${totalRows.toLocaleString()} rows`);
  
  // Check if data already exists in PostgreSQL
  const pgCountResult = await pgPool.query(`SELECT COUNT(*) as count FROM ${tableName}`);
  const existingRows = parseInt(pgCountResult.rows[0].count);
  
  if (existingRows > 0) {
    console.log(`   ℹ️  PostgreSQL already has ${existingRows.toLocaleString()} rows`);
    const readline = await import('readline');
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
    
    const answer = await new Promise(resolve => {
      rl.question('   Overwrite existing data? (yes/no): ', resolve);
    });
    rl.close();
    
    if (answer.toLowerCase() !== 'yes') {
      console.log('   ⏭️  Skipping');
      return;
    }
    
    // Delete existing data
    console.log('   🗑️  Deleting existing data...');
    await pgPool.query(`DELETE FROM ${tableName}`);
  }
  
  // Get all rows from SQLite
  const rows = await sqliteDb.all(`SELECT * FROM ${tableName}`);
  
  if (rows.length === 0) {
    return;
  }
  
  // Get column names from first row
  const columns = Object.keys(rows[0]);
  const columnsList = columns.join(', ');
  const placeholders = columns.map((_, i) => `$${i + 1}`).join(', ');
  
  // Insert data in batches
  let inserted = 0;
  const totalBatches = Math.ceil(rows.length / BATCH_SIZE);
  
  for (let batchNum = 0; batchNum < totalBatches; batchNum++) {
    const start = batchNum * BATCH_SIZE;
    const end = Math.min(start + BATCH_SIZE, rows.length);
    const batch = rows.slice(start, end);
    
    // Build batch insert query
    const valuesList = batch.map((_, i) => {
      const offset = i * columns.length;
      return `(${columns.map((_, j) => `$${offset + j + 1}`).join(', ')})`;
    }).join(', ');
    
    const values = batch.flatMap(row => columns.map(col => row[col]));
    
    await pgPool.query(
      `INSERT INTO ${tableName} (${columnsList}) VALUES ${valuesList}
       ON CONFLICT DO NOTHING`,
      values
    );
    
    inserted += batch.length;
    const progress = ((inserted / rows.length) * 100).toFixed(1);
    process.stdout.write(`\r   Progress: ${progress}% (${inserted.toLocaleString()}/${rows.length.toLocaleString()})`);
  }
  
  console.log(`\n   ✅ Migrated ${inserted.toLocaleString()} rows`);
  
  // Verify counts match
  const verifyResult = await pgPool.query(`SELECT COUNT(*) as count FROM ${tableName}`);
  const finalCount = parseInt(verifyResult.rows[0].count);
  
  if (finalCount >= totalRows) {
    console.log(`   ✅ Verification passed (${finalCount.toLocaleString()} rows in PostgreSQL)`);
  } else {
    console.log(`   ⚠️  Warning: Expected ${totalRows}, got ${finalCount}`);
  }
}

async function migrate() {
  console.log('🔄 Starting SQLite to PostgreSQL migration\n');
  
  // Check environment
  if (!process.env.DATABASE_URL) {
    console.error('❌ DATABASE_URL not found in environment variables');
    process.exit(1);
  }
  
  let sqliteDb;
  let pgPool;
  
  try {
    // Connect to SQLite
    sqliteDb = await openSqliteDb();
    console.log('✅ Connected to SQLite\n');
    
    // Connect to PostgreSQL
    pgPool = new Pool({
      connectionString: process.env.DATABASE_URL,
      ssl: { rejectUnauthorized: false },
      max: 20
    });
    
    await pgPool.query('SELECT NOW()');
    console.log('✅ Connected to PostgreSQL\n');
    
    // Start migration
    const startTime = Date.now();
    
    // Migrate in order (respecting foreign keys)
    await migrateTable(sqliteDb, pgPool, 'organizations', 'organization_id');
    await migrateTable(sqliteDb, pgPool, 'devices', 'device_id');
    await migrateTable(sqliteDb, pgPool, 'channels', 'channel_id');
    await migrateTable(sqliteDb, pgPool, 'readings', 'id');
    
    const duration = ((Date.now() - startTime) / 1000).toFixed(1);
    
    console.log(`\n✅ Migration complete in ${duration} seconds!\n`);
    
    // Final summary
    console.log('📊 Final row counts:');
    const tables = ['organizations', 'devices', 'channels', 'readings'];
    
    for (const table of tables) {
      const result = await pgPool.query(`SELECT COUNT(*) as count FROM ${table}`);
      const count = parseInt(result.rows[0].count);
      console.log(`   ${table}: ${count.toLocaleString()}`);
    }
    
    console.log('\n💡 Next steps:');
    console.log('   1. Verify data: npm run db:check -- --db postgres');
    console.log('   2. Test report: npm run report:weekly -- --site 23271 --db postgres');
    console.log('   3. Set up daily sync: Update cron job to use --db postgres\n');
    
  } catch (error) {
    console.error('\n❌ Migration failed:');
    console.error(`   ${error.message}`);
    console.error(error.stack);
    process.exit(1);
  } finally {
    if (sqliteDb) {
      await sqliteDb.close();
    }
    if (pgPool) {
      await pgPool.end();
    }
  }
}

migrate();
