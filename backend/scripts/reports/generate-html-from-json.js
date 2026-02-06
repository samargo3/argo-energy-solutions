#!/usr/bin/env node
/**
 * Generate HTML report from existing JSON
 * Quick utility to convert JSON reports to customer-ready HTML
 */

import fs from 'fs';
import { saveHTMLReport } from './lib/report-renderer.js';

const args = process.argv.slice(2);
const jsonPath = args[0];

if (!jsonPath) {
  console.log('Usage: node generate-html-from-json.js <json-file>');
  console.log('Example: node generate-html-from-json.js data/weekly-brief-23271-corrected.json');
  process.exit(1);
}

if (!fs.existsSync(jsonPath)) {
  console.error(`Error: File not found: ${jsonPath}`);
  process.exit(1);
}

console.log(`Reading JSON report: ${jsonPath}`);
const reportData = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));

const htmlPath = jsonPath.replace('.json', '.html');
saveHTMLReport(reportData, htmlPath);

console.log(`✅ HTML report generated: ${htmlPath}`);
console.log(`\n💡 Open this file in your browser to view the professional report`);
