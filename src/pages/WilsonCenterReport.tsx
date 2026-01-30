import { useState } from 'react';
import { useEniscopeChannelReadings, type ChannelReading } from '../hooks/useEniscopeChannel';
import { detectAnomalies, type AnomalyAnalysis } from '../services/analytics/anomalyDetection';
import { formatDisplayDate, formatDateTime } from '../utils/dateUtils';
import { format, subDays, subWeeks, subMonths } from 'date-fns';
import './WilsonCenterReport.css';

// Wilson Center channels from documentation
const WILSON_CENTER_CHANNELS = [
  { id: '162320', name: 'RTU-1_WCDS_Wilson Ctr', category: 'HVAC - RTU' },
  { id: '162119', name: 'RTU-2_WCDS_Wilson Ctr', category: 'HVAC - RTU' },
  { id: '162120', name: 'RTU-3_WCDS_Wilson Ctr', category: 'HVAC - RTU' },
  { id: '162122', name: 'AHU-1A_WCDS_Wilson Ctr', category: 'HVAC - AHU' },
  { id: '162123', name: 'AHU-1B_WCDS_Wilson Ctr', category: 'HVAC - AHU' },
  { id: '162121', name: 'AHU-2_WCDS_Wilson Ctr', category: 'HVAC - AHU' },
  { id: '162285', name: 'CDPK_Kitchen Main Panel(s)_WCDS_Wilson Ctr', category: 'Electrical Panel' },
  { id: '162319', name: 'CDKH_Kitchen Panel(small)_WCDS_Wilson Ctr', category: 'Electrical Panel' },
  { id: '162277', name: 'Air Sense_Main Kitchen_WCDS_Wilson', category: 'Environmental Sensor' },
];

export default function WilsonCenterReport() {
  const [selectedChannelId, setSelectedChannelId] = useState<string>(WILSON_CENTER_CHANNELS[0].id);
  const [startDate, setStartDate] = useState<Date>(subDays(new Date(), 7));
  const [endDate, setEndDate] = useState<Date>(new Date());
  const [resolution, setResolution] = useState<'60' | '900' | '1800' | '3600' | '86400'>('3600');

  const selectedChannel = WILSON_CENTER_CHANNELS.find((ch) => ch.id === selectedChannelId);

  const { data: readings, isLoading, error } = useEniscopeChannelReadings({
    channelId: selectedChannelId,
    startDate,
    endDate,
    resolution,
  });

  // Analyze for anomalies
  const anomalyAnalysis: AnomalyAnalysis | null = readings ? detectAnomalies(readings) : null;

  // Calculate statistics
  const stats = readings && readings.length > 0 ? {
    totalEnergy: readings.reduce((sum, r) => sum + r.energy, 0),
    avgPower: readings.reduce((sum, r) => sum + r.power, 0) / readings.length,
    peakPower: Math.max(...readings.map((r) => r.power)),
    minPower: Math.min(...readings.map((r) => r.power)),
    avgVoltage: readings.filter((r) => r.voltage).reduce((sum, r) => sum + (r.voltage || 0), 0) / readings.filter((r) => r.voltage).length,
    avgPowerFactor: readings.filter((r) => r.powerFactor).reduce((sum, r) => sum + (r.powerFactor || 0), 0) / readings.filter((r) => r.powerFactor).length,
    dataPoints: readings.length,
  } : null;

  const handleQuickRange = (days: number) => {
    setEndDate(new Date());
    setStartDate(subDays(new Date(), days));
  };

  const getHealthColor = (health: AnomalyAnalysis['equipmentHealth']) => {
    switch (health) {
      case 'excellent': return '#10b981';
      case 'good': return '#3b82f6';
      case 'fair': return '#f59e0b';
      case 'poor': return '#ef4444';
      case 'critical': return '#dc2626';
      default: return '#6b7280';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return '#dc2626';
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#3b82f6';
      default: return '#6b7280';
    }
  };

  return (
    <div className="wilson-center-report">
      <div className="container">
        <h1 className="page-title">Wilson Center Equipment Report</h1>
        <p className="page-subtitle">Analyze equipment performance and detect anomalies</p>

        {/* Controls */}
        <div className="report-controls">
          <div className="control-group">
            <label htmlFor="channel-select">Select Unit:</label>
            <select
              id="channel-select"
              value={selectedChannelId}
              onChange={(e) => setSelectedChannelId(e.target.value)}
              className="form-select"
            >
              {WILSON_CENTER_CHANNELS.map((channel) => (
                <option key={channel.id} value={channel.id}>
                  {channel.name} ({channel.category})
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label htmlFor="start-date">Start Date:</label>
            <input
              id="start-date"
              type="datetime-local"
              value={format(startDate, "yyyy-MM-dd'T'HH:mm")}
              onChange={(e) => setStartDate(new Date(e.target.value))}
              className="form-input"
            />
          </div>

          <div className="control-group">
            <label htmlFor="end-date">End Date:</label>
            <input
              id="end-date"
              type="datetime-local"
              value={format(endDate, "yyyy-MM-dd'T'HH:mm")}
              onChange={(e) => setEndDate(new Date(e.target.value))}
              className="form-input"
            />
          </div>

          <div className="control-group">
            <label htmlFor="resolution">Resolution:</label>
            <select
              id="resolution"
              value={resolution}
              onChange={(e) => setResolution(e.target.value as typeof resolution)}
              className="form-select"
            >
              <option value="60">1 minute</option>
              <option value="900">15 minutes</option>
              <option value="1800">30 minutes</option>
              <option value="3600">1 hour</option>
              <option value="86400">1 day</option>
            </select>
          </div>
        </div>

        {/* Quick Range Buttons */}
        <div className="quick-range-buttons">
          <button onClick={() => handleQuickRange(1)} className="btn btn-secondary">Today</button>
          <button onClick={() => handleQuickRange(7)} className="btn btn-secondary">Last 7 Days</button>
          <button onClick={() => handleQuickRange(30)} className="btn btn-secondary">Last 30 Days</button>
          <button onClick={() => handleQuickRange(90)} className="btn btn-secondary">Last 90 Days</button>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading data from Eniscope API...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="error-state">
            <h3>Error Loading Data</h3>
            <p>{error instanceof Error ? error.message : 'Failed to load data'}</p>
            <p className="error-hint">
              Make sure your Eniscope API credentials are configured in your .env file.
            </p>
          </div>
        )}

        {/* Results */}
        {readings && readings.length > 0 && stats && anomalyAnalysis && (
          <>
            {/* Summary Cards */}
            <div className="summary-cards">
              <div className="summary-card">
                <h3>Equipment Health</h3>
                <div className="health-indicator" style={{ color: getHealthColor(anomalyAnalysis.equipmentHealth) }}>
                  <span className="health-badge">{anomalyAnalysis.equipmentHealth.toUpperCase()}</span>
                </div>
              </div>

              <div className="summary-card">
                <h3>Total Energy</h3>
                <p className="stat-value">{stats.totalEnergy.toFixed(2)} kWh</p>
              </div>

              <div className="summary-card">
                <h3>Average Power</h3>
                <p className="stat-value">{stats.avgPower.toFixed(2)} kW</p>
              </div>

              <div className="summary-card">
                <h3>Peak Power</h3>
                <p className="stat-value">{stats.peakPower.toFixed(2)} kW</p>
              </div>

              <div className="summary-card">
                <h3>Data Points</h3>
                <p className="stat-value">{stats.dataPoints.toLocaleString()}</p>
              </div>

              {stats.avgVoltage && !isNaN(stats.avgVoltage) && (
                <div className="summary-card">
                  <h3>Avg Voltage</h3>
                  <p className="stat-value">{stats.avgVoltage.toFixed(1)} V</p>
                </div>
              )}

              {stats.avgPowerFactor && !isNaN(stats.avgPowerFactor) && (
                <div className="summary-card">
                  <h3>Power Factor</h3>
                  <p className="stat-value">{stats.avgPowerFactor.toFixed(3)}</p>
                  {stats.avgPowerFactor < 0.85 && (
                    <span className="warning-badge">⚠️ Low</span>
                  )}
                </div>
              )}
            </div>

            {/* Anomaly Summary */}
            {anomalyAnalysis.summary.totalAnomalies > 0 && (
              <div className="anomaly-summary">
                <h2>Anomaly Detection Summary</h2>
                <div className="anomaly-stats">
                  <div className="anomaly-stat">
                    <span className="anomaly-count critical">{anomalyAnalysis.summary.critical}</span>
                    <span className="anomaly-label">Critical</span>
                  </div>
                  <div className="anomaly-stat">
                    <span className="anomaly-count high">{anomalyAnalysis.summary.high}</span>
                    <span className="anomaly-label">High</span>
                  </div>
                  <div className="anomaly-stat">
                    <span className="anomaly-count medium">{anomalyAnalysis.summary.medium}</span>
                    <span className="anomaly-label">Medium</span>
                  </div>
                  <div className="anomaly-stat">
                    <span className="anomaly-count low">{anomalyAnalysis.summary.low}</span>
                    <span className="anomaly-label">Low</span>
                  </div>
                </div>
              </div>
            )}

            {/* Recommendations */}
            {anomalyAnalysis.recommendations.length > 0 && (
              <div className="recommendations-section">
                <h2>Recommendations</h2>
                <ul className="recommendations-list">
                  {anomalyAnalysis.recommendations.map((rec, idx) => (
                    <li key={idx}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Anomalies List */}
            {anomalyAnalysis.anomalies.length > 0 && (
              <div className="anomalies-section">
                <h2>Detected Anomalies</h2>
                <div className="anomalies-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Severity</th>
                        <th>Type</th>
                        <th>Timestamp</th>
                        <th>Value</th>
                        <th>Description</th>
                        <th>Recommendation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {anomalyAnalysis.anomalies.map((anomaly, idx) => (
                        <tr key={idx}>
                          <td>
                            <span
                              className="severity-badge"
                              style={{ backgroundColor: getSeverityColor(anomaly.severity) }}
                            >
                              {anomaly.severity}
                            </span>
                          </td>
                          <td>{anomaly.type.replace(/_/g, ' ')}</td>
                          <td>{formatDateTime(anomaly.timestamp)}</td>
                          <td>{anomaly.value.toFixed(2)}</td>
                          <td>{anomaly.description}</td>
                          <td>{anomaly.recommendation || 'N/A'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* No Anomalies Message */}
            {anomalyAnalysis.anomalies.length === 0 && (
              <div className="no-anomalies">
                <h2>✅ No Anomalies Detected</h2>
                <p>Equipment appears to be operating normally during the selected time period.</p>
              </div>
            )}

            {/* Detailed Statistics */}
            <div className="detailed-stats">
              <h2>Detailed Statistics</h2>
              <div className="stats-grid">
                <div className="stat-item">
                  <label>Time Period:</label>
                  <span>{formatDisplayDate(startDate)} - {formatDisplayDate(endDate)}</span>
                </div>
                <div className="stat-item">
                  <label>Channel:</label>
                  <span>{selectedChannel?.name}</span>
                </div>
                <div className="stat-item">
                  <label>Category:</label>
                  <span>{selectedChannel?.category}</span>
                </div>
                <div className="stat-item">
                  <label>Min Power:</label>
                  <span>{stats.minPower.toFixed(2)} kW</span>
                </div>
                <div className="stat-item">
                  <label>Peak Power:</label>
                  <span>{stats.peakPower.toFixed(2)} kW</span>
                </div>
                <div className="stat-item">
                  <label>Average Power:</label>
                  <span>{stats.avgPower.toFixed(2)} kW</span>
                </div>
              </div>
            </div>
          </>
        )}

        {/* No Data Message */}
        {readings && readings.length === 0 && !isLoading && (
          <div className="no-data">
            <h3>No Data Available</h3>
            <p>No readings found for the selected unit and time period.</p>
            <p className="hint">Try selecting a different date range or unit.</p>
          </div>
        )}
      </div>
    </div>
  );
}
