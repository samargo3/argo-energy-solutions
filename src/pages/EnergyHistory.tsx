import EnergyHistoryChart from '../components/charts/EnergyHistoryChart'

export default function EnergyHistory() {
  return (
    <div className="dashboard">
      <div className="container" style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 20px' }}>
        <EnergyHistoryChart />
      </div>
    </div>
  )
}
