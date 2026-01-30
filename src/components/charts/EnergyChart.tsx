import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import type { EnergyConsumptionGrouped } from '../../types'
import { formatDisplayDate } from '../../utils/dateUtils'
import './EnergyChart.css'

interface EnergyChartProps {
  data: EnergyConsumptionGrouped[]
}

export default function EnergyChart({ data }: EnergyChartProps) {
  const chartData = data.map(item => ({
    date: formatDisplayDate(item.date, 'MMM dd'),
    consumption: item.value,
    cost: item.cost || 0,
  }))

  return (
    <div className="energy-chart">
      <h3 className="chart-title">Energy Consumption Over Time</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis 
            yAxisId="left"
            label={{ value: 'Consumption (kWh)', angle: -90, position: 'insideLeft' }}
          />
          <YAxis 
            yAxisId="right" 
            orientation="right"
            label={{ value: 'Cost ($)', angle: 90, position: 'insideRight' }}
          />
          <Tooltip />
          <Legend />
          <Line 
            yAxisId="left"
            type="monotone" 
            dataKey="consumption" 
            stroke="#2563eb" 
            strokeWidth={2}
            name="Consumption (kWh)"
            dot={{ r: 3 }}
          />
          <Line 
            yAxisId="right"
            type="monotone" 
            dataKey="cost" 
            stroke="#10b981" 
            strokeWidth={2}
            name="Cost ($)"
            dot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

