import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { screen } from '@testing-library/react'
import { renderWithProviders } from '../test/testUtils'
import Dashboard from './Dashboard'

vi.mock('../hooks/useCustomerData', () => ({
  useCustomers: vi.fn(),
}))

vi.mock('../hooks/useEnergyData', () => ({
  useGroupedEnergyData: vi.fn(),
}))

// Mock recharts to avoid canvas/SVG issues in jsdom
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children?: React.ReactNode }) => <div data-testid="responsive-container">{children}</div>,
  LineChart: ({ children }: { children?: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
}))

import { useCustomers } from '../hooks/useCustomerData'
import { useGroupedEnergyData } from '../hooks/useEnergyData'

const mockUseCustomers = vi.mocked(useCustomers)
const mockUseGroupedEnergyData = vi.mocked(useGroupedEnergyData)

describe('Dashboard', () => {
  it('shows loading state', () => {
    mockUseCustomers.mockReturnValue({ data: undefined, isLoading: true } as ReturnType<typeof useCustomers>)
    mockUseGroupedEnergyData.mockReturnValue({ data: undefined, isLoading: true } as ReturnType<typeof useGroupedEnergyData>)

    renderWithProviders(<Dashboard />)
    expect(screen.getByText('Loading energy data...')).toBeInTheDocument()
  })

  it('renders title and controls', () => {
    mockUseCustomers.mockReturnValue({
      data: { items: [{ id: '1', name: 'Test Co' }] },
      isLoading: false,
    } as ReturnType<typeof useCustomers>)
    mockUseGroupedEnergyData.mockReturnValue({ data: undefined, isLoading: false } as ReturnType<typeof useGroupedEnergyData>)

    renderWithProviders(<Dashboard />)
    expect(screen.getByText('Energy Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Last Month')).toBeInTheDocument()
  })

  it('renders stats cards when energy data is available', () => {
    mockUseCustomers.mockReturnValue({
      data: { items: [{ id: '1', name: 'Test Co' }] },
      isLoading: false,
    } as ReturnType<typeof useCustomers>)
    mockUseGroupedEnergyData.mockReturnValue({
      data: [
        { date: '2025-01-01', value: 200, cost: 20 },
        { date: '2025-01-02', value: 300, cost: 30 },
      ],
      isLoading: false,
    } as ReturnType<typeof useGroupedEnergyData>)

    renderWithProviders(<Dashboard />)
    expect(screen.getByText('Total Consumption')).toBeInTheDocument()
    expect(screen.getByText('Peak Consumption')).toBeInTheDocument()
    expect(screen.getByText('Total Cost')).toBeInTheDocument()
  })

  it('populates customer dropdown', () => {
    mockUseCustomers.mockReturnValue({
      data: {
        items: [
          { id: '1', name: 'Customer A' },
          { id: '2', name: 'Customer B' },
        ],
      },
      isLoading: false,
    } as ReturnType<typeof useCustomers>)
    mockUseGroupedEnergyData.mockReturnValue({ data: undefined, isLoading: false } as ReturnType<typeof useGroupedEnergyData>)

    renderWithProviders(<Dashboard />)
    expect(screen.getByText('Customer A')).toBeInTheDocument()
    expect(screen.getByText('Customer B')).toBeInTheDocument()
  })

  it('shows error state when customer fetch fails', () => {
    mockUseCustomers.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Failed to fetch customers'),
    } as ReturnType<typeof useCustomers>)
    mockUseGroupedEnergyData.mockReturnValue({ data: undefined, isLoading: false } as ReturnType<typeof useGroupedEnergyData>)

    renderWithProviders(<Dashboard />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText('Failed to fetch customers')).toBeInTheDocument()
  })

  it('shows error state when energy data fetch fails', () => {
    mockUseCustomers.mockReturnValue({
      data: undefined,
      isLoading: false,
    } as ReturnType<typeof useCustomers>)
    mockUseGroupedEnergyData.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Failed to fetch energy data'),
    } as ReturnType<typeof useGroupedEnergyData>)

    renderWithProviders(<Dashboard />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText('Failed to fetch energy data')).toBeInTheDocument()
  })
})
