import { Link } from 'react-router-dom';
import './Reports.css';

export default function Reports() {
  return (
    <div className="reports-page">
      <div className="container">
        <h1 className="page-title">Reports</h1>
        <p className="page-subtitle">Generate and view energy analysis reports</p>

        <div className="reports-grid">
          <div className="report-card">
            <h2>Wilson Center Equipment Report</h2>
            <p>Analyze specific units at Wilson Center for anomalies and equipment issues</p>
            <ul className="report-features">
              <li>✓ Select specific unit/channel</li>
              <li>✓ Customizable date range</li>
              <li>✓ Anomaly detection</li>
              <li>✓ Equipment health assessment</li>
              <li>✓ Actionable recommendations</li>
            </ul>
            <Link to="/reports/wilson-center" className="btn btn-primary">
              Generate Report
            </Link>
          </div>

          <div className="report-card">
            <h2>Weekly Analytics Brief</h2>
            <p>Comprehensive weekly analysis with forecasting, cost optimization, and sensor health</p>
            <ul className="report-features">
              <li>&#10003; 24-hour load profile</li>
              <li>&#10003; 7-day energy forecast</li>
              <li>&#10003; Time-of-Use cost analysis</li>
              <li>&#10003; Demand shaving scenarios</li>
              <li>&#10003; Sensor health monitoring</li>
            </ul>
            <Link to="/reports/weekly" className="btn btn-primary">
              View Weekly Report
            </Link>
          </div>

          <div className="report-card">
            <h2>Electrical Health Screening</h2>
            <p>Monthly assessment of power quality, voltage stability, and harmonic distortion</p>
            <ul className="report-features">
              <li>&#10003; Voltage stability &amp; sag/swell events</li>
              <li>&#10003; Peak current analysis</li>
              <li>&#10003; Frequency excursion monitoring</li>
              <li>&#10003; Neutral current indicators</li>
              <li>&#10003; Current THD analysis</li>
              <li>&#10003; Overall electrical health score</li>
            </ul>
            <Link to="/reports/electrical-health" className="btn btn-primary">
              Generate Report
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

