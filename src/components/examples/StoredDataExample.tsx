/**
 * Example component showing how to use stored energy data
 * 
 * This demonstrates the useStoredEnergyData hooks for accessing
 * locally stored SQLite data instead of making API calls.
 */

import { useStoredChannels, useStoredAggregatedReadings, useStoredEnergyStatistics } from '../../hooks/useStoredEnergyData';
import { useState } from 'react';

export function StoredDataExample() {
  const [selectedChannelId, setSelectedChannelId] = useState<number | null>(null);
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });

  // Fetch all channels
  const { data: channels, isLoading: channelsLoading } = useStoredChannels();

  // Fetch aggregated readings for selected channel
  const { data: dailyReadings, isLoading: readingsLoading } = useStoredAggregatedReadings(
    selectedChannelId,
    `${dateRange.start}T00:00:00Z`,
    `${dateRange.end}T23:59:59Z`,
    'day'
  );

  // Fetch statistics for selected channel
  const { data: statistics, isLoading: statsLoading } = useStoredEnergyStatistics(
    selectedChannelId,
    `${dateRange.start}T00:00:00Z`,
    `${dateRange.end}T23:59:59Z`
  );

  return (
    <div style={{ padding: '20px' }}>
      <h2>Stored Energy Data Example</h2>
      <p>This component uses data from the local SQLite database instead of making API calls.</p>

      {/* Channel Selection */}
      <div style={{ marginBottom: '20px' }}>
        <label>
          Select Channel:
          <select
            value={selectedChannelId || ''}
            onChange={(e) => setSelectedChannelId(e.target.value ? Number(e.target.value) : null)}
            style={{ marginLeft: '10px', padding: '5px' }}
          >
            <option value="">-- Select a channel --</option>
            {channelsLoading ? (
              <option>Loading channels...</option>
            ) : (
              channels?.map((channel) => (
                <option key={channel.channel_id} value={channel.channel_id}>
                  {channel.channel_name} ({channel.organization_name})
                </option>
              ))
            )}
          </select>
        </label>
      </div>

      {/* Date Range Selection */}
      <div style={{ marginBottom: '20px' }}>
        <label>
          Start Date:
          <input
            type="date"
            value={dateRange.start}
            onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
            style={{ marginLeft: '10px', marginRight: '20px', padding: '5px' }}
          />
        </label>
        <label>
          End Date:
          <input
            type="date"
            value={dateRange.end}
            onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
            style={{ marginLeft: '10px', padding: '5px' }}
          />
        </label>
      </div>

      {/* Statistics Display */}
      {selectedChannelId && (
        <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f5f5f5', borderRadius: '5px' }}>
          <h3>Energy Statistics</h3>
          {statsLoading ? (
            <p>Loading statistics...</p>
          ) : statistics ? (
            <div>
              <p><strong>Total Energy:</strong> {statistics.total_energy_kwh.toFixed(2)} kWh</p>
              <p><strong>Average Power:</strong> {statistics.average_power_kw.toFixed(2)} kW</p>
              <p><strong>Peak Power:</strong> {statistics.peak_power_kw.toFixed(2)} kW</p>
              <p><strong>Min Power:</strong> {statistics.min_power_kw.toFixed(2)} kW</p>
              <p><strong>Average Voltage:</strong> {statistics.average_voltage_v.toFixed(2)} V</p>
              <p><strong>Total Readings:</strong> {statistics.count.toLocaleString()}</p>
              {statistics.peak_timestamp && (
                <p><strong>Peak Time:</strong> {new Date(statistics.peak_timestamp).toLocaleString()}</p>
              )}
            </div>
          ) : (
            <p>No statistics available</p>
          )}
        </div>
      )}

      {/* Daily Readings Table */}
      {selectedChannelId && (
        <div>
          <h3>Daily Energy Consumption</h3>
          {readingsLoading ? (
            <p>Loading readings...</p>
          ) : dailyReadings && dailyReadings.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#e0e0e0' }}>
                  <th style={{ padding: '10px', textAlign: 'left', border: '1px solid #ccc' }}>Date</th>
                  <th style={{ padding: '10px', textAlign: 'right', border: '1px solid #ccc' }}>Total Energy (kWh)</th>
                  <th style={{ padding: '10px', textAlign: 'right', border: '1px solid #ccc' }}>Avg Power (kW)</th>
                  <th style={{ padding: '10px', textAlign: 'right', border: '1px solid #ccc' }}>Peak Power (kW)</th>
                  <th style={{ padding: '10px', textAlign: 'right', border: '1px solid #ccc' }}>Readings</th>
                </tr>
              </thead>
              <tbody>
                {dailyReadings.map((reading, index) => (
                  <tr key={index} style={{ backgroundColor: index % 2 === 0 ? '#fff' : '#f9f9f9' }}>
                    <td style={{ padding: '10px', border: '1px solid #ccc' }}>{reading.period}</td>
                    <td style={{ padding: '10px', textAlign: 'right', border: '1px solid #ccc' }}>
                      {reading.total_energy_kwh.toFixed(2)}
                    </td>
                    <td style={{ padding: '10px', textAlign: 'right', border: '1px solid #ccc' }}>
                      {reading.average_power_kw.toFixed(2)}
                    </td>
                    <td style={{ padding: '10px', textAlign: 'right', border: '1px solid #ccc' }}>
                      {reading.peak_power_kw.toFixed(2)}
                    </td>
                    <td style={{ padding: '10px', textAlign: 'right', border: '1px solid #ccc' }}>
                      {reading.count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No readings available for the selected date range.</p>
          )}
        </div>
      )}

      {/* Info Note */}
      <div style={{ marginTop: '30px', padding: '15px', backgroundColor: '#e3f2fd', borderRadius: '5px' }}>
        <p><strong>Note:</strong> This component requires the SQLite database to be set up and populated.</p>
        <p>Run <code>npm run ingest:full</code> to populate the database with data.</p>
        <p>Run <code>npm run db:check</code> to verify the database status.</p>
      </div>
    </div>
  );
}
