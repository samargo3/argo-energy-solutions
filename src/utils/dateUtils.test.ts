import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import {
  formatDateForApi,
  getDateRange,
  formatDisplayDate,
  formatDateTime,
  getPreviousPeriod,
} from './dateUtils'

describe('formatDateForApi', () => {
  it('returns ISO 8601 string', () => {
    const date = new Date('2025-06-15T12:00:00Z')
    expect(formatDateForApi(date)).toBe(date.toISOString())
  })
})

describe('getDateRange', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2025-06-15T14:30:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns start and end date strings for "month"', () => {
    const range = getDateRange('month')
    expect(range).toHaveProperty('startDate')
    expect(range).toHaveProperty('endDate')
    expect(new Date(range.startDate).getTime()).toBeLessThan(new Date(range.endDate).getTime())
  })

  it('today range starts at beginning of day', () => {
    const range = getDateRange('today')
    const start = new Date(range.startDate)
    expect(start.getUTCHours()).toBe(0)
    expect(start.getUTCMinutes()).toBe(0)
    expect(start.getUTCSeconds()).toBe(0)
  })

  it('uses custom dates when period is custom', () => {
    const customStart = new Date('2025-03-01T00:00:00Z')
    const customEnd = new Date('2025-03-31T23:59:59Z')
    const range = getDateRange('custom', customStart, customEnd)
    expect(range.startDate).toBe(customStart.toISOString())
    expect(range.endDate).toBe(customEnd.toISOString())
  })
})

describe('formatDisplayDate', () => {
  it('formats ISO string to readable date', () => {
    const result = formatDisplayDate('2025-06-15T12:00:00Z')
    expect(result).toContain('Jun')
    expect(result).toContain('15')
    expect(result).toContain('2025')
  })

  it('accepts a Date object', () => {
    const result = formatDisplayDate(new Date('2025-01-01T00:00:00Z'))
    expect(result).toContain('Jan')
  })

  it('accepts custom format string', () => {
    const result = formatDisplayDate('2025-06-15T12:00:00Z', 'yyyy-MM-dd')
    expect(result).toBe('2025-06-15')
  })
})

describe('formatDateTime', () => {
  it('includes date and time in output', () => {
    const result = formatDateTime('2025-06-15T14:30:00Z')
    expect(result).toContain('Jun')
    expect(result).toContain('15')
    expect(result).toContain('14:30')
  })
})

describe('getPreviousPeriod', () => {
  it('returns a period of the same duration ending at the start of the current period', () => {
    const prev = getPreviousPeriod('2025-02-01T00:00:00Z', '2025-02-28T00:00:00Z')
    expect(prev.endDate).toBe(new Date('2025-02-01T00:00:00Z').toISOString())
    const prevStart = new Date(prev.startDate).getTime()
    const prevEnd = new Date(prev.endDate).getTime()
    const originalDuration =
      new Date('2025-02-28T00:00:00Z').getTime() - new Date('2025-02-01T00:00:00Z').getTime()
    expect(prevEnd - prevStart).toBe(originalDuration)
  })
})
