import { describe, it, expect, vi } from 'vitest'
import { screen } from '@testing-library/react'
import { renderWithProviders } from '../test/testUtils'
import Customers from './Customers'
import type { Customer } from '../types'

// Mock the hook module
vi.mock('../hooks/useCustomerData', () => ({
  useCustomers: vi.fn(),
}))

import { useCustomers } from '../hooks/useCustomerData'
const mockUseCustomers = vi.mocked(useCustomers)

describe('Customers', () => {
  it('shows loading state', () => {
    mockUseCustomers.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as ReturnType<typeof useCustomers>)

    renderWithProviders(<Customers />)
    expect(screen.getByText('Loading customers...')).toBeInTheDocument()
  })

  it('shows error state', () => {
    mockUseCustomers.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Network error'),
    } as ReturnType<typeof useCustomers>)

    renderWithProviders(<Customers />)
    expect(screen.getByText(/Error loading customers/)).toBeInTheDocument()
  })

  it('shows empty state when no customers', () => {
    mockUseCustomers.mockReturnValue({
      data: { items: [] as Customer[], total: 0, page: 1, pageSize: 10, totalPages: 0 },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useCustomers>)

    renderWithProviders(<Customers />)
    expect(screen.getByText(/No customers found/)).toBeInTheDocument()
  })

  it('renders customer cards with data', () => {
    mockUseCustomers.mockReturnValue({
      data: {
        items: [
          { id: '1', name: 'Acme Corp', email: 'acme@test.com', address: '123 Main St', sites: [{ id: 's1' }] },
          { id: '2', name: 'Widget Inc', email: 'widget@test.com' },
        ],
        total: 2,
        page: 1,
        pageSize: 10,
        totalPages: 1,
      },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useCustomers>)

    renderWithProviders(<Customers />)
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    expect(screen.getByText('Widget Inc')).toBeInTheDocument()
    expect(screen.getByText('acme@test.com')).toBeInTheDocument()
    expect(screen.getByText('123 Main St')).toBeInTheDocument()
    expect(screen.getByText('1 site(s)')).toBeInTheDocument()
  })

  it('links to customer portal', () => {
    mockUseCustomers.mockReturnValue({
      data: {
        items: [{ id: '42', name: 'Test Customer' }],
        total: 1, page: 1, pageSize: 10, totalPages: 1,
      },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useCustomers>)

    renderWithProviders(<Customers />)
    const link = screen.getByText('Test Customer').closest('a')
    expect(link).toHaveAttribute('href', '/customers/42')
  })
})
