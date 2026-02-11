import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts'

interface ForecastProps {
  data: Array<{ timestamp: string; predicted_kwh: number; lower_bound: number; upper_bound: number }>
  dailySummary?: Array<{ date: string; predicted_kwh: number; peak_hour_kwh: number }>
}

function formatDate(ts: string) {
  const d = new Date(ts)
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

function formatTime(ts: string) {
  const d = new Date(ts)
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

export default function ForecastChart({ data, dailySummary }: ForecastProps) {
  // Show daily aggregates if available, otherwise hourly
  if (dailySummary && dailySummary.length > 0) {
    const chartData = dailySummary.map((d) => ({
      date: formatDate(d.date + 'T12:00:00'),
      'Predicted kWh': Number(d.predicted_kwh.toFixed(0)),
      'Peak Hour kW': Number(d.peak_hour_kwh.toFixed(1)),
    }))

    return (
      <div style={{ width: '100%', height: 320 }}>
        <ResponsiveContainer>
          <AreaChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }}
              label={{ value: 'kWh', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
            />
            <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #e5e7eb', fontSize: 13 }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Area
              type="monotone"
              dataKey="Predicted kWh"
              stroke="#8b5cf6"
              fill="#8b5cf6"
              fillOpacity={0.15}
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    )
  }

  // Hourly view with confidence bands (sample every 4 hours for readability)
  const sampled = data.filter((_, i) => i % 4 === 0)
  const chartData = sampled.map((d) => ({
    time: formatTime(d.timestamp),
    Predicted: Number(d.predicted_kwh.toFixed(1)),
    Lower: Number(d.lower_bound.toFixed(1)),
    Upper: Number(d.upper_bound.toFixed(1)),
  }))

  return (
    <div style={{ width: '100%', height: 320 }}>
      <ResponsiveContainer>
        <AreaChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="time" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }}
            label={{ value: 'kWh', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
          />
          <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #e5e7eb', fontSize: 13 }} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Area type="monotone" dataKey="Upper" stroke="none" fill="#8b5cf6" fillOpacity={0.1} />
          <Area type="monotone" dataKey="Predicted" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.2} strokeWidth={2} />
          <Area type="monotone" dataKey="Lower" stroke="none" fill="#ffffff" fillOpacity={1} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
