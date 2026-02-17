import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import StatsCard from './StatsCard'

describe('StatsCard', () => {
  it('renders title and value', () => {
    render(<StatsCard title="Total Consumption" value="1,234 kWh" />)
    expect(screen.getByText('Total Consumption')).toBeInTheDocument()
    expect(screen.getByText('1,234 kWh')).toBeInTheDocument()
  })

  it('renders subtitle when provided', () => {
    render(<StatsCard title="Peak" value="500 kWh" subtitle="Jan 15, 2025" />)
    expect(screen.getByText('Jan 15, 2025')).toBeInTheDocument()
  })

  it('does not render subtitle when not provided', () => {
    const { container } = render(<StatsCard title="Min" value="10 kWh" />)
    expect(container.querySelector('.stats-card-subtitle')).toBeNull()
  })
})
