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
            <h2>Coming Soon</h2>
            <p>Additional report types will be available here</p>
            <ul className="report-features">
              <li>Monthly energy summaries</li>
              <li>Cost analysis reports</li>
              <li>Comparative analysis</li>
              <li>PDF export functionality</li>
            </ul>
            <button className="btn btn-secondary" disabled>
              Coming Soon
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

