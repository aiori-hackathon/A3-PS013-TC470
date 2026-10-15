import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Login } from './Login'

const { mockLogin, mockPost } = vi.hoisted(() => ({
  mockLogin: vi.fn(),
  mockPost: vi.fn(),
}))

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ login: mockLogin }),
}))

vi.mock('../api/client', () => ({
  api: { post: mockPost },
  ApiError: class ApiError extends Error {},
}))

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/timeline" element={<h1>Timeline destination</h1>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('Login', () => {
  beforeEach(() => {
    mockLogin.mockReset().mockResolvedValue(undefined)
    mockPost.mockReset().mockResolvedValue({})
  })

  it('creates an account, signs in, and opens the workspace', async () => {
    const user = userEvent.setup()
    renderLogin()

    await user.click(screen.getByRole('button', { name: 'Create an account' }))
    await user.type(screen.getByLabelText('Work email'), 'analyst@example.com')
    await user.type(screen.getByLabelText('Password'), 'StrongPassword1')
    await user.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByText('Timeline destination')).toBeInTheDocument()
    expect(mockPost).toHaveBeenCalledWith('/api/auth/register', {
      email: 'analyst@example.com',
      password: 'StrongPassword1',
    })
    expect(mockLogin).toHaveBeenCalledWith('analyst@example.com', 'StrongPassword1')
  })

  it('shows registration errors without attempting to sign in', async () => {
    const user = userEvent.setup()
    mockPost.mockRejectedValueOnce(new Error('An account with this email already exists'))
    renderLogin()

    await user.click(screen.getByRole('button', { name: 'Create an account' }))
    await user.type(screen.getByLabelText('Work email'), 'analyst@example.com')
    await user.type(screen.getByLabelText('Password'), 'StrongPassword1')
    await user.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'An account with this email already exists',
    )
    expect(mockLogin).not.toHaveBeenCalled()
  })
})
