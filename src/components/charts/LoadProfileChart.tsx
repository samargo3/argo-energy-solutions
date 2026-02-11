import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from 'recharts'

interface LoadProfileProps {
  data: Array<{ hour: number; avg_kw: number; max_kw: number }>
  peakHours?: number[]
}

export default function LoadProfileChart({ data, peakHours = [] }: LoadProfileProps) {
  const chartData = data.map((d) => ({
    hour: `${d.hour.toString().padStart(2, '0')}:00`,
    'Avg kW': Number(d.avg_kw.toFixed(1)),
    'Peak kW': Number(d.max_kw.toFixed(1)),
    isPeak: peakHours.includes(d.hour),
  }))

  return (
    <div style={{ width: '100%', height: 320 }}>
      <ResponsiveContainer>
        <BarChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="hour"
            tick={{ fontSize: 11 }}
            interval={1}
          />
          <YAxis
            tick={{ fontSize: 11 }}
            label={{ value: 'kW', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
          />
          <Tooltip
            contentStyle={{ borderRadius: 8, border: '1px solid #e5e7eb', fontSize: 13 }}
            formatter={(value: number, name: string) => [`${value} kW`, name]}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="Avg kW" fill="#3b82f6" radius={[3, 3, 0, 0]} />
          <Bar dataKey="Peak kW" fill="#f59e0b" radius={[3, 3, 0, 0]} opacity={0.5} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
