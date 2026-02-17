import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import { renderWithProviders } from '../test/testUtils'
import Reports from './Reports'

describe('Reports', () => {
  it('renders the page title', () => {
    renderWithProviders(<Reports />)
    expect(screen.getByText('Reports')).toBeInTheDocument()
  })

  it('renders all three report cards', () => {
    renderWithProviders(<Reports />)
    expect(screen.getByText('Wilson Center Equipment Report')).toBeInTheDocument()
    expect(screen.getByText('Weekly Analytics Brief')).toBeInTheDocument()
    expect(screen.getByText('Electrical Health Screening')).toBeInTheDocument()
  })

  it('has links to each report page', () => {
    renderWithProviders(<Reports />)
    const links = screen.getAllByText('Generate Report')
    expect(links.length).toBeGreaterThanOrEqual(2)

    const weeklyLink = screen.getByText('View Weekly Report')
    expect(weeklyLink.closest('a')).toHaveAttribute('href', '/reports/weekly')
  })

  it('displays feature lists for each report', () => {
    renderWithProviders(<Reports />)
    expect(screen.getByText(/Anomaly detection/)).toBeInTheDocument()
    expect(screen.getByText(/7-day energy forecast/)).toBeInTheDocument()
    expect(screen.getByText(/Current THD analysis/)).toBeInTheDocument()
  })
})
