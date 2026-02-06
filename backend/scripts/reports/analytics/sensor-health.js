/**
 * Sensor & Communications Health Analytics
 * 
 * Detects data quality issues:
 * - Missing data gaps
 * - Stale meters (no recent data)
 * - Flatlined sensors
 * - Low data completeness
 */

import { findGaps, calculateCompleteness, rollingVariance } from '../lib/stats-utils.js';
import { parseTimestamp, getIntervalHours } from '../lib/date-utils.js';

/**
 * Analyze sensor health for a channel's data
 */
export function analyzeSensorHealth(channelData, config, intervalSeconds) {
  const {
    gapMultiplier,
    missingThresholdPct,
    flatlineHours,
    flatlineVarianceThreshold,
  } = config.sensorHealth;
  
  const issues = [];
  const channelId = channelData.channelId;
  const channelName = channelData.channelName;
  
  // 1. Detect missing data gaps
  const gaps = findGaps(
    channelData.readings.map(r => r.ts),
    intervalSeconds
  );
  
  for (const gap of gaps) {
    if (gap.missingIntervals >= gapMultiplier) {
      issues.push({
        type: 'missing_data',
        severity: gap.missingIntervals > 10 ? 'high' : 'medium',
        channelId,
        channelName,
        start: gap.start,
        end: gap.end,
        missingIntervals: gap.missingIntervals,
        duration: `${(gap.actualInterval / 3600).toFixed(1)} hours`,
        description: `Missing ${gap.missingIntervals} intervals (${(gap.actualInterval / 3600).toFixed(1)}h gap)`,
      });
    }
  }
  
  // 2. Check overall data completeness
  const expectedIntervals = channelData.expectedIntervals || channelData.readings.length;
  const actualIntervals = channelData.readings.length;
  const completeness = calculateCompleteness(actualIntervals, expectedIntervals);
  
  if (completeness < (100 - missingThresholdPct)) {
    issues.push({
      type: 'low_completeness',
      severity: completeness < 50 ? 'high' : 'medium',
      channelId,
      channelName,
      completeness: completeness.toFixed(1) + '%',
      missingCount: expectedIntervals - actualIntervals,
      description: `Only ${completeness.toFixed(1)}% data completeness (missing ${expectedIntervals - actualIntervals} intervals)`,
    });
  }
  
  // 3. Detect flatlined sensors
  const powerReadings = channelData.readings
    .map(r => r.P || r.power_kw || 0)
    .filter(p => !isNaN(p));
  
  if (powerReadings.length > 0) {
    const flatlineWindow = Math.ceil((flatlineHours * 3600) / intervalSeconds);
    
    if (powerReadings.length >= flatlineWindow) {
      const rolling = rollingVariance(powerReadings, flatlineWindow);
      
      for (const stat of rolling) {
        if (stat.variance < flatlineVarianceThreshold && stat.mean > 0.1) {
          // Flatline detected (low variance but non-zero mean)
          const startIdx = stat.index - flatlineWindow + 1;
          const endIdx = stat.index;
          
          issues.push({
            type: 'flatline',
            severity: 'medium',
            channelId,
            channelName,
            start: channelData.readings[startIdx]?.ts,
            end: channelData.readings[endIdx]?.ts,
            meanPower: stat.mean.toFixed(2) + ' kW',
            variance: stat.variance.toFixed(4),
            description: `Flatlined at ${stat.mean.toFixed(2)} kW for ${flatlineHours}+ hours (possible stuck sensor)`,
          });
          
          // Only report first flatline to avoid spam
          break;
        }
      }
    }
  }
  
  // 4. Check for stale data (last reading is old)
  if (channelData.readings.length > 0) {
    const lastReading = channelData.readings[channelData.readings.length - 1];
    const lastTime = parseTimestamp(lastReading.ts);
    const now = new Date();
    const hoursSinceLastReading = (now - lastTime) / (1000 * 3600);
    
    if (hoursSinceLastReading > config.sensorHealth.staleHours) {
      issues.push({
        type: 'stale_data',
        severity: hoursSinceLastReading > 24 ? 'high' : 'low',
        channelId,
        channelName,
        lastReading: lastReading.ts,
        hoursSince: hoursSinceLastReading.toFixed(1),
        description: `No data for ${hoursSinceLastReading.toFixed(1)} hours (last: ${lastTime.toLocaleString()})`,
        source: 'inferred_from_timestamps',
      });
    }
  }
  
  return issues;
}

/**
 * Analyze sensor health for all channels
 */
export function analyzeSensorHealthForSite(channelsData, config, intervalSeconds) {
  const allIssues = [];
  
  for (const channelData of channelsData) {
    const issues = analyzeSensorHealth(channelData, config, intervalSeconds);
    allIssues.push(...issues);
  }
  
  // Sort by severity
  const severityOrder = { high: 0, medium: 1, low: 2 };
  allIssues.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);
  
  return {
    totalIssues: allIssues.length,
    highSeverity: allIssues.filter(i => i.severity === 'high').length,
    mediumSeverity: allIssues.filter(i => i.severity === 'medium').length,
    lowSeverity: allIssues.filter(i => i.severity === 'low').length,
    issues: allIssues,
    summary: generateHealthSummary(allIssues),
  };
}

/**
 * Generate a summary of health issues
 */
function generateHealthSummary(issues) {
  const byType = {};
  
  for (const issue of issues) {
    if (!byType[issue.type]) {
      byType[issue.type] = {
        count: 0,
        channels: new Set(),
      };
    }
    byType[issue.type].count++;
    byType[issue.type].channels.add(issue.channelName);
  }
  
  const summary = [];
  
  for (const [type, data] of Object.entries(byType)) {
    const channelList = Array.from(data.channels).slice(0, 3).join(', ');
    const moreText = data.channels.size > 3 ? ` and ${data.channels.size - 3} more` : '';
    
    summary.push({
      type,
      count: data.count,
      affectedChannels: data.channels.size,
      description: `${data.count} ${type} issue(s) affecting ${data.channels.size} channel(s): ${channelList}${moreText}`,
    });
  }
  
  return summary;
}
