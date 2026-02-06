/**
 * Professional Report Renderer
 * 
 * Converts JSON report to customer-ready HTML format
 */

import fs from 'fs';

/**
 * Format currency
 */
function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Format number with commas
 */
function formatNumber(value, decimals = 0) {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * Format date
 */
function formatDate(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

/**
 * Get severity badge color
 */
function getSeverityColor(severity) {
  const colors = {
    high: '#dc3545',
    medium: '#fd7e14',
    low: '#ffc107'
  };
  return colors[severity] || '#6c757d';
}

/**
 * Get priority badge color
 */
function getPriorityColor(priority) {
  const colors = {
    high: '#dc3545',
    medium: '#fd7e14',
    low: '#28a745'
  };
  return colors[priority] || '#6c757d';
}

/**
 * Render HTML report
 */
export function renderHTMLReport(reportData) {
  const { metadata, summary, sections } = reportData;
  
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Weekly Energy Report - ${metadata.site.siteName}</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      line-height: 1.6;
      color: #333;
      background: #f8f9fa;
      padding: 20px;
    }
    
    .container {
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      box-shadow: 0 0 20px rgba(0,0,0,0.1);
    }
    
    .header {
      background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
      color: white;
      padding: 40px;
      text-align: center;
    }
    
    .header h1 {
      font-size: 32px;
      margin-bottom: 10px;
      font-weight: 600;
    }
    
    .header .subtitle {
      font-size: 18px;
      opacity: 0.9;
    }
    
    .company-logo {
      margin-bottom: 20px;
      font-size: 24px;
      font-weight: 700;
      letter-spacing: 1px;
    }
    
    .report-meta {
      background: #f8f9fa;
      padding: 30px 40px;
      border-bottom: 1px solid #dee2e6;
    }
    
    .report-meta-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 20px;
    }
    
    .meta-item {
      display: flex;
      flex-direction: column;
    }
    
    .meta-label {
      font-size: 12px;
      text-transform: uppercase;
      color: #6c757d;
      margin-bottom: 5px;
      font-weight: 600;
    }
    
    .meta-value {
      font-size: 16px;
      color: #212529;
      font-weight: 500;
    }
    
    .content {
      padding: 40px;
    }
    
    .section {
      margin-bottom: 40px;
    }
    
    .section-title {
      font-size: 24px;
      color: #1e3a8a;
      margin-bottom: 20px;
      padding-bottom: 10px;
      border-bottom: 3px solid #3b82f6;
      font-weight: 600;
    }
    
    .executive-summary {
      background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
      padding: 30px;
      border-radius: 8px;
      margin-bottom: 40px;
      border-left: 5px solid #3b82f6;
    }
    
    .executive-summary h2 {
      color: #1e3a8a;
      margin-bottom: 20px;
      font-size: 28px;
    }
    
    .headline-items {
      list-style: none;
      margin: 20px 0;
    }
    
    .headline-items li {
      padding: 10px 0;
      padding-left: 30px;
      position: relative;
      font-size: 16px;
    }
    
    .headline-items li:before {
      content: "•";
      position: absolute;
      left: 10px;
      color: #3b82f6;
      font-weight: bold;
      font-size: 20px;
    }
    
    .savings-box {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: white;
      padding: 25px;
      border-radius: 8px;
      margin: 20px 0;
      text-align: center;
    }
    
    .savings-box h3 {
      font-size: 16px;
      margin-bottom: 15px;
      opacity: 0.9;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
    
    .savings-amount {
      font-size: 48px;
      font-weight: 700;
      margin: 10px 0;
    }
    
    .savings-detail {
      font-size: 14px;
      opacity: 0.9;
      margin-top: 10px;
    }
    
    .quick-wins {
      list-style: none;
    }
    
    .quick-win-item {
      background: #f8f9fa;
      border-left: 5px solid #3b82f6;
      padding: 20px;
      margin-bottom: 15px;
      border-radius: 4px;
    }
    
    .quick-win-header {
      display: flex;
      justify-content: space-between;
      align-items: start;
      margin-bottom: 10px;
      flex-wrap: wrap;
      gap: 10px;
    }
    
    .quick-win-title {
      font-size: 18px;
      font-weight: 600;
      color: #212529;
      flex: 1;
    }
    
    .badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: white;
    }
    
    .impact-box {
      background: #e7f5ff;
      padding: 15px;
      border-radius: 4px;
      margin: 15px 0;
    }
    
    .impact-row {
      display: flex;
      justify-content: space-between;
      padding: 5px 0;
    }
    
    .impact-label {
      font-weight: 600;
      color: #495057;
    }
    
    .impact-value {
      color: #059669;
      font-weight: 700;
    }
    
    .recommendations-list {
      list-style: none;
      margin-top: 10px;
    }
    
    .recommendations-list li {
      padding: 5px 0 5px 20px;
      position: relative;
      font-size: 14px;
      color: #495057;
    }
    
    .recommendations-list li:before {
      content: "→";
      position: absolute;
      left: 0;
      color: #3b82f6;
    }
    
    .risk-item {
      background: #fff5f5;
      border-left: 5px solid #dc3545;
      padding: 15px;
      margin-bottom: 10px;
      border-radius: 4px;
    }
    
    .risk-header {
      font-weight: 600;
      font-size: 16px;
      margin-bottom: 8px;
      color: #dc3545;
    }
    
    .opportunity-item {
      background: #f0fdf4;
      border-left: 5px solid #10b981;
      padding: 15px;
      margin-bottom: 10px;
      border-radius: 4px;
    }
    
    .opportunity-header {
      font-weight: 600;
      font-size: 16px;
      margin-bottom: 8px;
      color: #059669;
    }
    
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
      font-size: 14px;
    }
    
    th {
      background: #1e3a8a;
      color: white;
      padding: 12px;
      text-align: left;
      font-weight: 600;
      text-transform: uppercase;
      font-size: 12px;
      letter-spacing: 0.5px;
    }
    
    td {
      padding: 12px;
      border-bottom: 1px solid #dee2e6;
    }
    
    tbody tr:hover {
      background: #f8f9fa;
    }
    
    .footer {
      background: #f8f9fa;
      padding: 30px 40px;
      border-top: 1px solid #dee2e6;
      text-align: center;
      color: #6c757d;
      font-size: 14px;
    }
    
    .footer-company {
      font-weight: 600;
      color: #1e3a8a;
      margin-bottom: 10px;
      font-size: 16px;
    }
    
    .data-quality-badge {
      display: inline-block;
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 600;
      margin: 5px;
    }
    
    .quality-excellent {
      background: #d1fae5;
      color: #065f46;
    }
    
    .quality-good {
      background: #fef3c7;
      color: #92400e;
    }
    
    .quality-poor {
      background: #fee2e2;
      color: #991b1b;
    }
    
    @media print {
      body {
        padding: 0;
        background: white;
      }
      
      .container {
        box-shadow: none;
      }
      
      .section {
        page-break-inside: avoid;
      }
      
      .quick-win-item {
        page-break-inside: avoid;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <div class="header">
      <div class="company-logo">⚡ ARGO ENERGY SOLUTIONS</div>
      <h1>Weekly Energy Analytics Report</h1>
      <div class="subtitle">${metadata.site.siteName}</div>
    </div>
    
    <!-- Report Metadata -->
    <div class="report-meta">
      <div class="report-meta-grid">
        <div class="meta-item">
          <div class="meta-label">Report Period</div>
          <div class="meta-value">${formatDate(metadata.period.start)} - ${formatDate(metadata.period.end)}</div>
        </div>
        <div class="meta-item">
          <div class="meta-label">Location</div>
          <div class="meta-value">${metadata.site.city}, ${metadata.site.country}</div>
        </div>
        <div class="meta-item">
          <div class="meta-label">Generated</div>
          <div class="meta-value">${new Date(metadata.generatedAt).toLocaleDateString('en-US')}</div>
        </div>
        <div class="meta-item">
          <div class="meta-label">Data Quality</div>
          <div class="meta-value">${reportData.dataQuality.avgCompleteness.toFixed(1)}% Complete</div>
        </div>
      </div>
    </div>
    
    <!-- Main Content -->
    <div class="content">
      
      <!-- Executive Summary -->
      <div class="executive-summary">
        <h2>📊 Executive Summary</h2>
        
        ${summary.headline.length > 0 ? `
        <h3 style="margin-top: 20px; margin-bottom: 10px; font-size: 18px; color: #1e3a8a;">Key Findings</h3>
        <ul class="headline-items">
          ${summary.headline.map(h => `<li>${h}</li>`).join('')}
        </ul>
        ` : ''}
        
        ${summary.totalPotentialSavings.weeklyKwh > 0 ? `
        <div class="savings-box">
          <h3>Total Potential Savings</h3>
          <div class="savings-amount">${formatCurrency(summary.totalPotentialSavings.estimatedAnnual)}</div>
          <div class="savings-detail">
            ${formatNumber(summary.totalPotentialSavings.weeklyKwh)} kWh per week
            (${formatCurrency(summary.totalPotentialSavings.weeklyCost)}/week)
          </div>
        </div>
        ` : ''}
        
        ${summary.topRisks.length > 0 ? `
        <h3 style="margin-top: 30px; margin-bottom: 15px; font-size: 18px; color: #dc3545;">⚠️ Top Risks</h3>
        ${summary.topRisks.map(risk => `
          <div class="risk-item">
            <div class="risk-header">
              <span class="badge" style="background-color: ${getSeverityColor(risk.severity)}">${risk.severity}</span>
              ${risk.category}
            </div>
            <div>${risk.description}</div>
          </div>
        `).join('')}
        ` : ''}
        
        ${summary.topOpportunities.length > 0 ? `
        <h3 style="margin-top: 30px; margin-bottom: 15px; font-size: 18px; color: #059669;">💡 Top Opportunities</h3>
        ${summary.topOpportunities.map(opp => `
          <div class="opportunity-item">
            <div class="opportunity-header">${opp.category}</div>
            <div style="margin-bottom: 5px;"><strong>${opp.potentialSavings}</strong> (${opp.annualValue})</div>
            <div style="font-size: 14px; color: #495057;">${opp.description}</div>
          </div>
        `).join('')}
        ` : ''}
      </div>
      
      <!-- Quick Wins -->
      ${sections.quickWins.length > 0 ? `
      <div class="section">
        <h2 class="section-title">✅ Recommended Actions (Quick Wins)</h2>
        <ul class="quick-wins">
          ${sections.quickWins.map((win, i) => `
            <li class="quick-win-item">
              <div class="quick-win-header">
                <div class="quick-win-title">
                  ${i + 1}. ${win.title}
                </div>
                <span class="badge" style="background-color: ${getPriorityColor(win.priority)}">${win.priority} priority</span>
              </div>
              
              ${typeof win.impact.weeklyKwh === 'number' ? `
              <div class="impact-box">
                <div class="impact-row">
                  <span class="impact-label">Weekly Impact:</span>
                  <span class="impact-value">${formatNumber(win.impact.weeklyKwh)} kWh (${formatCurrency(win.impact.weeklyCost)})</span>
                </div>
                <div class="impact-row">
                  <span class="impact-label">Annual Value:</span>
                  <span class="impact-value">${formatCurrency(win.impact.annualCost)}</span>
                </div>
              </div>
              ` : ''}
              
              <div style="margin: 15px 0; color: #495057;">${win.description}</div>
              
              ${win.recommendations && win.recommendations.length > 0 ? `
              <div>
                <strong style="font-size: 14px; color: #495057;">Recommended Actions:</strong>
                <ul class="recommendations-list">
                  ${win.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
              </div>
              ` : ''}
              
              <div style="margin-top: 15px; font-size: 13px; color: #6c757d;">
                <strong>Owner:</strong> ${win.owner} | 
                <strong>Effort:</strong> ${win.effort} | 
                <strong>Confidence:</strong> ${win.confidence}
              </div>
            </li>
          `).join('')}
        </ul>
      </div>
      ` : ''}
      
      <!-- After-Hours Waste -->
      ${sections.afterHoursWaste.topMeters.length > 0 ? `
      <div class="section">
        <h2 class="section-title">🌙 After-Hours Energy Waste Analysis</h2>
        <p style="margin-bottom: 20px; color: #495057;">
          Equipment running during unoccupied hours (evenings, weekends) when not needed for operations.
        </p>
        
        <table>
          <thead>
            <tr>
              <th>Equipment/Meter</th>
              <th>Excess kWh/Week</th>
              <th>Weekly Cost</th>
              <th>Annual Cost</th>
              <th>Avg Power</th>
            </tr>
          </thead>
          <tbody>
            ${sections.afterHoursWaste.topMeters.slice(0, 10).map(meter => `
              <tr>
                <td><strong>${meter.channelName}</strong></td>
                <td>${formatNumber(meter.impact.excessKwh, 1)}</td>
                <td>${formatCurrency(meter.impact.excessCost)}</td>
                <td>${formatCurrency(meter.impact.excessCost * 52)}</td>
                <td>${formatNumber(meter.thisWeek.avgPowerKw, 2)} kW</td>
              </tr>
            `).join('')}
            <tr style="background: #e7f5ff; font-weight: 600;">
              <td>TOTAL</td>
              <td>${formatNumber(sections.afterHoursWaste.summary.totalExcessKwh, 1)}</td>
              <td>${formatCurrency(sections.afterHoursWaste.summary.totalExcessCost)}</td>
              <td>${formatCurrency(sections.afterHoursWaste.summary.estimatedAnnualCost)}</td>
              <td>-</td>
            </tr>
          </tbody>
        </table>
      </div>
      ` : ''}
      
      <!-- Anomalies -->
      ${sections.anomalies.summary.totalEvents > 0 ? `
      <div class="section">
        <h2 class="section-title">📈 Consumption Anomalies</h2>
        <p style="margin-bottom: 20px; color: #495057;">
          Unusual consumption patterns detected this week compared to baseline (previous 4 weeks).
        </p>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 4px; margin-bottom: 20px;">
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
            <div>
              <div style="font-size: 12px; color: #6c757d; text-transform: uppercase; margin-bottom: 5px;">Total Events</div>
              <div style="font-size: 24px; font-weight: 700; color: #1e3a8a;">${sections.anomalies.summary.totalEvents}</div>
            </div>
            <div>
              <div style="font-size: 12px; color: #6c757d; text-transform: uppercase; margin-bottom: 5px;">Affected Equipment</div>
              <div style="font-size: 24px; font-weight: 700; color: #1e3a8a;">${sections.anomalies.summary.affectedChannels}</div>
            </div>
            <div>
              <div style="font-size: 12px; color: #6c757d; text-transform: uppercase; margin-bottom: 5px;">Excess Energy</div>
              <div style="font-size: 24px; font-weight: 700; color: #1e3a8a;">${formatNumber(sections.anomalies.summary.totalExcessKwh, 1)} kWh</div>
            </div>
          </div>
        </div>
        
        ${sections.anomalies.timeline.slice(0, 10).length > 0 ? `
        <table>
          <thead>
            <tr>
              <th>Equipment</th>
              <th>Start Time</th>
              <th>Peak Power</th>
              <th>Excess kWh</th>
              <th>Context</th>
            </tr>
          </thead>
          <tbody>
            ${sections.anomalies.timeline.slice(0, 10).map(event => `
              <tr>
                <td><strong>${event.channelName}</strong></td>
                <td>${new Date(event.start).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}</td>
                <td>${formatNumber(event.peakPower, 2)} kW</td>
                <td>${formatNumber(event.excessKwh, 1)}</td>
                <td>
                  <span class="badge" style="background-color: ${event.context === 'business_hours' ? '#10b981' : '#6366f1'}">
                    ${event.context === 'business_hours' ? 'Business Hours' : 'After Hours'}
                  </span>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
        ` : ''}
      </div>
      ` : ''}
      
      <!-- Spikes -->
      ${sections.spikes.summary.totalEvents > 0 ? `
      <div class="section">
        <h2 class="section-title">⚡ Demand Spikes</h2>
        <p style="margin-bottom: 20px; color: #495057;">
          Peak power events that exceed normal operating levels. These may indicate equipment issues or opportunities for load management.
        </p>
        
        ${sections.spikes.topSpikes.slice(0, 10).length > 0 ? `
        <table>
          <thead>
            <tr>
              <th>Equipment</th>
              <th>Time</th>
              <th>Peak Power</th>
              <th>Duration</th>
              <th>Excess kWh</th>
            </tr>
          </thead>
          <tbody>
            ${sections.spikes.topSpikes.slice(0, 10).map(spike => `
              <tr>
                <td><strong>${spike.channelName}</strong></td>
                <td>${new Date(spike.start).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}</td>
                <td style="color: #dc3545; font-weight: 600;">${formatNumber(spike.peakPower, 2)} kW</td>
                <td>${spike.duration}</td>
                <td>${formatNumber(spike.totalExcessKwh, 1)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
        ` : ''}
      </div>
      ` : ''}
      
      <!-- Data Quality -->
      ${sections.sensorHealth.totalIssues > 0 ? `
      <div class="section">
        <h2 class="section-title">🔧 Data Quality & Sensor Health</h2>
        <p style="margin-bottom: 20px; color: #495057;">
          Monitoring system health and data completeness. Issues may prevent accurate analysis.
        </p>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 4px; margin-bottom: 20px;">
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px;">
            <div>
              <div style="font-size: 12px; color: #6c757d; text-transform: uppercase; margin-bottom: 5px;">Total Issues</div>
              <div style="font-size: 24px; font-weight: 700; color: #dc3545;">${sections.sensorHealth.totalIssues}</div>
            </div>
            <div>
              <div style="font-size: 12px; color: #6c757d; text-transform: uppercase; margin-bottom: 5px;">High Severity</div>
              <div style="font-size: 24px; font-weight: 700; color: #dc3545;">${sections.sensorHealth.bySeverity.high}</div>
            </div>
            <div>
              <div style="font-size: 12px; color: #6c757d; text-transform: uppercase; margin-bottom: 5px;">Medium Severity</div>
              <div style="font-size: 24px; font-weight: 700; color: #fd7e14;">${sections.sensorHealth.bySeverity.medium}</div>
            </div>
            <div>
              <div style="font-size: 12px; color: #6c757d; text-transform: uppercase; margin-bottom: 5px;">Low Severity</div>
              <div style="font-size: 24px; font-weight: 700; color: #ffc107;">${sections.sensorHealth.bySeverity.low}</div>
            </div>
          </div>
        </div>
        
        ${sections.sensorHealth.issues.slice(0, 15).length > 0 ? `
        <table>
          <thead>
            <tr>
              <th>Equipment</th>
              <th>Issue Type</th>
              <th>Severity</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            ${sections.sensorHealth.issues.slice(0, 15).map(issue => `
              <tr>
                <td><strong>${issue.channelName}</strong></td>
                <td style="text-transform: capitalize;">${issue.type.replace(/_/g, ' ')}</td>
                <td>
                  <span class="badge" style="background-color: ${getSeverityColor(issue.severity)}">
                    ${issue.severity}
                  </span>
                </td>
                <td>${issue.description}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
        ` : ''}
      </div>
      ` : ''}
      
    </div>
    
    <!-- Footer -->
    <div class="footer">
      <div class="footer-company">⚡ ARGO ENERGY SOLUTIONS</div>
      <div>Professional Energy Analytics & Optimization Services</div>
      <div style="margin-top: 15px; font-size: 12px;">
        Report ID: ${metadata.site.siteId}-${new Date(metadata.generatedAt).getTime()}<br>
        Generated: ${new Date(metadata.generatedAt).toLocaleString('en-US')}<br>
        Report Version: ${metadata.reportVersion}
      </div>
      <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #dee2e6;">
        This report is confidential and intended solely for ${metadata.site.siteName}.<br>
        For questions about this report, please contact your Argo Energy Solutions representative.
      </div>
    </div>
    
  </div>
</body>
</html>`;
}

/**
 * Save HTML report to file
 */
export function saveHTMLReport(reportData, outputPath) {
  const html = renderHTMLReport(reportData);
  fs.writeFileSync(outputPath, html, 'utf-8');
  return outputPath;
}
