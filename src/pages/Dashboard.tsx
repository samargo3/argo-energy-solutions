import { useState } from 'react'
import { useCustomers } from '../hooks/useCustomerData'
import { useGroupedEnergyData } from '../hooks/useEnergyData'
import { calculateEnergyStatistics } from '../services/analytics/statistics'
import { getDateRange } from '../utils/dateUtils'
import EnergyChart from '../components/charts/EnergyChart'
import StatsCard from '../components/common/StatsCard'
import './Dashboard.css'

export default function Dashboard() {
  const [dateRange, setDateRange] = useState(getDateRange('month'))
  const [selectedCustomer, setSelectedCustomer] = useState<string | null>(null)
  
  const { data: customersData, isLoading: customersLoading } = useCustomers()
  const { data: energyData, isLoading: energyLoading } = useGroupedEnergyData(
    selectedCustomer || customersData?.items[0]?.id || '',
    { ...dateRange, groupBy: 'day' }
  )

  const customers = customersData?.items || []
  const stats = energyData ? calculateEnergyStatistics(
    energyData.map(d => ({
      id: d.date,
      siteId: '',
      customerId: selectedCustomer || '',
      timestamp: d.date,
      value: d.value,
      cost: d.cost,
    })),
    dateRange.startDate,
    dateRange.endDate
  ) : null

  return (
    <div className="dashboard">
      <div className="container">
        <h1 className="dashboard-title">Energy Dashboard</h1>
        
        <div className="dashboard-controls">
          <div className="control-group">
            <label>Customer:</label>
            <select 
              value={selectedCustomer || customers[0]?.id || ''} 
              onChange={(e) => setSelectedCustomer(e.target.value)}
              disabled={customersLoading}
            >
              {customers.map(customer => (
                <option key={customer.id} value={customer.id}>
                  {customer.name}
                </option>
              ))}
            </select>
          </div>
          <div className="control-group">
            <label>Period:</label>
            <select 
              onChange={(e) => {
                const period = e.target.value as 'today' | 'week' | 'month' | 'year'
                setDateRange(getDateRange(period))
              }}
            >
              <option value="month">Last Month</option>
              <option value="today">Today</option>
              <option value="week">Last Week</option>
              <option value="year">Last Year</option>
            </select>
          </div>
        </div>

        {energyLoading ? (
          <div className="loading">Loading energy data...</div>
        ) : (
          <>
            {stats && (
              <div className="stats-grid">
                <StatsCard
                  title="Total Consumption"
                  value={`${stats.totalConsumption.toFixed(2)} kWh`}
                  subtitle={`Average: ${stats.averageConsumption.toFixed(2)} kWh`}
                />
                <StatsCard
                  title="Peak Consumption"
                  value={`${stats.peakConsumption.toFixed(2)} kWh`}
                  subtitle={stats.peakTimestamp ? new Date(stats.peakTimestamp).toLocaleDateString() : ''}
                />
                {stats.cost && (
                  <StatsCard
                    title="Total Cost"
                    value={`$${stats.cost.toFixed(2)}`}
                    subtitle={`Average: $${stats.averageCost?.toFixed(2)}`}
                  />
                )}
              </div>
            )}

            {energyData && energyData.length > 0 && (
              <div className="chart-container">
                <EnergyChart data={energyData} />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

