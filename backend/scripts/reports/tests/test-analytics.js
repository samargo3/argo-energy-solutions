/**
 * Unit Tests for Analytics Functions
 * 
 * Run with: node tests/test-analytics.js
 */

import assert from 'assert';
import {
  calculateStats,
  percentile,
  nonZeroPercentile,
  findGaps,
  calculateCompleteness,
  rollingVariance,
} from '../lib/stats-utils.js';

/**
 * Test runner
 */
function runTest(name, fn) {
  try {
    fn();
    console.log(`✓ ${name}`);
  } catch (error) {
    console.error(`✗ ${name}`);
    console.error(`  ${error.message}`);
    process.exitCode = 1;
  }
}

console.log('Running Analytics Unit Tests\n');
console.log('='.repeat(60));

// Test: calculateStats
runTest('calculateStats: basic statistics', () => {
  const values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
  const stats = calculateStats(values);
  
  assert.strictEqual(stats.count, 10);
  assert.strictEqual(stats.sum, 55);
  assert.strictEqual(stats.mean, 5.5);
  assert.strictEqual(stats.min, 1);
  assert.strictEqual(stats.max, 10);
  assert.strictEqual(stats.median, 5.5);
});

runTest('calculateStats: empty array', () => {
  const stats = calculateStats([]);
  assert.strictEqual(stats.count, 0);
  assert.strictEqual(stats.sum, 0);
});

// Test: percentile
runTest('percentile: 50th percentile (median)', () => {
  const values = [1, 2, 3, 4, 5];
  const p50 = percentile(values, 50);
  assert.strictEqual(p50, 3);
});

runTest('percentile: 95th percentile', () => {
  const values = Array.from({ length: 100 }, (_, i) => i + 1);
  const p95 = percentile(values, 95);
  assert.ok(p95 >= 95 && p95 <= 96);
});

// Test: nonZeroPercentile
runTest('nonZeroPercentile: excludes zeros', () => {
  const values = [0, 0, 0, 10, 20, 30, 40, 50];
  const p5 = nonZeroPercentile(values, 5);
  assert.ok(p5 > 0); // Should be close to 10, not 0
});

// Test: findGaps
runTest('findGaps: detects missing intervals', () => {
  const timestamps = [
    '2026-01-01T00:00:00Z',
    '2026-01-01T01:00:00Z',
    '2026-01-01T04:00:00Z', // 3-hour gap
    '2026-01-01T05:00:00Z',
  ];
  
  const gaps = findGaps(timestamps, 3600); // 1-hour intervals
  
  assert.strictEqual(gaps.length, 1);
  assert.strictEqual(gaps[0].missingIntervals, 2);
});

runTest('findGaps: no gaps when data is continuous', () => {
  const timestamps = [
    '2026-01-01T00:00:00Z',
    '2026-01-01T01:00:00Z',
    '2026-01-01T02:00:00Z',
  ];
  
  const gaps = findGaps(timestamps, 3600);
  assert.strictEqual(gaps.length, 0);
});

// Test: calculateCompleteness
runTest('calculateCompleteness: 100% complete', () => {
  const completeness = calculateCompleteness(100, 100);
  assert.strictEqual(completeness, 100);
});

runTest('calculateCompleteness: 50% complete', () => {
  const completeness = calculateCompleteness(50, 100);
  assert.strictEqual(completeness, 50);
});

// Test: rollingVariance
runTest('rollingVariance: detects flatline', () => {
  // Create data with constant values (flatline)
  const values = [10, 10, 10, 10, 10, 10, 10, 10];
  const rolling = rollingVariance(values, 4);
  
  assert.ok(rolling.length > 0);
  assert.ok(rolling[0].variance < 0.01); // Should be near-zero variance
});

runTest('rollingVariance: detects variance in changing data', () => {
  const values = [10, 20, 30, 40, 50, 60, 70, 80];
  const rolling = rollingVariance(values, 4);
  
  assert.ok(rolling.length > 0);
  assert.ok(rolling[0].variance > 1); // Should have significant variance
});

// Test: Baseline percentile logic
runTest('Baseline: 5th percentile for after-hours', () => {
  // Simulate after-hours power readings with some zeros and low values
  const afterHoursPowers = [0, 0, 0, 5, 10, 15, 20, 25, 30, 35];
  const baseline = nonZeroPercentile(afterHoursPowers, 5);
  
  assert.ok(baseline > 0); // Should exclude zeros
  assert.ok(baseline < 15); // Should be near the low end
});

// Test: Anomaly grouping (consecutive intervals)
runTest('Anomaly grouping: consecutive intervals', () => {
  const anomalies = [
    { ts: '2026-01-01T10:00:00Z', excessKwh: 5 },
    { ts: '2026-01-01T10:15:00Z', excessKwh: 6 },
    { ts: '2026-01-01T10:30:00Z', excessKwh: 7 },
    { ts: '2026-01-01T12:00:00Z', excessKwh: 8 }, // Gap
  ];
  
  // Simple grouping test
  let currentGroup = [anomalies[0]];
  for (let i = 1; i < anomalies.length; i++) {
    const prevTime = new Date(anomalies[i - 1].ts).getTime();
    const currTime = new Date(anomalies[i].ts).getTime();
    const gap = (currTime - prevTime) / 1000;
    
    if (gap < 3600) { // Within 1 hour
      currentGroup.push(anomalies[i]);
    } else {
      break;
    }
  }
  
  assert.strictEqual(currentGroup.length, 3); // First 3 should be grouped
});

console.log('='.repeat(60));
console.log('\nAll tests completed!');

if (process.exitCode === 1) {
  console.log('❌ Some tests failed\n');
} else {
  console.log('✅ All tests passed\n');
}
