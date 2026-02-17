import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginPage from './LoginPage'

const mockLogin = vi.fn()

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    login: mockLogin,
    token: null,
    isAuthenticated: false,
    logout: vi.fn(),
  }),
}))

describe('LoginPage', () => {
  beforeEach(() => {
    mockLogin.mockReset()
  })

  it('renders the login form', () => {
    render(<LoginPage />)
    expect(screen.getByText('Argo Energy')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument()
  })

  it('calls login with entered password on submit', async () => {
    mockLogin.mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(<LoginPage />)
    await user.type(screen.getByLabelText('Password'), 'my-secret')
    await user.click(screen.getByRole('button', { name: 'Sign In' }))

    expect(mockLogin).toHaveBeenCalledWith('my-secret')
  })

  it('shows error message on login failure', async () => {
    mockLogin.mockRejectedValue(new Error('Invalid password'))
    const user = userEvent.setup()

    render(<LoginPage />)
    await user.type(screen.getByLabelText('Password'), 'wrong')
    await user.click(screen.getByRole('button', { name: 'Sign In' }))

    expect(await screen.findByText('Invalid password')).toBeInTheDocument()
  })

  it('disables button while loading', async () => {
    mockLogin.mockImplementation(() => new Promise(() => {})) // never resolves
    const user = userEvent.setup()

    render(<LoginPage />)
    await user.type(screen.getByLabelText('Password'), 'test')
    await user.click(screen.getByRole('button', { name: 'Sign In' }))

    expect(screen.getByRole('button', { name: 'Signing in...' })).toBeDisabled()
  })
})
