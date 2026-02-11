import { useEffect, useState, useCallback } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { format, parseISO } from 'date-fns'
import {
  Zap,
  TrendingUp,
  Loader2,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react'
import apiClient from '../../services/api/apiClient'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface EnergyRow {
  timestamp: string
  energy_kwh: number
  avg_power_kw: number
}

interface ApiResponse {
  meta: {
    start_date: string
    end_date: string
    rows: number
    aggregation: string
  }
  data: EnergyRow[]
}

interface ChartPoint {
  ts: string          // raw ISO string for tooltip
  label: string       // formatted tick label
  energy_kwh: number
  avg_power_kw: number
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const BLUE = '#2563eb'

// ---------------------------------------------------------------------------
// Custom tooltip
// ---------------------------------------------------------------------------
function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean
  payload?: Array<{ payload: ChartPoint }>
  label?: string
}) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload
  const dt = parseISO(point.ts)
  return (
    <div
      style={{
        background: '#fff',
        border: '1px solid var(--border-color, #e5e7eb)',
        borderRadius: 8,
        padding: '10px 14px',
        boxShadow: '0 4px 12px rgba(0,0,0,.08)',
        fontSize: 13,
      }}
    >
      <p style={{ fontWeight: 600, marginBottom: 4 }}>
        {format(dt, 'EEE, MMM d yyyy')}
      </p>
      <p style={{ color: 'var(--text-light, #6b7280)' }}>
        {format(dt, 'HH:mm')}
      </p>
      <p style={{ color: BLUE, fontWeight: 600, marginTop: 6 }}>
        {point.energy_kwh.toFixed(2)} kWh
      </p>
      <p style={{ color: '#6366f1', fontSize: 12 }}>
        {point.avg_power_kw.toFixed(2)} kW avg
      </p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export default function EnergyHistoryChart() {
  const [data, setData] = useState<ChartPoint[]>([])
  const [meta, setMeta] = useState<ApiResponse['meta'] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await apiClient.get<ApiResponse>('/api/energy/history')
      const json = res.data

      setMeta(json.meta)
      setData(
        json.data.map((r) => {
          const dt = parseISO(r.timestamp)
          return {
            ts: r.timestamp,
            label: format(dt, 'MMM d HH:mm'),
            energy_kwh: r.energy_kwh,
            avg_power_kw: r.avg_power_kw,
          }
        }),
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // ----- Derived KPIs -----
  const totalKwh = data.reduce((sum, d) => sum + d.energy_kwh, 0)
  const maxPeakKw = data.reduce((max, d) => Math.max(max, d.avg_power_kw), 0)

  // ----- Loading state -----
  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 400 }}>
        <Loader2 size={32} style={{ animation: 'spin 1s linear infinite', color: BLUE }} />
        <span style={{ marginLeft: 12, fontSize: 15, color: 'var(--text-light, #6b7280)' }}>
          Loading energy data…
        </span>
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
      </div>
    )
  }

  // ----- Error state -----
  if (error) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: 400,
          gap: 16,
        }}
      >
        <AlertTriangle size={40} color="#ef4444" />
        <p style={{ fontSize: 15, color: '#ef4444' }}>{error}</p>
        <button
          onClick={fetchData}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '8px 20px',
            background: BLUE,
            color: '#fff',
            border: 'none',
            borderRadius: 6,
            cursor: 'pointer',
            fontSize: 14,
            fontWeight: 500,
          }}
        >
          <RefreshCw size={16} /> Retry
        </button>
      </div>
    )
  }

  // ----- Success state -----
  return (
    <div style={{ width: '100%' }}>
      {/* ── Header ── */}
      <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>
        Winter Profile (Nov 2025 – Feb 2026)
      </h2>
      {meta && (
        <p style={{ color: 'var(--text-light, #6b7280)', fontSize: 13, marginBottom: 20 }}>
          {meta.rows.toLocaleString()} hourly readings &middot; {meta.aggregation} aggregation
        </p>
      )}

      {/* ── Summary Cards ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginBottom: 28 }}>
        <div
          style={{
            background: '#eff6ff',
            borderRadius: 10,
            padding: '18px 22px',
            display: 'flex',
            alignItems: 'center',
            gap: 14,
          }}
        >
          <Zap size={28} color={BLUE} />
          <div>
            <p style={{ fontSize: 13, color: 'var(--text-light, #6b7280)', marginBottom: 2 }}>
              Total Energy
            </p>
            <p style={{ fontSize: 22, fontWeight: 700, color: BLUE }}>
              {totalKwh.toLocaleString(undefined, { maximumFractionDigits: 1 })} kWh
            </p>
          </div>
        </div>

        <div
          style={{
            background: '#f0fdf4',
            borderRadius: 10,
            padding: '18px 22px',
            display: 'flex',
            alignItems: 'center',
            gap: 14,
          }}
        >
          <TrendingUp size={28} color="#16a34a" />
          <div>
            <p style={{ fontSize: 13, color: 'var(--text-light, #6b7280)', marginBottom: 2 }}>
              Max Peak Power
            </p>
            <p style={{ fontSize: 22, fontWeight: 700, color: '#16a34a' }}>
              {maxPeakKw.toFixed(2)} kW
            </p>
          </div>
        </div>
      </div>

      {/* ── Chart ── */}
      <ResponsiveContainer width="100%" height={420}>
        <LineChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11 }}
            angle={-45}
            textAnchor="end"
            height={70}
            interval={Math.max(1, Math.floor(data.length / 24))}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            label={{
              value: 'Energy (kWh)',
              angle: -90,
              position: 'insideLeft',
              offset: 0,
              style: { fontSize: 13, fill: 'var(--text-light, #6b7280)' },
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="energy_kwh"
            stroke={BLUE}
            strokeWidth={1.5}
            dot={false}
            name="Energy (kWh)"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
