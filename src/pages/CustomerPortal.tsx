import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useCustomer } from '../hooks/useCustomerData'
import { useGroupedEnergyData } from '../hooks/useEnergyData'
import { getDateRange } from '../utils/dateUtils'
import EnergyChart from '../components/charts/EnergyChart'
import StatsCard from '../components/common/StatsCard'
import { calculateEnergyStatistics } from '../services/analytics/statistics'
import './CustomerPortal.css'

export default function CustomerPortal() {
  const { id } = useParams<{ id: string }>()
  const [dateRange, setDateRange] = useState(getDateRange('month'))

  const { data: customer, isLoading: customerLoading } = useCustomer(id || '')
  const { data: energyData, isLoading: energyLoading } = useGroupedEnergyData(
    id || '',
    { ...dateRange, groupBy: 'day' }
  )

  const stats = energyData ? calculateEnergyStatistics(
    energyData.map(d => ({
      id: d.date,
      siteId: '',
      customerId: id || '',
      timestamp: d.date,
      value: d.value,
      cost: d.cost,
    })),
    dateRange.startDate,
    dateRange.endDate
  ) : null

  if (customerLoading) {
    return (
      <div className="customer-portal">
        <div className="container">
          <div className="loading">Loading customer data...</div>
        </div>
      </div>
    )
  }

  if (!customer) {
    return (
      <div className="customer-portal">
        <div className="container">
          <div className="error">Customer not found</div>
        </div>
      </div>
    )
  }

  return (
    <div className="customer-portal">
      <div className="container">
        <div className="customer-header">
          <h1 className="customer-name">{customer.name}</h1>
          {customer.email && <p className="customer-email">{customer.email}</p>}
        </div>

        <div className="dashboard-controls">
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

