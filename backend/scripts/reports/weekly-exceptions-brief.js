#!/usr/bin/env node

/**
 * Weekly Exceptions & Opportunities Brief Generator
 * 
 * Generates a comprehensive weekly energy analytics report from Eniscope interval data
 * 
 * Usage:
 *   node weekly-exceptions-brief.js --site <org_id> [options]
 * 
 * Options:
 *   --site <id>        Site organization ID (required)
 *   --start <iso>      Report start date (ISO format, optional)
 *   --end <iso>        Report end date (ISO format, optional)
 *   --out <file>       Output file path (default: report-{timestamp}.json)
 *   --config <file>    Custom config file (optional)
 *   --timezone <tz>    Timezone override (default: America/New_York)
 * 
 * If --start and --end are not provided, uses last complete week (Mon-Sun)
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { parseArgs } from 'util';

// Import modules
import { DEFAULT_CONFIG, mergeConfig } from './config/report-config.js';
import { getLastCompleteWeek, getBaselinePeriod, formatDateRange } from './lib/date-utils.js';
import { WeeklyReportDataFetcher } from './lib/data-fetcher.js';
import { analyzeSensorHealthForSite } from './analytics/sensor-health.js';
import { analyzeAfterHoursWaste } from './analytics/after-hours-waste.js';
import { analyzeAnomalies } from './analytics/anomaly-detection.js';
import { analyzeSpikes } from './analytics/spike-detection.js';
import { generateQuickWins } from './analytics/quick-wins.js';
import { saveHTMLReport } from './lib/report-renderer.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Main report generation function
 */
async function generateWeeklyBrief(options) {
  const { siteId, startDate, endDate, config, outputPath } = options;
  
  console.log('\n' + '='.repeat(70));
  console.log('WEEKLY EXCEPTIONS & OPPORTUNITIES BRIEF');
  console.log('='.repeat(70));
  console.log(`Site ID: ${siteId}`);
  console.log(`Period: ${formatDateRange(startDate, endDate)}`);
  console.log(`Timezone: ${config.timezone}`);
  console.log('='.repeat(70) + '\n');
  
  // Initialize data fetcher
  const dataFetcher = new WeeklyReportDataFetcher(config);
  
  // Calculate baseline period
  const baselinePeriod = getBaselinePeriod(startDate, config.baseline.weeksCount);
  
  console.log(`Baseline period: ${formatDateRange(baselinePeriod.start, baselinePeriod.end)}`);
  console.log(`(${config.baseline.weeksCount} weeks prior to report week)\n`);
  
  // Fetch all data
  const data = await dataFetcher.fetchAllData(
    siteId,
    { start: startDate, end: endDate },
    baselinePeriod
  );
  
  console.log('\n' + '='.repeat(70));
  console.log('RUNNING ANALYTICS');
  console.log('='.repeat(70) + '\n');
  
  // Run analytics
  console.log('1. Analyzing sensor health...');
  const sensorHealth = analyzeSensorHealthForSite(
    data.reportData,
    config,
    data.resolution
  );
  console.log(`   Found ${sensorHealth.totalIssues} issue(s)\n`);
  
  console.log('2. Analyzing after-hours waste...');
  const afterHoursWaste = analyzeAfterHoursWaste(
    data.reportData,
    data.baselineData,
    config,
    data.resolution
  );
  console.log(`   Found ${afterHoursWaste.topMeters.length} meter(s) with significant excess\n`);
  
  console.log('3. Detecting anomalies...');
  const anomalies = analyzeAnomalies(
    data.reportData,
    data.baselineData,
    config,
    data.resolution
  );
  console.log(`   Found ${anomalies.totalAnomalyEvents} anomaly event(s)\n`);
  
  console.log('4. Detecting spikes...');
  const spikes = analyzeSpikes(
    data.reportData,
    data.baselineData,
    config,
    data.resolution
  );
  console.log(`   Found ${spikes.totalSpikeEvents} spike event(s)\n`);
  
  console.log('5. Generating quick wins...');
  const quickWins = generateQuickWins(
    {
      sensorHealth,
      afterHoursWaste,
      anomalies,
      spikes,
    },
    config
  );
  console.log(`   Generated ${quickWins.length} recommendation(s)\n`);
  
  // Build report structure
  const report = {
    metadata: {
      generatedAt: new Date().toISOString(),
      reportVersion: '1.0.0',
      site: data.siteMetadata,
      period: {
        start: startDate.toISOString(),
        end: endDate.toISOString(),
        timezone: config.timezone,
      },
      baseline: {
        start: baselinePeriod.start.toISOString(),
        end: baselinePeriod.end.toISOString(),
        weeksCount: config.baseline.weeksCount,
      },
      dataResolution: `${data.resolution}s (${data.resolution / 60}min)`,
    },
    
    summary: {
      headline: generateHeadline({
        sensorHealth,
        afterHoursWaste,
        anomalies,
        spikes,
      }),
      topRisks: identifyTopRisks({
        sensorHealth,
        afterHoursWaste,
        anomalies,
        spikes,
      }),
      topOpportunities: identifyTopOpportunities({
        afterHoursWaste,
        anomalies,
        spikes,
      }),
      totalPotentialSavings: {
        weeklyKwh: afterHoursWaste.summary.totalExcessKwh + anomalies.totalExcessKwh,
        weeklyCost: afterHoursWaste.summary.totalExcessCost + (anomalies.totalExcessKwh * config.tariff.defaultRate),
        estimatedAnnual: (afterHoursWaste.summary.totalExcessCost + (anomalies.totalExcessKwh * config.tariff.defaultRate)) * 52,
      },
    },
    
    sections: {
      sensorHealth: {
        summary: sensorHealth.summary,
        totalIssues: sensorHealth.totalIssues,
        bySeverity: {
          high: sensorHealth.highSeverity,
          medium: sensorHealth.mediumSeverity,
          low: sensorHealth.lowSeverity,
        },
        issues: sensorHealth.issues,
      },
      
      afterHoursWaste: {
        summary: afterHoursWaste.summary,
        topMeters: afterHoursWaste.topMeters,
      },
      
      anomalies: {
        summary: {
          totalEvents: anomalies.totalAnomalyEvents,
          affectedChannels: anomalies.channelsWithAnomalies,
          totalExcessKwh: anomalies.totalExcessKwh,
        },
        timeline: anomalies.timeline,
        byChannel: anomalies.results,
      },
      
      spikes: {
        summary: {
          totalEvents: spikes.totalSpikeEvents,
          affectedChannels: spikes.channelsWithSpikes,
          totalExcessKwh: spikes.totalExcessKwh,
        },
        topSpikes: spikes.topSpikes,
        byChannel: spikes.results,
      },
      
      quickWins,
    },
    
    charts: {
      afterHoursRanking: afterHoursWaste.charts?.topContributorsChart || [],
      anomalyTimeline: anomalies.timeline || [],
      spikeEvents: spikes.topSpikes || [],
    },
    
    dataQuality: {
      channelsAnalyzed: data.reportData.length,
      avgCompleteness: calculateAvgCompleteness(data.reportData),
      alarmsAndEvents: {
        alarmsCount: data.alarmsAndEvents.alarms.length,
        eventsCount: data.alarmsAndEvents.events.length,
        source: data.alarmsAndEvents.source,
      },
    },
  };
  
  // Save JSON report
  const outputDir = path.dirname(outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  fs.writeFileSync(outputPath, JSON.stringify(report, null, 2));
  
  // Generate HTML report (customer-ready format)
  const htmlPath = outputPath.replace('.json', '.html');
  saveHTMLReport(report, htmlPath);
  
  console.log('\n' + '='.repeat(70));
  console.log('REPORT GENERATION COMPLETE');
  console.log('='.repeat(70));
  console.log(`JSON Report: ${outputPath}`);
  console.log(`  File size: ${(fs.statSync(outputPath).size / 1024).toFixed(1)} KB`);
  console.log(`HTML Report: ${htmlPath}`);
  console.log(`  File size: ${(fs.statSync(htmlPath).size / 1024).toFixed(1)} KB`);
  console.log(`\n💡 Open the HTML file in your browser to view the professional report\n`);
  
  // Print summary to console
  printSummary(report);
  
  return report;
}

/**
 * Generate headline summary
 */
function generateHeadline(analytics) {
  const headlines = [];
  
  if (analytics.sensorHealth.highSeverity > 0) {
    headlines.push(`${analytics.sensorHealth.highSeverity} critical data quality issue(s)`);
  }
  
  if (analytics.afterHoursWaste.summary.totalExcessKwh > 50) {
    headlines.push(`${analytics.afterHoursWaste.summary.totalExcessKwh.toFixed(0)} kWh after-hours waste detected`);
  }
  
  if (analytics.anomalies.totalAnomalyEvents > 5) {
    headlines.push(`${analytics.anomalies.totalAnomalyEvents} anomalous consumption event(s)`);
  }
  
  if (analytics.spikes.totalSpikeEvents > 5) {
    headlines.push(`${analytics.spikes.totalSpikeEvents} demand spike(s) identified`);
  }
  
  if (headlines.length === 0) {
    headlines.push('No significant issues detected this week');
  }
  
  return headlines;
}

/**
 * Identify top risks
 */
function identifyTopRisks(analytics) {
  const risks = [];
  
  if (analytics.sensorHealth.highSeverity > 0) {
    risks.push({
      category: 'Data Quality',
      severity: 'high',
      description: `${analytics.sensorHealth.highSeverity} high-severity sensor/communication issue(s) preventing accurate monitoring`,
    });
  }
  
  if (analytics.anomalies.totalAnomalyEvents > 10) {
    risks.push({
      category: 'Consumption Anomalies',
      severity: 'medium',
      description: `${analytics.anomalies.totalAnomalyEvents} unexpected consumption event(s) requiring investigation`,
    });
  }
  
  return risks.slice(0, 5);
}

/**
 * Identify top opportunities
 */
function identifyTopOpportunities(analytics) {
  const opportunities = [];
  
  if (analytics.afterHoursWaste.summary.totalExcessKwh > 0) {
    opportunities.push({
      category: 'After-Hours Optimization',
      potentialSavings: `${analytics.afterHoursWaste.summary.totalExcessKwh.toFixed(0)} kWh/week`,
      annualValue: `$${analytics.afterHoursWaste.summary.estimatedAnnualCost.toFixed(0)}/year`,
      description: 'Reduce unnecessary equipment operation during unoccupied hours',
    });
  }
  
  if (analytics.spikes.totalSpikeEvents > 0) {
    opportunities.push({
      category: 'Demand Management',
      potentialSavings: `${analytics.spikes.totalExcessKwh.toFixed(0)} kWh/week`,
      annualValue: 'Plus potential demand charge reductions',
      description: 'Reduce peak demand through load management strategies',
    });
  }
  
  return opportunities.slice(0, 5);
}

/**
 * Calculate average data completeness
 */
function calculateAvgCompleteness(channelsData) {
  if (channelsData.length === 0) return 0;
  
  const completeness = channelsData.map(ch => {
    if (!ch.expectedIntervals || ch.expectedIntervals === 0) return 100;
    return (ch.readings.length / ch.expectedIntervals) * 100;
  });
  
  const avg = completeness.reduce((sum, c) => sum + c, 0) / completeness.length;
  return parseFloat(avg.toFixed(1));
}

/**
 * Print summary to console
 */
function printSummary(report) {
  console.log('EXECUTIVE SUMMARY');
  console.log('-'.repeat(70));
  
  console.log('\nHeadline:');
  report.summary.headline.forEach(h => console.log(`  • ${h}`));
  
  if (report.summary.topRisks.length > 0) {
    console.log('\nTop Risks:');
    report.summary.topRisks.forEach(r => {
      console.log(`  • [${r.severity.toUpperCase()}] ${r.category}: ${r.description}`);
    });
  }
  
  if (report.summary.topOpportunities.length > 0) {
    console.log('\nTop Opportunities:');
    report.summary.topOpportunities.forEach(o => {
      console.log(`  • ${o.category}: ${o.potentialSavings} (${o.annualValue})`);
      console.log(`    ${o.description}`);
    });
  }
  
  console.log('\nPotential Savings:');
  console.log(`  Weekly: ${report.summary.totalPotentialSavings.weeklyKwh.toFixed(0)} kWh ($${report.summary.totalPotentialSavings.weeklyCost.toFixed(2)})`);
  console.log(`  Annual: $${report.summary.totalPotentialSavings.estimatedAnnual.toFixed(0)}`);
  
  console.log('\nQuick Wins:');
  report.sections.quickWins.slice(0, 5).forEach((win, i) => {
    console.log(`  ${i + 1}. [${win.priority.toUpperCase()}] ${win.title}`);
    if (typeof win.impact.weeklyKwh === 'number') {
      console.log(`     Impact: ${win.impact.weeklyKwh.toFixed(0)} kWh/week ($${win.impact.weeklyCost.toFixed(2)})`);
    }
  });
  
  console.log('\n' + '='.repeat(70) + '\n');
}

/**
 * CLI entry point
 */
async function main() {
  try {
    // Parse command-line arguments
    const { values } = parseArgs({
      options: {
        site: { type: 'string' },
        start: { type: 'string' },
        end: { type: 'string' },
        out: { type: 'string' },
        config: { type: 'string' },
        timezone: { type: 'string' },
      },
    });
    
    if (!values.site) {
      console.error('Error: --site parameter is required\n');
      console.log('Usage: node weekly-exceptions-brief.js --site <org_id> [options]');
      console.log('\nOptions:');
      console.log('  --site <id>        Site organization ID (required)');
      console.log('  --start <iso>      Report start date (ISO format, optional)');
      console.log('  --end <iso>        Report end date (ISO format, optional)');
      console.log('  --out <file>       Output file path (default: report-{timestamp}.json)');
      console.log('  --config <file>    Custom config file (optional)');
      console.log('  --timezone <tz>    Timezone override (default: America/New_York)');
      console.log('\nExample:');
      console.log('  node weekly-exceptions-brief.js --site 12345 --out my-report.json');
      process.exit(1);
    }
    
    // Load custom config if provided
    let config = DEFAULT_CONFIG;
    if (values.config) {
      const customConfig = JSON.parse(fs.readFileSync(values.config, 'utf-8'));
      config = mergeConfig(customConfig);
    }
    
    // Override timezone if provided
    if (values.timezone) {
      config.timezone = values.timezone;
    }
    
    // Determine report period
    let startDate, endDate;
    if (values.start && values.end) {
      startDate = new Date(values.start);
      endDate = new Date(values.end);
    } else {
      const lastWeek = getLastCompleteWeek(config.timezone);
      startDate = lastWeek.start;
      endDate = lastWeek.end;
    }
    
    // Determine output path
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
    const outputPath = values.out || path.join(
      __dirname,
      '..',
      '..',
      '..',
      'data',
      `weekly-brief-${values.site}-${timestamp}.json`
    );
    
    // Generate report
    await generateWeeklyBrief({
      siteId: values.site,
      startDate,
      endDate,
      config,
      outputPath,
    });
    
  } catch (error) {
    console.error('\n❌ Error generating report:', error.message);
    if (process.env.DEBUG) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { generateWeeklyBrief };
