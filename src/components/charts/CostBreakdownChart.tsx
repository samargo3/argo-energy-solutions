import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
} from 'recharts'

interface TouBreakdown {
  kwh: number
  cost: number
  hours: number
  pct_of_total_kwh: number
  rate: number
}

interface CostBreakdownProps {
  periodBreakdown: Record<string, TouBreakdown>
  flatCost: number
  touCost: number
  savings: number
  savingsPct: number
}

const COLORS: Record<string, string> = {
  off_peak: '#10b981',
  mid_peak: '#f59e0b',
  on_peak: '#ef4444',
}

const LABELS: Record<string, string> = {
  off_peak: 'Off-Peak',
  mid_peak: 'Mid-Peak',
  on_peak: 'On-Peak',
}

export default function CostBreakdownChart({
  periodBreakdown, flatCost, touCost, savings, savingsPct,
}: CostBreakdownProps) {
  const pieData = Object.entries(periodBreakdown).map(([key, val]) => ({
    name: LABELS[key] || key,
    value: Number(val.cost.toFixed(2)),
    kwh: Number(val.kwh.toFixed(0)),
    rate: val.rate,
    pct: val.pct_of_total_kwh,
  }))

  return (
    <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', alignItems: 'center' }}>
      <div style={{ width: 280, height: 280 }}>
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              dataKey="value"
              label={({ name, pct }) => `${name} ${pct.toFixed(0)}%`}
              labelLine={false}
            >
              {pieData.map((entry, i) => (
                <Cell
                  key={entry.name}
                  fill={COLORS[Object.keys(periodBreakdown)[i]] || '#6b7280'}
                />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number, name: string, props: any) => [
                `$${value} (${props.payload.kwh} kWh @ $${props.payload.rate}/kWh)`,
                name,
              ]}
              contentStyle={{ borderRadius: 8, border: '1px solid #e5e7eb', fontSize: 13 }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div style={{ flex: 1, minWidth: 200 }}>
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          <div style={{ padding: '1rem', background: '#f9fafb', borderRadius: 8, border: '1px solid #e5e7eb' }}>
            <div style={{ fontSize: 13, color: '#6b7280' }}>Flat Rate Cost</div>
            <div style={{ fontSize: 20, fontWeight: 700 }}>${flatCost.toFixed(2)}</div>
          </div>
          <div style={{ padding: '1rem', background: '#f0fdf4', borderRadius: 8, border: '1px solid #bbf7d0' }}>
            <div style={{ fontSize: 13, color: '#16a34a' }}>TOU Optimized Cost</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: '#16a34a' }}>${touCost.toFixed(2)}</div>
          </div>
          <div style={{ padding: '1rem', background: '#eff6ff', borderRadius: 8, border: '1px solid #bfdbfe' }}>
            <div style={{ fontSize: 13, color: '#2563eb' }}>Potential Savings</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: '#2563eb' }}>
              ${savings.toFixed(2)}/mo ({savingsPct}%)
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
