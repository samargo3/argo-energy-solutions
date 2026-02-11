import { useQuery } from '@tanstack/react-query'
import apiClient from '../services/api/apiClient'

export interface WeeklyReport {
  metadata: {
    generatedAt: string
    reportVersion: string
    site: { siteId: number; siteName: string; address: string }
    period: { start: string; end: string; timezone: string }
    baseline: { start: string; end: string; weeksCount: number }
    dataResolution: string
  }
  summary: {
    headline: string[]
    topRisks: string[]
    topOpportunities: string[]
    totalPotentialSavings: {
      weeklyKwh: number
      weeklyCost: number
      estimatedAnnual: number
      costOptimizationMonthly: number
      costOptimizationAnnual: number
    }
  }
  sections: {
    sensorHealth: {
      summary: Array<{ type: string; count: number; affectedChannels: number; description: string }>
      totalIssues: number
      bySeverity: { high: number; medium: number; low: number }
      issues: Array<{
        type: string
        severity: string
        channelId: number
        channelName: string
        lastReading?: string
        hoursSince?: string
        description: string
      }>
    }
    afterHoursWaste: {
      summary: {
        totalMetersWithExcess: number
        totalExcessKwh: number
        totalExcessCost: number
        estimatedAnnualCost: number
      }
    }
    anomalies: {
      summary: { totalEvents: number; affectedChannels: number; totalExcessKwh: number }
    }
    spikes: {
      summary: { totalEvents: number; affectedChannels: number; totalExcessKwh: number }
    }
    quickWins: Array<{
      title: string
      type: string
      priority: string
      impact: { weeklyKwh: string; weeklyCost: number; annualCost: number; description: string }
      description: string
      recommendations: string[]
      confidence: string
      effort: string
    }>
    forecast: {
      forecast: Array<{ timestamp: string; predicted_kwh: number; lower_bound: number; upper_bound: number }>
      summary: {
        site_id: number
        horizon_days: number
        training_rows: number
        forecast_hours: number
        total_predicted_kwh: number
        total_last_7d_actual_kwh: number
        daily_forecast: Array<{ date: string; predicted_kwh: number; peak_hour_kwh: number }>
        trend_direction: string
        trend_change_pct: number
      }
    }
    costOptimization: {
      tou_analysis: {
        total_kwh: number
        flat_rate: number
        flat_total_cost: number
        tou_total_cost: number
        tou_vs_flat_savings: number
        tou_vs_flat_pct: number
        period_breakdown: Record<string, { kwh: number; cost: number; hours: number; pct_of_total_kwh: number; rate: number }>
        load_shift_opportunity: { on_peak_kwh: number; potential_savings_per_kwh: number; max_monthly_savings: number }
      }
      demand_analysis: {
        billing_peak_kw: number
        peak_timestamp: string
        demand_rate_per_kw: number
        monthly_demand_charge: number
        annual_demand_charge: number
        top_peak_events: Array<{ timestamp: string; demand_kw: number; hour_of_day: number; day_of_week: string }>
        shaving_scenarios: Array<{ reduction_pct: number; reduced_peak_kw: number; monthly_savings: number; annual_savings: number }>
        load_profile: Array<{ hour: number; avg_kw: number; max_kw: number }>
        weekday_peak_kw: number
        weekend_peak_kw: number
        peak_concentration_hours: number[]
        recommendations: Array<{ priority: string; category: string; title: string; detail: string }>
      }
      combined_summary: {
        total_energy_kwh: number
        current_flat_cost: number
        tou_optimized_cost: number
        demand_charge: number
        estimated_monthly_savings_potential: number
        estimated_annual_savings_potential: number
      }
    }
  }
  dataQuality: {
    channelsAnalyzed: number
    avgCompleteness: number
  }
}

export function useWeeklyReport(siteId: string) {
  return useQuery<WeeklyReport>({
    queryKey: ['weekly-report', siteId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/api/reports/weekly/${siteId}/latest`)
      return data
    },
    enabled: !!siteId,
    staleTime: 5 * 60 * 1000,
  })
}
