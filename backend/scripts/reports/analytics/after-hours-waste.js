/**
 * After-Hours Energy Waste Analytics
 * 
 * Identifies energy consumption during non-business hours that exceeds
 * the expected baseline, indicating potential waste or optimization opportunities.
 */

import { nonZeroPercentile, calculateStats } from '../lib/stats-utils.js';
import { parseTimestamp, getIntervalHours } from '../lib/date-utils.js';
import { isBusinessHours } from '../config/report-config.js';

/**
 * Calculate after-hours waste for a channel
 */
export function calculateAfterHoursWaste(channelData, baselineData, config, intervalSeconds) {
  const { baselinePercentile, minPowerThreshold, minExcessKwh } = config.afterHours;
  const intervalHours = getIntervalHours(intervalSeconds);
  
  // 1. Calculate baseline after-hours power (5th percentile of after-hours periods)
  const baselineAfterHoursPower = baselineData
    .filter(reading => !isBusinessHours(parseTimestamp(reading.ts), config))
    .map(reading => reading.P || reading.power_kw || 0)
    .filter(p => p > minPowerThreshold);
  
  const baselineKw = nonZeroPercentile(baselineAfterHoursPower, baselinePercentile);
  
  // 2. Calculate this week's after-hours consumption
  const reportAfterHoursReadings = channelData.readings
    .filter(reading => !isBusinessHours(parseTimestamp(reading.ts), config))
    .map(reading => ({
      ts: reading.ts,
      power: reading.P || reading.power_kw || 0,
    }));
  
  let totalAfterHoursKwh = 0;
  let excessAfterHoursKwh = 0;
  const excessIntervals = [];
  
  for (const reading of reportAfterHoursReadings) {
    const kwh = reading.power * intervalHours;
    totalAfterHoursKwh += kwh;
    
    const excess = Math.max(0, reading.power - baselineKw);
    const excessKwh = excess * intervalHours;
    excessAfterHoursKwh += excessKwh;
    
    if (excess > minPowerThreshold) {
      excessIntervals.push({
        ts: reading.ts,
        power: reading.power,
        baselinePower: baselineKw,
        excessKw: excess,
        excessKwh,
      });
    }
  }
  
  // 3. Calculate statistics
  const afterHoursPowers = reportAfterHoursReadings.map(r => r.power);
  const stats = calculateStats(afterHoursPowers);
  
  return {
    channelId: channelData.channelId,
    channelName: channelData.channelName,
    baseline: {
      kw: parseFloat(baselineKw.toFixed(2)),
      source: `${baselinePercentile}th percentile of after-hours baseline`,
    },
    thisWeek: {
      totalAfterHoursKwh: parseFloat(totalAfterHoursKwh.toFixed(2)),
      excessAfterHoursKwh: parseFloat(excessAfterHoursKwh.toFixed(2)),
      avgPowerKw: parseFloat(stats.mean.toFixed(2)),
      maxPowerKw: parseFloat(stats.max.toFixed(2)),
      minPowerKw: parseFloat(stats.min.toFixed(2)),
      intervals: reportAfterHoursReadings.length,
    },
    impact: {
      excessKwh: parseFloat(excessAfterHoursKwh.toFixed(2)),
      excessCost: parseFloat((excessAfterHoursKwh * config.tariff.defaultRate).toFixed(2)),
      percentOfTotal: totalAfterHoursKwh > 0 
        ? parseFloat((excessAfterHoursKwh / totalAfterHoursKwh * 100).toFixed(1))
        : 0,
    },
    excessIntervals: excessIntervals.slice(0, 10), // Top 10 for details
    isSignificant: excessAfterHoursKwh >= minExcessKwh,
  };
}

/**
 * Analyze after-hours waste for all channels
 */
export function analyzeAfterHoursWaste(channelsData, baselinesData, config, intervalSeconds) {
  const results = [];
  
  for (const channelData of channelsData) {
    const baselineData = baselinesData.find(b => b.channelId === channelData.channelId);
    
    if (!baselineData || baselineData.readings.length === 0) {
      console.warn(`No baseline data for channel ${channelData.channelId}, skipping after-hours analysis`);
      continue;
    }
    
    const result = calculateAfterHoursWaste(channelData, baselineData.readings, config, intervalSeconds);
    
    if (result.isSignificant) {
      results.push(result);
    }
  }
  
  // Sort by excess kWh (highest first)
  results.sort((a, b) => b.impact.excessKwh - a.impact.excessKwh);
  
  // Calculate totals
  const totalExcessKwh = results.reduce((sum, r) => sum + r.impact.excessKwh, 0);
  const totalExcessCost = results.reduce((sum, r) => sum + r.impact.excessCost, 0);
  
  return {
    topMeters: results.slice(0, 10), // Top 10 contributors
    allMeters: results,
    summary: {
      totalMetersWithExcess: results.length,
      totalExcessKwh: parseFloat(totalExcessKwh.toFixed(2)),
      totalExcessCost: parseFloat(totalExcessCost.toFixed(2)),
      estimatedAnnualCost: parseFloat((totalExcessCost * 52).toFixed(2)),
    },
    charts: {
      topContributorsChart: results.slice(0, 10).map(r => ({
        name: r.channelName,
        excessKwh: r.impact.excessKwh,
        cost: r.impact.excessCost,
      })),
      afterHoursProfile: generateAfterHoursProfile(results),
    },
  };
}

/**
 * Generate after-hours load profile by hour of day
 */
function generateAfterHoursProfile(results) {
  const profile = [];
  
  // Aggregate by hour (simplified - would need actual timestamp grouping for real implementation)
  for (let hour = 0; hour < 24; hour++) {
    const totalKw = results.reduce((sum, r) => sum + (r.thisWeek.avgPowerKw || 0), 0);
    
    profile.push({
      hour,
      avgPowerKw: parseFloat((totalKw / Math.max(1, results.length)).toFixed(2)),
    });
  }
  
  return profile;
}
