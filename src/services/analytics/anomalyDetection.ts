import type { ChannelReading } from '../../hooks/useEniscopeChannel';

export interface Anomaly {
  type: 'power_spike' | 'power_drop' | 'voltage_anomaly' | 'power_factor_issue' | 'zero_reading' | 'unusual_pattern';
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
  value: number;
  expectedValue?: number;
  description: string;
  recommendation?: string;
}

export interface AnomalyAnalysis {
  anomalies: Anomaly[];
  summary: {
    totalAnomalies: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  equipmentHealth: 'excellent' | 'good' | 'fair' | 'poor' | 'critical';
  recommendations: string[];
}

/**
 * Detect anomalies in channel readings
 */
export const detectAnomalies = (readings: ChannelReading[]): AnomalyAnalysis => {
  if (readings.length === 0) {
    return {
      anomalies: [],
      summary: { totalAnomalies: 0, critical: 0, high: 0, medium: 0, low: 0 },
      equipmentHealth: 'excellent',
      recommendations: ['No data available for analysis'],
    };
  }

  const anomalies: Anomaly[] = [];
  const powerValues = readings.map((r) => r.power).filter((p) => p !== undefined && !isNaN(p)) as number[];
  const voltageValues = readings.map((r) => r.voltage).filter((v) => v !== undefined && !isNaN(v)) as number[];
  const pfValues = readings.map((r) => r.powerFactor).filter((pf) => pf !== undefined && !isNaN(pf)) as number[];

  // Calculate statistics
  const avgPower = powerValues.reduce((sum, p) => sum + p, 0) / powerValues.length;
  const powerStdDev = Math.sqrt(
    powerValues.reduce((sum, p) => sum + Math.pow(p - avgPower, 2), 0) / powerValues.length
  );

  const avgVoltage = voltageValues.length > 0
    ? voltageValues.reduce((sum, v) => sum + v, 0) / voltageValues.length
    : null;
  const avgPF = pfValues.length > 0
    ? pfValues.reduce((sum, pf) => sum + pf, 0) / pfValues.length
    : null;

  // Detect power spikes (3+ standard deviations)
  readings.forEach((reading) => {
    if (reading.power !== undefined && !isNaN(reading.power)) {
      const zScore = Math.abs((reading.power - avgPower) / (powerStdDev || 1));
      
      if (zScore > 4) {
        anomalies.push({
          type: 'power_spike',
          severity: 'critical',
          timestamp: reading.timestamp,
          value: reading.power,
          expectedValue: avgPower,
          description: `Critical power spike detected: ${reading.power.toFixed(2)} kW (expected ~${avgPower.toFixed(2)} kW)`,
          recommendation: 'Check for equipment malfunction, short circuit, or sudden load increase. Inspect equipment immediately.',
        });
      } else if (zScore > 3) {
        anomalies.push({
          type: 'power_spike',
          severity: 'high',
          timestamp: reading.timestamp,
          value: reading.power,
          expectedValue: avgPower,
          description: `Significant power spike: ${reading.power.toFixed(2)} kW`,
          recommendation: 'Monitor equipment and investigate cause of increased load.',
        });
      }
    }
  });

  // Detect power drops (equipment off when should be on, or significant drops)
  const nonZeroPower = powerValues.filter((p) => p > 0.01);
  const avgNonZeroPower = nonZeroPower.length > 0
    ? nonZeroPower.reduce((sum, p) => sum + p, 0) / nonZeroPower.length
    : 0;

  readings.forEach((reading, index) => {
    if (reading.power !== undefined && !isNaN(reading.power)) {
      // Check for sudden drops (more than 50% from previous reading)
      if (index > 0) {
        const prevPower = readings[index - 1].power || 0;
        if (prevPower > 0.1 && reading.power < prevPower * 0.5 && reading.power < 0.1) {
          anomalies.push({
            type: 'power_drop',
            severity: 'medium',
            timestamp: reading.timestamp,
            value: reading.power,
            expectedValue: prevPower,
            description: `Sudden power drop detected: ${reading.power.toFixed(2)} kW (from ${prevPower.toFixed(2)} kW)`,
            recommendation: 'Check if equipment shut down unexpectedly or if there was a power interruption.',
          });
        }
      }

      // Check for zero readings when equipment should be running
      if (reading.power < 0.01 && avgNonZeroPower > 0.1) {
        // Check if surrounding readings suggest equipment should be on
        const contextWindow = readings.slice(Math.max(0, index - 3), Math.min(readings.length, index + 4));
        const contextAvg = contextWindow
          .map((r) => r.power || 0)
          .filter((p) => p > 0.01)
          .reduce((sum, p) => sum + p, 0) / contextWindow.length;

        if (contextAvg > 0.1) {
          anomalies.push({
            type: 'zero_reading',
            severity: 'medium',
            timestamp: reading.timestamp,
            value: reading.power,
            expectedValue: contextAvg,
            description: `Unexpected zero power reading (equipment may be offline)`,
            recommendation: 'Verify equipment status and sensor connectivity.',
          });
        }
      }
    }
  });

  // Detect voltage anomalies
  if (avgVoltage !== null) {
    readings.forEach((reading) => {
      if (reading.voltage !== undefined && !isNaN(reading.voltage)) {
        const voltageDeviation = Math.abs(reading.voltage - avgVoltage);
        const voltagePercentDeviation = (voltageDeviation / avgVoltage) * 100;

        if (voltagePercentDeviation > 10) {
          anomalies.push({
            type: 'voltage_anomaly',
            severity: voltagePercentDeviation > 15 ? 'high' : 'medium',
            timestamp: reading.timestamp,
            value: reading.voltage,
            expectedValue: avgVoltage,
            description: `Voltage anomaly: ${reading.voltage.toFixed(1)} V (expected ~${avgVoltage.toFixed(1)} V, ${voltagePercentDeviation.toFixed(1)}% deviation)`,
            recommendation: 'Check power quality, potential issues with electrical supply or equipment.',
          });
        }
      }
    });
  }

  // Detect power factor issues
  if (avgPF !== null) {
    readings.forEach((reading) => {
      if (reading.powerFactor !== undefined && !isNaN(reading.powerFactor)) {
        if (reading.powerFactor < 0.5) {
          anomalies.push({
            type: 'power_factor_issue',
            severity: 'high',
            timestamp: reading.timestamp,
            value: reading.powerFactor,
            expectedValue: 0.85,
            description: `Very low power factor: ${reading.powerFactor.toFixed(3)} (target: >0.85)`,
            recommendation: 'Investigate motor issues, consider power factor correction equipment.',
          });
        } else if (reading.powerFactor < 0.7 && reading.power > 0.1) {
          anomalies.push({
            type: 'power_factor_issue',
            severity: 'medium',
            timestamp: reading.timestamp,
            value: reading.powerFactor,
            expectedValue: 0.85,
            description: `Low power factor: ${reading.powerFactor.toFixed(3)}`,
            recommendation: 'Consider power factor correction to reduce reactive power penalties.',
          });
        }
      }
    });
  }

  // Detect unusual patterns (e.g., equipment running at unusual times)
  // This is a simplified check - could be enhanced with ML
  const hourPatterns: Record<number, number[]> = {};
  readings.forEach((reading) => {
    const date = new Date(reading.timestamp);
    const hour = date.getHours();
    if (!hourPatterns[hour]) hourPatterns[hour] = [];
    if (reading.power > 0.1) hourPatterns[hour].push(reading.power);
  });

  // Calculate summary
  const summary = {
    totalAnomalies: anomalies.length,
    critical: anomalies.filter((a) => a.severity === 'critical').length,
    high: anomalies.filter((a) => a.severity === 'high').length,
    medium: anomalies.filter((a) => a.severity === 'medium').length,
    low: anomalies.filter((a) => a.severity === 'low').length,
  };

  // Determine equipment health
  let equipmentHealth: AnomalyAnalysis['equipmentHealth'] = 'excellent';
  if (summary.critical > 0 || summary.high > 5) {
    equipmentHealth = 'critical';
  } else if (summary.high > 2 || summary.medium > 10) {
    equipmentHealth = 'poor';
  } else if (summary.medium > 5 || summary.totalAnomalies > 15) {
    equipmentHealth = 'fair';
  } else if (summary.totalAnomalies > 5) {
    equipmentHealth = 'good';
  }

  // Generate recommendations
  const recommendations: string[] = [];
  
  if (summary.critical > 0) {
    recommendations.push('🔴 CRITICAL: Immediate equipment inspection required');
  }
  
  if (summary.high > 0) {
    recommendations.push('⚠️ High priority: Schedule maintenance check');
  }
  
  const pfIssues = anomalies.filter((a) => a.type === 'power_factor_issue').length;
  if (pfIssues > 0) {
    recommendations.push('💡 Consider power factor correction equipment');
  }
  
  const voltageIssues = anomalies.filter((a) => a.type === 'voltage_anomaly').length;
  if (voltageIssues > 0) {
    recommendations.push('⚡ Review power quality and electrical supply');
  }
  
  if (summary.totalAnomalies === 0) {
    recommendations.push('✅ No significant anomalies detected - equipment operating normally');
  }

  return {
    anomalies: anomalies.sort((a, b) => {
      const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
      return severityOrder[b.severity] - severityOrder[a.severity];
    }),
    summary,
    equipmentHealth,
    recommendations,
  };
};
