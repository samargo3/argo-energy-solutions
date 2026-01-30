import './StatsCard.css'

interface StatsCardProps {
  title: string
  value: string
  subtitle?: string
}

export default function StatsCard({ title, value, subtitle }: StatsCardProps) {
  return (
    <div className="stats-card">
      <h3 className="stats-card-title">{title}</h3>
      <div className="stats-card-value">{value}</div>
      {subtitle && <div className="stats-card-subtitle">{subtitle}</div>}
    </div>
  )
}

