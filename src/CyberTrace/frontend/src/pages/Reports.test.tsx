import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { Reports } from './Reports'
import { api } from '../api/client'
import type { Case } from '../types/case'
import type { Report } from '../types/report'

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

const mockCase: Case = {
  id: 'case-1',
  name: 'Test case',
  description: null,
  is_synthetic: false,
  scenario_key: null,
  created_by: 'user-1',
  created_at: '2026-10-10T00:00:00Z',
}

const mockReport: Report = {
  id: 'rep-1',
  case_id: 'case-1',
  format: 'json',
  generated_by: 'user-1',
  generated_at: '2026-10-10T00:00:00Z',
}

function renderReports() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/reports?case_id=case-1']}>
        <Reports />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Reports page', () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset()
    vi.mocked(api.post).mockReset()
    vi.mocked(api.get).mockImplementation((path: string) => {
      if (path === '/api/cases') return Promise.resolve([mockCase])
      if (path.includes('/reports')) return Promise.resolve([mockReport])
      return Promise.resolve([])
    })
  })

  it('lists existing reports with format and generated date', async () => {
    renderReports()
    expect(await screen.findByText('JSON (full export)')).toBeInTheDocument()
  })

  it('generates a new report when a format button is clicked', async () => {
    vi.mocked(api.post).mockResolvedValue(mockReport)
    renderReports()

    await screen.findByText('Generate a new report')
    await userEvent.click(screen.getByRole('button', { name: 'Generate PDF' }))

    expect(api.post).toHaveBeenCalledWith('/api/cases/case-1/reports?format=pdf')
  })

  it('shows an empty state when no case is selected', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/reports']}>
          <Reports />
        </MemoryRouter>
      </QueryClientProvider>,
    )
    expect(
      screen.getByText('Select a case above to generate or download reports.'),
    ).toBeInTheDocument()
  })
})
