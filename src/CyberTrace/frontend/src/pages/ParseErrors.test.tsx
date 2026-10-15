import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ParseErrors } from './ParseErrors'
import { api } from '../api/client'
import type { Case } from '../types/case'
import type { ParseIssuesResponse } from '../types/parseIssues'

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

const mockIssues: ParseIssuesResponse = {
  parse_errors: [
    {
      id: 'err-1',
      evidence_file_id: 'ev-1',
      case_id: 'case-1',
      line_number: 2,
      raw_line: 'this line is not valid syslog at all',
      reason: 'unrecognized syslog line format',
      parser_name: 'syslog_auth',
      created_at: '2026-10-10T00:00:00Z',
      evidence_filename: 'auth.log',
    },
  ],
  parsing_gaps: [
    {
      id: 'gap-1',
      evidence_file_id: 'ev-1',
      gap_start_line: 1,
      gap_end_line: 3,
      description: 'Timestamp jump of 14400s between line 1 and 3',
      created_at: '2026-10-10T00:00:00Z',
      evidence_filename: 'auth.log',
    },
  ],
}

function renderParseErrors() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/parse-errors?case_id=case-1']}>
        <ParseErrors />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ParseErrors page', () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset()
    vi.mocked(api.get).mockImplementation((path: string) => {
      if (path === '/api/cases') return Promise.resolve([mockCase])
      if (path.includes('/parse-issues')) return Promise.resolve(mockIssues)
      return Promise.resolve([])
    })
  })

  it('shows malformed records with source evidence, line number, and reason', async () => {
    renderParseErrors()

    expect(await screen.findByText('this line is not valid syslog at all')).toBeInTheDocument()
    expect(screen.getByText('unrecognized syslog line format')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getAllByText('auth.log').length).toBeGreaterThan(0)
  })

  it('shows detected parsing gaps with line range and description', async () => {
    renderParseErrors()

    expect(await screen.findByText('1 – 3')).toBeInTheDocument()
    expect(
      screen.getByText('Timestamp jump of 14400s between line 1 and 3'),
    ).toBeInTheDocument()
  })

  it('shows an empty-state prompt when no case is selected', () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/parse-errors']}>
          <ParseErrors />
        </MemoryRouter>
      </QueryClientProvider>,
    )
    expect(
      screen.getByText('Select a case above to view its parse errors and detected gaps.'),
    ).toBeInTheDocument()
  })
})
