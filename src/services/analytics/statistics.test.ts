import { describe, it, expect } from 'vitest'
import {
  calculateEnergyStatistics,
  comparePeriods,
  calculatePercentageChange,
  detectAnomalies,
  groupByPeriod,
} from './statistics'
import type { EnergyConsumption } from '../../types'

const makeSample = (overrides?: Partial<EnergyConsumption>): EnergyConsumption => ({
  id: '1',
  siteId: 'site-1',
  customerId: 'cust-1',
  timestamp: '2025-01-15T12:00:00Z',
  value: 100,
  cost: 10,
  ...overrides,
})

describe('calculateEnergyStatistics', () => {
  it('returns zeroes for empty data', () => {
    const stats = calculateEnergyStatistics([], '2025-01-01', '2025-01-31')
    expect(stats.totalConsumption).toBe(0)
    expect(stats.averageConsumption).toBe(0)
    expect(stats.peakConsumption).toBe(0)
    expect(stats.minConsumption).toBe(0)
    expect(stats.cost).toBe(0)
  })

  it('calculates totals, averages, peak and min correctly', () => {
    const data: EnergyConsumption[] = [
      makeSample({ id: '1', value: 50, cost: 5, timestamp: '2025-01-01T00:00:00Z' }),
      makeSample({ id: '2', value: 150, cost: 15, timestamp: '2025-01-02T00:00:00Z' }),
      makeSample({ id: '3', value: 100, cost: 10, timestamp: '2025-01-03T00:00:00Z' }),
    ]
    const stats = calculateEnergyStatistics(data, '2025-01-01', '2025-01-03')

    expect(stats.totalConsumption).toBe(300)
    expect(stats.averageConsumption).toBe(100)
    expect(stats.peakConsumption).toBe(150)
    expect(stats.peakTimestamp).toBe('2025-01-02T00:00:00Z')
    expect(stats.minConsumption).toBe(50)
    expect(stats.minTimestamp).toBe('2025-01-01T00:00:00Z')
    expect(stats.cost).toBe(30)
    expect(stats.averageCost).toBe(10)
  })

  it('handles data with no costs', () => {
    const data = [makeSample({ value: 100, cost: undefined })]
    const stats = calculateEnergyStatistics(data, '2025-01-01', '2025-01-31')
    expect(stats.cost).toBe(0)
    expect(stats.averageCost).toBe(0)
  })

  it('preserves period dates', () => {
    const stats = calculateEnergyStatistics([], '2025-06-01', '2025-06-30')
    expect(stats.period).toEqual({ start: '2025-06-01', end: '2025-06-30' })
  })
})

describe('comparePeriods', () => {
  it('calculates consumption and cost change percentages', () => {
    const current = calculateEnergyStatistics(
      [makeSample({ value: 120, cost: 12 })],
      '2025-02-01', '2025-02-28'
    )
    const previous = calculateEnergyStatistics(
      [makeSample({ value: 100, cost: 10 })],
      '2025-01-01', '2025-01-31'
    )
    const comparison = comparePeriods(current, previous)
    expect(comparison.change.consumption).toBe(20)
    expect(comparison.change.cost).toBe(20)
  })

  it('returns zero change when previous totals are zero', () => {
    const current = calculateEnergyStatistics(
      [makeSample({ value: 100 })],
      '2025-02-01', '2025-02-28'
    )
    const previous = calculateEnergyStatistics([], '2025-01-01', '2025-01-31')
    const comparison = comparePeriods(current, previous)
    expect(comparison.change.consumption).toBe(0)
  })
})

describe('calculatePercentageChange', () => {
  it('calculates positive change', () => {
    expect(calculatePercentageChange(120, 100)).toBe(20)
  })

  it('calculates negative change', () => {
    expect(calculatePercentageChange(80, 100)).toBe(-20)
  })

  it('handles zero previous value', () => {
    expect(calculatePercentageChange(50, 0)).toBe(100)
    expect(calculatePercentageChange(0, 0)).toBe(0)
  })
})

describe('detectAnomalies', () => {
  it('returns empty array for empty data', () => {
    expect(detectAnomalies([])).toEqual([])
  })

  it('detects outliers beyond threshold', () => {
    // Need enough normal data points so the outlier's z-score exceeds 2
    const data: EnergyConsumption[] = [
      ...Array.from({ length: 20 }, (_, i) =>
        makeSample({ id: String(i), value: 100 + (i % 3) })
      ),
      makeSample({ id: 'outlier', value: 500 }), // clear outlier
    ]
    const anomalies = detectAnomalies(data, 2)
    expect(anomalies.length).toBe(1)
    expect(anomalies[0].value).toBe(500)
  })

  it('returns no anomalies for uniform data', () => {
    const data = Array.from({ length: 10 }, (_, i) =>
      makeSample({ id: String(i), value: 100 })
    )
    expect(detectAnomalies(data)).toEqual([])
  })
})

describe('groupByPeriod', () => {
  const data: EnergyConsumption[] = [
    makeSample({ id: '1', timestamp: '2025-01-15T08:00:00Z' }),
    makeSample({ id: '2', timestamp: '2025-01-15T08:30:00Z' }),
    makeSample({ id: '3', timestamp: '2025-01-15T09:00:00Z' }),
    makeSample({ id: '4', timestamp: '2025-01-16T08:00:00Z' }),
  ]

  it('groups by hour', () => {
    const groups = groupByPeriod(data, 'hour')
    const keys = Object.keys(groups)
    expect(keys.length).toBe(3) // 8am on 15th, 9am on 15th, 8am on 16th
  })

  it('groups by day', () => {
    const groups = groupByPeriod(data, 'day')
    const keys = Object.keys(groups)
    expect(keys.length).toBe(2) // Jan 15 and Jan 16
  })

  it('groups by month', () => {
    const groups = groupByPeriod(data, 'month')
    expect(Object.keys(groups).length).toBe(1)
  })
})
