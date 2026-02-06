/**
 * Anomaly Detection Analytics
 * 
 * Detects anomalous energy consumption patterns by comparing
 * current week's data against historical baseline.
 */

import { calculateStats, calculateIQR, zScore, groupBy } from '../lib/stats-utils.js';
import { parseTimestamp, getHourOfWeek, getDayAndHour, getIntervalHours } from '../lib/date-utils.js';
import { isBusinessHours } from '../config/report-config.js';

/**
 * Build baseline profile by hour-of-week
 */
function buildBaselineProfile(baselineReadings, config) {
  // Group by hour of week (0-167)
  const grouped = groupBy(baselineReadings, reading => {
    const ts = parseTimestamp(reading.ts);
    return getHourOfWeek(ts);
  });
  
  const profile = {};
  
  for (const [hourOfWeek, readings] of Object.entries(grouped)) {
    const powers = readings
      .map(r => r.P || r.power_kw || 0)
      .filter(p => !isNaN(p));
    
    if (powers.length > 0) {
      const stats = calculateStats(powers);
      const iqr = calculateIQR(powers);
      
      profile[hourOfWeek] = {
        ...stats,
        ...iqr,
        upperThreshold: iqr.q3 + (config.anomaly.iqrMultiplier * iqr.iqr),
      };
    }
  }
  
  return profile;
}

/**
 * Detect anomalies in a channel's data
 */
export function detectAnomalies(channelData, baselineData, config, intervalSeconds) {
  const { iqrMultiplier, minConsecutiveIntervals, minExcessKwh } = config.anomaly;
  const intervalHours = getIntervalHours(intervalSeconds);
  
  // Build baseline profile
  const baselineProfile = buildBaselineProfile(baselineData.readings, config);
  
  // Check each reading against baseline
  const anomalousReadings = [];
  
  for (const reading of channelData.readings) {
    const ts = parseTimestamp(reading.ts);
    const hourOfWeek = getHourOfWeek(ts);
    const baseline = baselineProfile[hourOfWeek];
    
    if (!baseline) continue; // No baseline for this hour
    
    const power = reading.P || reading.power_kw || 0;
    
    // Check if this reading exceeds the threshold
    if (power > baseline.upperThreshold) {
      const excessKw = power - baseline.median;
      const excessKwh = excessKw * intervalHours;
      
      anomalousReadings.push({
        ts: reading.ts,
        power,
        baselineMedian: baseline.median,
        threshold: baseline.upperThreshold,
        excessKw,
        excessKwh,
        zScore: zScore(power, baseline.mean, baseline.std),
        isBusinessHours: isBusinessHours(ts, config),
      });
    }
  }
  
  // Group consecutive anomalies into events
  const events = groupConsecutiveAnomalies(anomalousReadings, minConsecutiveIntervals);
  
  // Filter by minimum excess kWh
  const significantEvents = events.filter(event => event.totalExcessKwh >= minExcessKwh);
  
  return {
    channelId: channelData.channelId,
    channelName: channelData.channelName,
    anomalyCount: significantEvents.length,
    events: significantEvents,
  };
}

/**
 * Group consecutive anomalous readings into events
 */
function groupConsecutiveAnomalies(readings, minConsecutive) {
  if (readings.length === 0) return [];
  
  const events = [];
  let currentEvent = null;
  
  for (let i = 0; i < readings.length; i++) {
    const reading = readings[i];
    
    if (!currentEvent) {
      // Start new event
      currentEvent = {
        start: reading.ts,
        end: reading.ts,
        readings: [reading],
        peakPower: reading.power,
        totalExcessKwh: reading.excessKwh,
        avgExcessKw: reading.excessKw,
      };
    } else {
      // Check if consecutive (within 2 intervals)
      const prevTime = new Date(currentEvent.end).getTime();
      const currTime = new Date(reading.ts).getTime();
      const gap = (currTime - prevTime) / 1000; // seconds
      
      if (gap < 7200) { // Within 2 hours (allowing for missed intervals)
        // Add to current event
        currentEvent.end = reading.ts;
        currentEvent.readings.push(reading);
        currentEvent.peakPower = Math.max(currentEvent.peakPower, reading.power);
        currentEvent.totalExcessKwh += reading.excessKwh;
      } else {
        // Save current event and start new one
        if (currentEvent.readings.length >= minConsecutive) {
          currentEvent.avgExcessKw = currentEvent.totalExcessKwh / (currentEvent.readings.length * (1/4)); // Assuming 15-min intervals
          currentEvent.duration = `${currentEvent.readings.length} intervals`;
          currentEvent.context = currentEvent.readings[0].isBusinessHours ? 'business_hours' : 'after_hours';
          events.push(currentEvent);
        }
        
        currentEvent = {
          start: reading.ts,
          end: reading.ts,
          readings: [reading],
          peakPower: reading.power,
          totalExcessKwh: reading.excessKwh,
        };
      }
    }
  }
  
  // Save last event
  if (currentEvent && currentEvent.readings.length >= minConsecutive) {
    currentEvent.avgExcessKw = currentEvent.totalExcessKwh / (currentEvent.readings.length * (1/4));
    currentEvent.duration = `${currentEvent.readings.length} intervals`;
    currentEvent.context = currentEvent.readings[0].isBusinessHours ? 'business_hours' : 'after_hours';
    events.push(currentEvent);
  }
  
  return events;
}

/**
 * Analyze anomalies for all channels
 */
export function analyzeAnomalies(channelsData, baselinesData, config, intervalSeconds) {
  const results = [];
  
  for (const channelData of channelsData) {
    const baselineData = baselinesData.find(b => b.channelId === channelData.channelId);
    
    if (!baselineData || baselineData.readings.length === 0) {
      console.warn(`No baseline data for channel ${channelData.channelId}, skipping anomaly detection`);
      continue;
    }
    
    const result = detectAnomalies(channelData, baselineData, config, intervalSeconds);
    
    if (result.anomalyCount > 0) {
      results.push(result);
    }
  }
  
  // Sort by total excess kWh across all events
  results.sort((a, b) => {
    const aTotal = a.events.reduce((sum, e) => sum + e.totalExcessKwh, 0);
    const bTotal = b.events.reduce((sum, e) => sum + e.totalExcessKwh, 0);
    return bTotal - aTotal;
  });
  
  // Calculate summary statistics
  const totalEvents = results.reduce((sum, r) => sum + r.anomalyCount, 0);
  const totalExcessKwh = results.reduce((sum, r) => 
    sum + r.events.reduce((s, e) => s + e.totalExcessKwh, 0), 0
  );
  
  return {
    channelsWithAnomalies: results.length,
    totalAnomalyEvents: totalEvents,
    totalExcessKwh: parseFloat(totalExcessKwh.toFixed(2)),
    results,
    timeline: generateAnomalyTimeline(results),
  };
}

/**
 * Generate anomaly timeline for visualization
 */
function generateAnomalyTimeline(results) {
  const timeline = [];
  
  for (const channelResult of results) {
    for (const event of channelResult.events) {
      timeline.push({
        channelName: channelResult.channelName,
        start: event.start,
        end: event.end,
        peakPower: event.peakPower,
        excessKwh: event.totalExcessKwh,
        context: event.context,
      });
    }
  }
  
  // Sort by start time
  timeline.sort((a, b) => new Date(a.start) - new Date(b.start));
  
  return timeline;
}
