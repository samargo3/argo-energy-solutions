/**
 * Spike Detection Analytics
 * 
 * Identifies unusual power spikes that exceed normal operating levels
 */

import { percentile, groupBy } from '../lib/stats-utils.js';
import { parseTimestamp, getHourOfWeek, getIntervalHours } from '../lib/date-utils.js';

/**
 * Build baseline for spike detection (95th percentile by hour of week)
 */
function buildSpikeBaseline(baselineReadings) {
  const grouped = groupBy(baselineReadings, reading => {
    const ts = parseTimestamp(reading.ts);
    return getHourOfWeek(ts);
  });
  
  const baseline = {};
  
  for (const [hourOfWeek, readings] of Object.entries(grouped)) {
    const powers = readings
      .map(r => r.P || r.power_kw || 0)
      .filter(p => !isNaN(p));
    
    if (powers.length > 0) {
      baseline[hourOfWeek] = {
        p95: percentile(powers, 95),
        p50: percentile(powers, 50),
        count: powers.length,
      };
    }
  }
  
  return baseline;
}

/**
 * Detect spikes in a channel's data
 */
export function detectSpikes(channelData, baselineData, config, intervalSeconds, isSiteTotal = false) {
  const { baselinePercentile, multiplier, submeterMinKw, siteMinKw, minDuration } = config.spike;
  const minAbsoluteKw = isSiteTotal ? siteMinKw : submeterMinKw;
  const intervalHours = getIntervalHours(intervalSeconds);
  
  // Build baseline
  const baseline = buildSpikeBaseline(baselineData.readings);
  
  // Detect spikes
  const spikes = [];
  
  for (const reading of channelData.readings) {
    const ts = parseTimestamp(reading.ts);
    const hourOfWeek = getHourOfWeek(ts);
    const baselineStats = baseline[hourOfWeek];
    
    if (!baselineStats) continue;
    
    const power = reading.P || reading.power_kw || 0;
    const threshold = Math.max(baselineStats.p95 * multiplier, minAbsoluteKw);
    
    if (power > threshold && power > minAbsoluteKw) {
      spikes.push({
        ts: reading.ts,
        power,
        baselineP95: baselineStats.p95,
        threshold,
        excessKw: power - baselineStats.p95,
        excessKwh: (power - baselineStats.p95) * intervalHours,
      });
    }
  }
  
  // Group adjacent spikes into events
  const events = groupConsecutiveSpikes(spikes, intervalSeconds);
  
  // Filter by minimum duration
  const significantEvents = events.filter(e => e.intervals >= minDuration);
  
  return {
    channelId: channelData.channelId,
    channelName: channelData.channelName,
    spikeCount: significantEvents.length,
    events: significantEvents,
  };
}

/**
 * Group consecutive spike readings into events
 */
function groupConsecutiveSpikes(spikes, intervalSeconds) {
  if (spikes.length === 0) return [];
  
  const events = [];
  let currentEvent = null;
  
  for (const spike of spikes) {
    if (!currentEvent) {
      currentEvent = {
        start: spike.ts,
        end: spike.ts,
        peakPower: spike.power,
        totalExcessKwh: spike.excessKwh,
        intervals: 1,
      };
    } else {
      const prevTime = new Date(currentEvent.end).getTime();
      const currTime = new Date(spike.ts).getTime();
      const gap = (currTime - prevTime) / 1000;
      
      // Check if consecutive (within 2 intervals)
      if (gap <= intervalSeconds * 2) {
        currentEvent.end = spike.ts;
        currentEvent.peakPower = Math.max(currentEvent.peakPower, spike.power);
        currentEvent.totalExcessKwh += spike.excessKwh;
        currentEvent.intervals++;
      } else {
        // Save current and start new
        events.push({
          ...currentEvent,
          duration: `${currentEvent.intervals} intervals`,
        });
        
        currentEvent = {
          start: spike.ts,
          end: spike.ts,
          peakPower: spike.power,
          totalExcessKwh: spike.excessKwh,
          intervals: 1,
        };
      }
    }
  }
  
  // Save last event
  if (currentEvent) {
    events.push({
      ...currentEvent,
      duration: `${currentEvent.intervals} intervals`,
    });
  }
  
  return events;
}

/**
 * Analyze spikes for all channels
 */
export function analyzeSpikes(channelsData, baselinesData, config, intervalSeconds, siteChannelId = null) {
  const results = [];
  
  for (const channelData of channelsData) {
    const baselineData = baselinesData.find(b => b.channelId === channelData.channelId);
    
    if (!baselineData || baselineData.readings.length === 0) {
      console.warn(`No baseline data for channel ${channelData.channelId}, skipping spike detection`);
      continue;
    }
    
    const isSiteTotal = channelData.channelId === siteChannelId;
    const result = detectSpikes(channelData, baselineData, config, intervalSeconds, isSiteTotal);
    
    if (result.spikeCount > 0) {
      results.push(result);
    }
  }
  
  // Sort by peak power
  results.sort((a, b) => {
    const aPeak = Math.max(...a.events.map(e => e.peakPower));
    const bPeak = Math.max(...b.events.map(e => e.peakPower));
    return bPeak - aPeak;
  });
  
  const totalEvents = results.reduce((sum, r) => sum + r.spikeCount, 0);
  const totalExcessKwh = results.reduce((sum, r) => 
    sum + r.events.reduce((s, e) => s + e.totalExcessKwh, 0), 0
  );
  
  return {
    channelsWithSpikes: results.length,
    totalSpikeEvents: totalEvents,
    totalExcessKwh: parseFloat(totalExcessKwh.toFixed(2)),
    results,
    topSpikes: getTopSpikes(results, 10),
  };
}

/**
 * Get top N spikes by peak power
 */
function getTopSpikes(results, count) {
  const allSpikes = [];
  
  for (const channelResult of results) {
    for (const event of channelResult.events) {
      allSpikes.push({
        channelName: channelResult.channelName,
        ...event,
      });
    }
  }
  
  allSpikes.sort((a, b) => b.peakPower - a.peakPower);
  
  return allSpikes.slice(0, count);
}
