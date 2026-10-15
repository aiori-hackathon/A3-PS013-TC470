import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { Evidence } from './Evidence'
import { api, ApiError } from '../api/client'
import type { Case } from '../types/case'
import type { EvidenceFile, EvidenceUploadResult } from '../types/evidence'

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

const mockEvidence: EvidenceFile = {
  id: 'ev-1',
  case_id: 'case-1',
  original_filename: 'auth.log',
  detected_format: 'syslog_auth',
  declared_format: null,
  sha256_hash: 'a'.repeat(64),
  byte_size: 100,
  uploaded_by: 'user-1',
  uploaded_at: '2026-10-10T00:00:00Z',
  source_timezone_assumption: 'UTC',
  notes: null,
}

function renderEvidence() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/evidence?case_id=case-1']}>
        <Evidence />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Evidence page ingestion summary', () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset()
    vi.mocked(api.postForm).mockReset()
    vi.mocked(api.get).mockImplementation((path: string) => {
      if (path === '/api/cases') return Promise.resolve([mockCase])
      if (path.includes('/evidence')) return Promise.resolve([mockEvidence])
      return Promise.resolve([])
    })
  })

  it('shows records parsed/failed/gaps after a successful upload', async () => {
    const uploadResult: EvidenceUploadResult = {
      evidence: mockEvidence,
      records_parsed: 5,
      records_failed: 1,
      gaps_detected: 2,
      automated_seconds: 0.01,
      manual_estimate_seconds: 90,
    }
    vi.mocked(api.postForm).mockResolvedValue(uploadResult)

    renderEvidence()

    await screen.findByText('Upload evidence file')
    const file = new File(['Oct 10 00:00:00 h p[1]: msg'], 'auth.log', { type: 'text/plain' })
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    expect(fileInput).toBeTruthy()
    await userEvent.upload(fileInput, file)

    const summary = await screen.findByTestId('ingestion-summary')
    expect(summary).toHaveTextContent('5')
    expect(summary).toHaveTextContent('1')
    expect(summary).toHaveTextContent('2')
  })

  it('shows an error message when upload fails', async () => {
    vi.mocked(api.postForm).mockRejectedValue(new ApiError('Unsupported file type', 400))

    renderEvidence()

    await screen.findByText('Upload evidence file')
    const file = new File(['bad'], 'bad.log', { type: 'text/plain' })
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    await userEvent.upload(fileInput, file)

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Unsupported file type')
    })
    expect(screen.queryByTestId('ingestion-summary')).not.toBeInTheDocument()
  })
})
