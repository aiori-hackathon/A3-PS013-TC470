import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { Timeline } from './Timeline'
import { api } from '../api/client'
import type { Case } from '../types/case'
import type { TimelineRecord, TimelineResponse } from '../types/timeline'

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

const mockRecord: TimelineRecord = {
  id: 'rec-1',
  case_id: 'case-1',
  evidence_file_id: 'ev-1',
  line_number: 3,
  raw_line: 'Oct 10 08:00:00 server sshd[1]: Failed password for root from 10.0.0.5 port 1 ssh2',
  event_time_utc: '2026-10-10T08:00:00Z',
  original_timezone: 'UTC (assumed)',
  source_ip: '10.0.0.5',
  user_or_actor: 'root',
  event_type: 'auth_failure',
  message: 'Failed password for root from 10.0.0.5',
  severity: 'warning',
  extra: null,
  evidence_filename: 'auth.log',
  evidence_sha256: 'a'.repeat(64),
  near_parse_gap: false,
}

const mockResponse: TimelineResponse = {
  total: 1,
  limit: 100,
  offset: 0,
  records: [mockRecord],
}

function renderTimeline() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/timeline?case_id=case-1']}>
        <Timeline />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Timeline page', () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset()
    vi.mocked(api.get).mockImplementation((path: string) => {
      if (path === '/api/cases') return Promise.resolve([mockCase])
      if (path.includes('/timeline')) return Promise.resolve(mockResponse)
      return Promise.resolve([])
    })
  })

  it('renders real timeline records with event type and severity', async () => {
    renderTimeline()

    expect(await screen.findByText('auth_failure')).toBeInTheDocument()
    expect(screen.getAllByText('warning').length).toBeGreaterThan(0)
    expect(screen.getByText('10.0.0.5')).toBeInTheDocument()
    expect(screen.getByText('Parsed')).toBeInTheDocument()
  })

  it('opens the detail drawer with raw_line and evidence info on row click', async () => {
    renderTimeline()

    const eventCell = await screen.findByText('auth_failure')
    await userEvent.click(eventCell)

    expect(await screen.findByText('Record detail')).toBeInTheDocument()
    expect(screen.getByText(mockRecord.raw_line)).toBeInTheDocument()
    expect(screen.getByText('auth.log')).toBeInTheDocument()
    expect(screen.getByText('Line 3')).toBeInTheDocument()
  })

  it('shows an empty state message when no case is selected', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/timeline']}>
          <Timeline />
        </MemoryRouter>
      </QueryClientProvider>,
    )
    expect(screen.getByText('Select a case above to view its timeline.')).toBeInTheDocument()
  })
})
