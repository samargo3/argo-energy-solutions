/**
 * Quick Wins Generator
 * 
 * Generates actionable recommendations based on analytics findings
 */

/**
 * Generate quick wins from all analytics results
 */
export function generateQuickWins(analytics, config) {
  const wins = [];
  
  // 1. After-hours waste opportunities
  if (analytics.afterHoursWaste?.topMeters) {
    for (const meter of analytics.afterHoursWaste.topMeters.slice(0, 3)) {
      if (meter.impact.excessKwh >= config.quickWins.minWeeklyImpact) {
        wins.push({
          title: `Reduce overnight base load on ${meter.channelName}`,
          type: 'after_hours_waste',
          priority: meter.impact.excessKwh > 100 ? 'high' : 'medium',
          impact: {
            weeklyKwh: meter.impact.excessKwh,
            weeklyCost: meter.impact.excessCost,
            annualCost: meter.impact.excessCost * 52,
          },
          description: `${meter.channelName} is consuming ${meter.thisWeek.avgPowerKw.toFixed(1)} kW on average during after-hours, ` +
            `${((meter.impact.excessKwh / meter.thisWeek.totalAfterHoursKwh) * 100).toFixed(0)}% above baseline. ` +
            `This suggests equipment running unnecessarily or at higher than needed levels.`,
          recommendations: [
            'Verify equipment schedules match actual occupancy',
            'Check for HVAC systems running outside business hours',
            'Look for computers/servers left on unnecessarily',
            'Consider adding occupancy sensors or time-based controls',
          ],
          confidence: meter.thisWeek.intervals > 100 ? 'high' : 'medium',
          owner: 'Facilities Manager',
          effort: 'Low to Medium',
        });
      }
    }
  }
  
  // 2. Sensor/communications issues
  if (analytics.sensorHealth?.highSeverity > 0) {
    const highIssues = analytics.sensorHealth.issues.filter(i => i.severity === 'high');
    const affectedChannels = [...new Set(highIssues.map(i => i.channelName))];
    
    if (affectedChannels.length > 0) {
      wins.push({
        title: `Fix data communication issues on ${affectedChannels.length} meter(s)`,
        type: 'sensor_health',
        priority: 'high',
        impact: {
          weeklyKwh: 'N/A',
          weeklyCost: 0,
          annualCost: 0,
          description: 'Missing data prevents accurate monitoring and may hide energy waste',
        },
        description: `${affectedChannels.length} meter(s) have high-severity data issues: ${affectedChannels.slice(0, 3).join(', ')}. ` +
          `This prevents accurate energy monitoring and may be hiding consumption anomalies.`,
        recommendations: [
          'Check network connectivity and power to affected meters',
          'Verify meter configuration and data logging settings',
          'Contact meter vendor if issues persist',
          'Consider replacing meters with repeated failures',
        ],
        confidence: 'high',
        owner: 'Energy Manager / Facilities',
        effort: 'Medium',
      });
    }
  }
  
  // 3. Anomaly patterns
  if (analytics.anomalies?.totalAnomalyEvents > 0) {
    const topAnomaly = analytics.anomalies.results[0];
    
    if (topAnomaly && topAnomaly.events.length > 0) {
      const topEvent = topAnomaly.events[0];
      
      wins.push({
        title: `Investigate recurring spikes on ${topAnomaly.channelName}`,
        type: 'anomaly',
        priority: topEvent.totalExcessKwh > 50 ? 'high' : 'medium',
        impact: {
          weeklyKwh: topEvent.totalExcessKwh,
          weeklyCost: topEvent.totalExcessKwh * config.tariff.defaultRate,
          annualCost: topEvent.totalExcessKwh * config.tariff.defaultRate * 52,
        },
        description: `${topAnomaly.channelName} showed ${topAnomaly.anomalyCount} anomalous event(s) this week, ` +
          `consuming ${topEvent.totalExcessKwh.toFixed(1)} kWh above normal patterns. ` +
          `Peak was ${topEvent.peakPower.toFixed(1)} kW during ${topEvent.context}.`,
        recommendations: [
          'Review equipment operation logs for this time period',
          'Check if new equipment was added or settings changed',
          'Verify load is appropriate for operational needs',
          'Consider load shifting if during peak demand periods',
        ],
        confidence: 'medium',
        owner: 'Operations / Energy Manager',
        effort: 'Medium',
      });
    }
  }
  
  // 4. Demand spike reduction
  if (analytics.spikes?.topSpikes && analytics.spikes.topSpikes.length > 0) {
    const topSpike = analytics.spikes.topSpikes[0];
    
    wins.push({
      title: `Reduce demand spikes on ${topSpike.channelName}`,
      type: 'spike',
      priority: 'medium',
      impact: {
        weeklyKwh: topSpike.totalExcessKwh,
        weeklyCost: topSpike.totalExcessKwh * config.tariff.defaultRate,
        annualCost: topSpike.totalExcessKwh * config.tariff.defaultRate * 52,
        additionalNote: config.tariff.demandCharge 
          ? `Plus potential demand charges: $${(topSpike.peakPower * config.tariff.demandCharge).toFixed(2)}/month`
          : 'May also impact demand charges if applicable',
      },
      description: `${topSpike.channelName} experienced spikes up to ${topSpike.peakPower.toFixed(1)} kW. ` +
        `This may indicate short-cycling, simultaneous equipment starts, or undersized equipment.`,
      recommendations: [
        'Stagger start times for large equipment',
        'Check for short-cycling HVAC or refrigeration',
        'Consider soft-start controllers for motors',
        'Verify equipment is properly sized',
      ],
      confidence: 'medium',
      owner: 'Facilities Manager',
      effort: 'Medium to High',
    });
  }
  
  // 5. Low-hanging fruit: flatlined sensors
  const flatlineIssues = analytics.sensorHealth?.issues.filter(i => i.type === 'flatline') || [];
  if (flatlineIssues.length > 0) {
    wins.push({
      title: `Check stuck sensors (${flatlineIssues.length} detected)`,
      type: 'sensor_health',
      priority: 'low',
      impact: {
        weeklyKwh: 'N/A',
        weeklyCost: 0,
        annualCost: 0,
        description: 'Stuck sensors provide inaccurate data for decision-making',
      },
      description: `${flatlineIssues.length} sensor(s) appear flatlined (stuck at constant value). ` +
        `This typically indicates sensor failure or configuration issues.`,
      recommendations: [
        'Inspect physical sensors for damage or disconnection',
        'Reset or recalibrate affected meters',
        'Replace sensors if recalibration fails',
      ],
      confidence: 'high',
      owner: 'Facilities / Maintenance',
      effort: 'Low',
    });
  }
  
  // 6. Aggregate opportunity summary
  if (analytics.afterHoursWaste?.summary.totalExcessKwh > 0) {
    wins.push({
      title: 'Overall after-hours optimization opportunity',
      type: 'summary',
      priority: 'high',
      impact: {
        weeklyKwh: analytics.afterHoursWaste.summary.totalExcessKwh,
        weeklyCost: analytics.afterHoursWaste.summary.totalExcessCost,
        annualCost: analytics.afterHoursWaste.summary.estimatedAnnualCost,
      },
      description: `Site-wide after-hours consumption is ${analytics.afterHoursWaste.summary.totalExcessKwh.toFixed(0)} kWh/week ` +
        `above baseline. This represents a significant optimization opportunity.`,
      recommendations: [
        'Conduct comprehensive after-hours walk-through',
        'Review and update all equipment schedules',
        'Implement building automation or occupancy-based controls',
        'Set up weekly monitoring to track progress',
      ],
      confidence: 'high',
      owner: 'Energy Manager / Facilities Director',
      effort: 'Medium',
    });
  }
  
  // Sort by priority and impact
  const priorityOrder = { high: 0, medium: 1, low: 2 };
  wins.sort((a, b) => {
    if (a.priority !== b.priority) {
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    }
    const aImpact = typeof a.impact.weeklyKwh === 'number' ? a.impact.weeklyKwh : 0;
    const bImpact = typeof b.impact.weeklyKwh === 'number' ? b.impact.weeklyKwh : 0;
    return bImpact - aImpact;
  });
  
  // Limit to max count
  return wins.slice(0, config.quickWins.maxCount);
}
