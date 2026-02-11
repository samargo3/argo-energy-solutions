import { useWeeklyReport } from '../hooks/useWeeklyReport'
import LoadProfileChart from '../components/charts/LoadProfileChart'
import ForecastChart from '../components/charts/ForecastChart'
import CostBreakdownChart from '../components/charts/CostBreakdownChart'
import StatsCard from '../components/common/StatsCard'
import './WeeklyReport.css'

const SITE_ID = '23271' // Wilson Center — will be dynamic with multi-tenant

export default function WeeklyReport() {
  const { data: report, isLoading, error } = useWeeklyReport(SITE_ID)

  if (isLoading) {
    return (
      <div className="weekly-report">
        <div className="container">
          <div className="loading-state">Loading weekly report...</div>
        </div>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="weekly-report">
        <div className="container">
          <div className="error-state">
            <h2>Report Unavailable</h2>
            <p>Could not load the weekly report. Make sure the API server is running and a report has been generated.</p>
            <p className="error-detail">{error instanceof Error ? error.message : 'Unknown error'}</p>
          </div>
        </div>
      </div>
    )
  }

  const { metadata, summary, sections, dataQuality } = report
  const { sensorHealth, forecast, costOptimization, quickWins } = sections

  const periodStart = new Date(metadata.period.start).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  const periodEnd = new Date(metadata.period.end).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })

  return (
    <div className="weekly-report">
      <div className="container">
        {/* Header */}
        <div className="report-header">
          <div>
            <h1 className="page-title">Weekly Energy Report</h1>
            <p className="page-subtitle">
              {metadata.site.siteName} &middot; {periodStart} &ndash; {periodEnd}
            </p>
          </div>
          <div className="report-meta">
            Generated {new Date(metadata.generatedAt).toLocaleDateString('en-US', {
              month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit',
            })}
          </div>
        </div>

        {/* Summary KPIs */}
        <div className="kpi-grid">
          <StatsCard
            title="Total Savings Potential"
            value={`$${summary.totalPotentialSavings.costOptimizationAnnual.toLocaleString()}/yr`}
            subtitle={`$${summary.totalPotentialSavings.costOptimizationMonthly.toFixed(0)}/mo`}
          />
          <StatsCard
            title="Sensor Issues"
            value={`${sensorHealth.totalIssues}`}
            subtitle={`${sensorHealth.bySeverity.high} high severity`}
          />
          <StatsCard
            title="Data Completeness"
            value={`${dataQuality.avgCompleteness.toFixed(0)}%`}
            subtitle={`${dataQuality.channelsAnalyzed} channels`}
          />
          <StatsCard
            title="Forecast Trend"
            value={forecast.summary.trend_direction === 'stable' ? 'Stable' :
              forecast.summary.trend_direction === 'up' ? 'Increasing' : 'Decreasing'}
            subtitle={`${forecast.summary.trend_change_pct > 0 ? '+' : ''}${forecast.summary.trend_change_pct}% vs last week`}
          />
        </div>

        {/* Headlines */}
        {summary.headline.length > 0 && (
          <div className="alert-banner">
            {summary.headline.map((h, i) => <span key={i}>{h}</span>)}
          </div>
        )}

        {/* Sensor Health */}
        <section className="report-section">
          <h2 className="section-title">Sensor Health</h2>
          {sensorHealth.totalIssues === 0 ? (
            <p className="section-ok">All sensors reporting normally.</p>
          ) : (
            <>
              <div className="severity-badges">
                {sensorHealth.bySeverity.high > 0 && (
                  <span className="badge badge-high">{sensorHealth.bySeverity.high} High</span>
                )}
                {sensorHealth.bySeverity.medium > 0 && (
                  <span className="badge badge-medium">{sensorHealth.bySeverity.medium} Medium</span>
                )}
                {sensorHealth.bySeverity.low > 0 && (
                  <span className="badge badge-low">{sensorHealth.bySeverity.low} Low</span>
                )}
              </div>
              <div className="issues-list">
                {sensorHealth.issues.slice(0, 8).map((issue, i) => (
                  <div key={i} className={`issue-row issue-${issue.severity}`}>
                    <span className="issue-indicator" />
                    <div className="issue-content">
                      <strong>{issue.channelName}</strong>
                      <span className="issue-desc">{issue.description}</span>
                    </div>
                    <span className={`issue-severity-tag tag-${issue.severity}`}>
                      {issue.severity}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </section>

        {/* Load Profile */}
        {costOptimization?.demand_analysis?.load_profile && (
          <section className="report-section">
            <h2 className="section-title">24-Hour Load Profile</h2>
            <p className="section-subtitle">
              Average and peak demand by hour of day (last 30 days).
              Weekday peak: {costOptimization.demand_analysis.weekday_peak_kw.toFixed(1)} kW
              &middot; Weekend peak: {costOptimization.demand_analysis.weekend_peak_kw.toFixed(1)} kW
            </p>
            <LoadProfileChart
              data={costOptimization.demand_analysis.load_profile}
              peakHours={costOptimization.demand_analysis.peak_concentration_hours}
            />
          </section>
        )}

        {/* Forecast */}
        {forecast?.summary && (
          <section className="report-section">
            <h2 className="section-title">7-Day Energy Forecast</h2>
            <p className="section-subtitle">
              Predicted total: {forecast.summary.total_predicted_kwh.toLocaleString()} kWh
              &middot; Last 7d actual: {forecast.summary.total_last_7d_actual_kwh.toLocaleString()} kWh
              &middot; Trained on {forecast.summary.training_rows.toLocaleString()} readings
            </p>
            <ForecastChart
              data={forecast.forecast}
              dailySummary={forecast.summary.daily_forecast}
            />
          </section>
        )}

        {/* Cost Optimization */}
        {costOptimization?.tou_analysis && (
          <section className="report-section">
            <h2 className="section-title">Cost Optimization</h2>
            <p className="section-subtitle">
              Time-of-Use analysis for {costOptimization.tou_analysis.total_kwh.toLocaleString()} kWh
              over the last 30 days
            </p>
            <CostBreakdownChart
              periodBreakdown={costOptimization.tou_analysis.period_breakdown}
              flatCost={costOptimization.tou_analysis.flat_total_cost}
              touCost={costOptimization.tou_analysis.tou_total_cost}
              savings={costOptimization.tou_analysis.tou_vs_flat_savings}
              savingsPct={costOptimization.tou_analysis.tou_vs_flat_pct}
            />
          </section>
        )}

        {/* Demand Shaving Scenarios */}
        {costOptimization?.demand_analysis?.shaving_scenarios && (
          <section className="report-section">
            <h2 className="section-title">Peak Demand Shaving Scenarios</h2>
            <p className="section-subtitle">
              Current billing peak: {costOptimization.demand_analysis.billing_peak_kw.toFixed(1)} kW
              &middot; Monthly demand charge: ${costOptimization.demand_analysis.monthly_demand_charge.toFixed(0)}
            </p>
            <div className="shaving-grid">
              {costOptimization.demand_analysis.shaving_scenarios.map((s) => (
                <div key={s.reduction_pct} className="shaving-card">
                  <div className="shaving-pct">{s.reduction_pct}%</div>
                  <div className="shaving-label">Reduction</div>
                  <div className="shaving-value">{s.reduced_peak_kw.toFixed(1)} kW</div>
                  <div className="shaving-savings">${s.annual_savings.toFixed(0)}/yr</div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Recommendations */}
        {costOptimization?.demand_analysis?.recommendations && (
          <section className="report-section">
            <h2 className="section-title">Recommendations</h2>
            <div className="recommendations-list">
              {costOptimization.demand_analysis.recommendations.map((rec, i) => (
                <div key={i} className="recommendation-card">
                  <div className="rec-header">
                    <span className={`badge badge-${rec.priority}`}>{rec.priority}</span>
                    <span className="rec-category">{rec.category.replace('_', ' ')}</span>
                  </div>
                  <h3>{rec.title}</h3>
                  <p>{rec.detail}</p>
                </div>
              ))}
              {quickWins.map((qw, i) => (
                <div key={`qw-${i}`} className="recommendation-card">
                  <div className="rec-header">
                    <span className={`badge badge-${qw.priority}`}>{qw.priority}</span>
                    <span className="rec-category">{qw.type.replace('_', ' ')}</span>
                  </div>
                  <h3>{qw.title}</h3>
                  <p>{qw.description}</p>
                  {qw.recommendations.length > 0 && (
                    <ul className="rec-steps">
                      {qw.recommendations.map((r, j) => <li key={j}>{r}</li>)}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
