/**
 * Chart Generation Utility
 * Generates chart images using a simple SVG/HTML approach
 * Can be embedded in HTML reports or saved as standalone images
 */

export function generatePowerTimeSeriesChart(readings, anomalies = []) {
  if (!readings || readings.length === 0) return null;
  // Create SVG chart for power over time
  const width = 800;
  const height = 400;
  const padding = { top: 40, right: 40, bottom: 60, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Extract power values and timestamps
  const data = readings.map((r, idx) => ({
    timestamp: parseInt(r.ts),
    power: (r.P || r.kW || 0) / 1000, // Convert to kW
    isAnomaly: anomalies.some(a => a.timestamp === r.ts),
  }));

  if (data.length === 0) return null;

  const powerValues = data.map(d => d.power);
  const minPower = Math.min(...powerValues);
  const maxPower = Math.max(...powerValues);
  const powerRange = maxPower - minPower || 1;

  const timeRange = data[data.length - 1].timestamp - data[0].timestamp;

  // Generate SVG
  let svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">`;
  
  // Background
  svg += `<rect width="${width}" height="${height}" fill="#f9fafb"/>`;
  
  // Chart area
  svg += `<g transform="translate(${padding.left},${padding.top})">`;
  
  // Grid lines
  for (let i = 0; i <= 5; i++) {
    const y = (chartHeight / 5) * i;
    svg += `<line x1="0" y1="${y}" x2="${chartWidth}" y2="${y}" stroke="#e5e7eb" stroke-width="1"/>`;
  }
  
  // Power line
  let path = '';
  data.forEach((point, idx) => {
    const x = (idx / (data.length - 1)) * chartWidth;
    const y = chartHeight - ((point.power - minPower) / powerRange) * chartHeight;
    path += idx === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
  });
  
  svg += `<path d="${path}" fill="none" stroke="#3b82f6" stroke-width="2"/>`;
  
  // Anomaly markers
  data.forEach((point, idx) => {
    if (point.isAnomaly) {
      const x = (idx / (data.length - 1)) * chartWidth;
      const y = chartHeight - ((point.power - minPower) / powerRange) * chartHeight;
      svg += `<circle cx="${x}" cy="${y}" r="4" fill="#ef4444"/>`;
    }
  });
  
  // Labels
  svg += `<text x="${chartWidth / 2}" y="${chartHeight + 40}" text-anchor="middle" font-size="12" fill="#374151">Time</text>`;
  svg += `<text x="-30" y="${chartHeight / 2}" text-anchor="middle" font-size="12" fill="#374151" transform="rotate(-90, -30, ${chartHeight / 2})">Power (kW)</text>`;
  
  svg += `</g></svg>`;
  
  return svg;
}

export function generateVoltageStabilityChart(readings) {
  const width = 800;
  const height = 300;
  const padding = { top: 40, right: 40, bottom: 60, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const data = readings
    .map(r => ({ timestamp: parseInt(r.ts), voltage: r.V }))
    .filter(d => d.voltage !== undefined && !isNaN(d.voltage));

  if (data.length === 0) return null;

  const voltages = data.map(d => d.voltage);
  const minVoltage = Math.min(...voltages);
  const maxVoltage = Math.max(...voltages);
  const avgVoltage = voltages.reduce((a, b) => a + b, 0) / voltages.length;
  const voltageRange = maxVoltage - minVoltage || 1;

  let svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">`;
  svg += `<rect width="${width}" height="${height}" fill="#f9fafb"/>`;
  svg += `<g transform="translate(${padding.left},${padding.top})">`;
  
  // Average line
  const avgY = chartHeight - ((avgVoltage - minVoltage) / voltageRange) * chartHeight;
  svg += `<line x1="0" y1="${avgY}" x2="${chartWidth}" y2="${avgY}" stroke="#10b981" stroke-width="2" stroke-dasharray="5,5"/>`;
  
  // Voltage line
  let path = '';
  data.forEach((point, idx) => {
    const x = (idx / (data.length - 1)) * chartWidth;
    const y = chartHeight - ((point.voltage - minVoltage) / voltageRange) * chartHeight;
    path += idx === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
  });
  
  svg += `<path d="${path}" fill="none" stroke="#8b5cf6" stroke-width="2"/>`;
  
  // Labels
  svg += `<text x="${chartWidth / 2}" y="${chartHeight + 40}" text-anchor="middle" font-size="12" fill="#374151">Time</text>`;
  svg += `<text x="-30" y="${chartHeight / 2}" text-anchor="middle" font-size="12" fill="#374151" transform="rotate(-90, -30, ${chartHeight / 2})">Voltage (V)</text>`;
  svg += `<text x="${chartWidth - 10}" y="${avgY - 5}" text-anchor="end" font-size="10" fill="#10b981">Avg: ${avgVoltage.toFixed(1)}V</text>`;
  
  svg += `</g></svg>`;
  
  return svg;
}

export function generatePowerFactorChart(readings) {
  const width = 800;
  const height = 300;
  const padding = { top: 40, right: 40, bottom: 60, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const data = readings
    .map(r => ({ timestamp: parseInt(r.ts), pf: r.PF }))
    .filter(d => d.pf !== undefined && !isNaN(d.pf));

  if (data.length === 0) return null;

  const pfs = data.map(d => d.pf);
  const minPF = Math.min(...pfs);
  const maxPF = Math.max(...pfs);
  const pfRange = maxPF - minPF || 1;

  let svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">`;
  svg += `<rect width="${width}" height="${height}" fill="#f9fafb"/>`;
  svg += `<g transform="translate(${padding.left},${padding.top})">`;
  
  // Target line (0.85)
  const targetY = chartHeight - ((0.85 - minPF) / pfRange) * chartHeight;
  svg += `<line x1="0" y1="${targetY}" x2="${chartWidth}" y2="${targetY}" stroke="#f59e0b" stroke-width="2" stroke-dasharray="5,5"/>`;
  
  // Power factor line
  let path = '';
  data.forEach((point, idx) => {
    const x = (idx / (data.length - 1)) * chartWidth;
    const y = chartHeight - ((point.pf - minPF) / pfRange) * chartHeight;
    path += idx === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
  });
  
  svg += `<path d="${path}" fill="none" stroke="#ef4444" stroke-width="2"/>`;
  
  // Labels
  svg += `<text x="${chartWidth / 2}" y="${chartHeight + 40}" text-anchor="middle" font-size="12" fill="#374151">Time</text>`;
  svg += `<text x="-30" y="${chartHeight / 2}" text-anchor="middle" font-size="12" fill="#374151" transform="rotate(-90, -30, ${chartHeight / 2})">Power Factor</text>`;
  svg += `<text x="${chartWidth - 10}" y="${targetY - 5}" text-anchor="end" font-size="10" fill="#f59e0b">Target: 0.85</text>`;
  
  svg += `</g></svg>`;
  
  return svg;
}

export function generateDailyPatternChart(readings) {
  if (!readings || readings.length === 0) return null;
  
  // Group by hour of day
  const hourlyData = {};
  
  readings.forEach(r => {
    const date = new Date(parseInt(r.ts) * 1000);
    const hour = date.getHours();
    if (!hourlyData[hour]) {
      hourlyData[hour] = { count: 0, total: 0 };
    }
    hourlyData[hour].total += (r.P || r.kW || 0) / 1000;
    hourlyData[hour].count++;
  });

  const hours = Array.from({ length: 24 }, (_, i) => i);
  const avgPowerByHour = hours.map(h => {
    const data = hourlyData[h];
    return data ? data.total / data.count : 0;
  });

  const maxPower = Math.max(...avgPowerByHour) || 1;

  const width = 800;
  const height = 300;
  const padding = { top: 40, right: 40, bottom: 60, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const barWidth = chartWidth / 24;

  let svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">`;
  svg += `<rect width="${width}" height="${height}" fill="#f9fafb"/>`;
  svg += `<g transform="translate(${padding.left},${padding.top})">`;
  
  // Bars
  avgPowerByHour.forEach((power, hour) => {
    const barHeight = (power / maxPower) * chartHeight;
    const x = hour * barWidth;
    const y = chartHeight - barHeight;
    
    svg += `<rect x="${x}" y="${y}" width="${barWidth - 2}" height="${barHeight}" fill="#3b82f6" opacity="0.8"/>`;
    
    // Hour labels (every 3 hours)
    if (hour % 3 === 0) {
      svg += `<text x="${x + barWidth / 2}" y="${chartHeight + 20}" text-anchor="middle" font-size="10" fill="#374151">${hour}:00</text>`;
    }
  });
  
  // Labels
  svg += `<text x="${chartWidth / 2}" y="${chartHeight + 40}" text-anchor="middle" font-size="12" fill="#374151">Hour of Day</text>`;
  svg += `<text x="-30" y="${chartHeight / 2}" text-anchor="middle" font-size="12" fill="#374151" transform="rotate(-90, -30, ${chartHeight / 2})">Average Power (kW)</text>`;
  
  svg += `</g></svg>`;
  
  return svg;
}
