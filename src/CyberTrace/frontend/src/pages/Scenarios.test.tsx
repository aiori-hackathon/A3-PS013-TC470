import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { Scenarios } from './Scenarios'
import { api, ApiError } from '../api/client'
import type { ScenarioInfo, ScenarioLoadResult } from '../types/scenario'

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client')
  return {
    ...actual,
    api: {
      get: vi.fn(),
      post: vi.fn(),
      postForm: vi.fn(),
      delete: vi.fn(),
      download: vi.fn(),
    },
  }
})

const mockScenarios: ScenarioInfo[] = [
  { key: 'ssh_bruteforce', name: 'SSH Brute Force (synthetic)', description: 'Desc A' },
  { key: 'sql_injection_probe', name: 'SQL Injection Probe (synthetic)', description: 'Desc B' },
  {
    key: 'phishing_lateral_movement',
    name: 'Phishing + Lateral Movement (synthetic)',
    description: 'Desc C',
  },
]

function renderScenarios() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <Scenarios />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Scenarios page', () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset()
    vi.mocked(api.post).mockReset()
    vi.mocked(api.get).mockResolvedValue(mockScenarios)
  })

  it('lists all three scenarios with descriptions', async () => {
    renderScenarios()
    expect(await screen.findByText('SSH Brute Force (synthetic)')).toBeInTheDocument()
    expect(screen.getByText('SQL Injection Probe (synthetic)')).toBeInTheDocument()
    expect(screen.getByText('Phishing + Lateral Movement (synthetic)')).toBeInTheDocument()
  })

  it('shows the ingestion summary after loading a scenario', async () => {
    const result: ScenarioLoadResult = {
      case: {
        id: 'case-1',
        name: 'SSH Brute Force (synthetic)',
        description: 'Desc A',
        is_synthetic: true,
        scenario_key: 'ssh_bruteforce',
        created_by: 'user-1',
        created_at: '2026-10-10T00:00:00Z',
      },
      records_parsed: 12,
      records_failed: 2,
      gaps_detected: 0,
    }
    vi.mocked(api.post).mockResolvedValue(result)

    renderScenarios()
    const button = await screen.findAllByRole('button', { name: 'Load scenario' })
    await userEvent.click(button[0])

    const summary = await screen.findByTestId('scenario-load-summary')
    expect(summary).toHaveTextContent('12')
    expect(summary).toHaveTextContent('2')
  })

  it('shows an error message when loading fails', async () => {
    vi.mocked(api.post).mockRejectedValue(new ApiError('Unknown scenario', 404))

    renderScenarios()
    const button = await screen.findAllByRole('button', { name: 'Load scenario' })
    await userEvent.click(button[0])

    expect(await screen.findByRole('alert')).toHaveTextContent('Unknown scenario')
  })
})
