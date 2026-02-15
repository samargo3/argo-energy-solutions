import { useState } from 'react'
import { format, subDays } from 'date-fns'
import apiClient from '../services/api/apiClient'
import './ElectricalHealthReport.css'

const NOMINAL_VOLTAGES = [120, 208, 277, 480] as const

export default function ElectricalHealthReport() {
  const [siteId, setSiteId] = useState('23271')
  const [startDate, setStartDate] = useState(format(subDays(new Date(), 30), 'yyyy-MM-dd'))
  const [endDate, setEndDate] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [nominalVoltage, setNominalVoltage] = useState<string>('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleGeneratePdf = async () => {
    setIsGenerating(true)
    setError(null)

    try {
      const params: Record<string, string> = {
        start_date: startDate,
        end_date: endDate,
      }
      if (nominalVoltage) {
        params.nominal_voltage = nominalVoltage
      }

      const response = await apiClient.get(
        `/api/reports/electrical-health/${siteId}`,
        { params, responseType: 'blob' },
      )

      // Trigger browser download
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `electrical-health-site-${siteId}-${startDate}-to-${endDate}.pdf`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to generate report. Make sure the API server is running.')
      }
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="electrical-health-page">
      <div className="container">
        <h1 className="page-title">Electrical Health Screening</h1>
        <p className="page-subtitle">
          Generate a monthly PDF report covering voltage stability, peak current events,
          frequency excursions, neutral current indicators, and current THD analysis.
        </p>

        <div className="report-form">
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="site-id">Site ID</label>
              <input
                id="site-id"
                type="text"
                value={siteId}
                onChange={(e) => setSiteId(e.target.value)}
                className="form-input"
                placeholder="e.g. 23271"
              />
            </div>

            <div className="form-group">
              <label htmlFor="nominal-voltage">Nominal Voltage (optional)</label>
              <select
                id="nominal-voltage"
                value={nominalVoltage}
                onChange={(e) => setNominalVoltage(e.target.value)}
                className="form-select"
              >
                <option value="">Auto-detect</option>
                {NOMINAL_VOLTAGES.map((v) => (
                  <option key={v} value={v}>{v}V</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="start-date">Start Date</label>
              <input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="end-date">End Date</label>
              <input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="form-input"
              />
            </div>
          </div>

          <div className="quick-range-buttons">
            <button
              className="btn btn-secondary"
              onClick={() => {
                setStartDate(format(subDays(new Date(), 30), 'yyyy-MM-dd'))
                setEndDate(format(new Date(), 'yyyy-MM-dd'))
              }}
            >
              Last 30 Days
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => {
                setStartDate(format(subDays(new Date(), 60), 'yyyy-MM-dd'))
                setEndDate(format(new Date(), 'yyyy-MM-dd'))
              }}
            >
              Last 60 Days
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => {
                setStartDate(format(subDays(new Date(), 90), 'yyyy-MM-dd'))
                setEndDate(format(new Date(), 'yyyy-MM-dd'))
              }}
            >
              Last 90 Days
            </button>
          </div>

          {error && (
            <div className="error-state">
              <p>{error}</p>
            </div>
          )}

          <button
            className="btn btn-primary generate-btn"
            onClick={handleGeneratePdf}
            disabled={isGenerating || !siteId}
          >
            {isGenerating ? 'Generating PDF...' : 'Generate PDF Report'}
          </button>
        </div>

        <div className="report-info">
          <h2>Report Contents</h2>
          <div className="info-grid">
            <div className="info-card">
              <h3>Voltage Stability</h3>
              <p>Min/max/average voltage per meter, sag and swell event counts, daily trend with nominal band.</p>
            </div>
            <div className="info-card">
              <h3>Peak Current Events</h3>
              <p>Per-meter peak current analysis, top events with timestamps, daily peak trend.</p>
            </div>
            <div className="info-card">
              <h3>Frequency Excursions</h3>
              <p>Grid frequency analysis, excursion counts outside 59.95-60.05 Hz band, daily trend.</p>
            </div>
            <div className="info-card">
              <h3>Neutral Current</h3>
              <p>Average and max neutral current per meter, elevated neutral events, daily trend.</p>
            </div>
            <div className="info-card">
              <h3>Current THD</h3>
              <p>Total harmonic distortion analysis with IEEE 519 reference, per-meter breakdown.</p>
            </div>
            <div className="info-card">
              <h3>Health Score</h3>
              <p>Weighted composite score (voltage, current, frequency, THD) with Good/Fair/Poor rating.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
