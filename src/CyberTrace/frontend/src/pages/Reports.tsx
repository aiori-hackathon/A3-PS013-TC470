import { useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../api/client'
import type { Case } from '../types/case'
import type { Report } from '../types/report'
import { Table, type Column } from '../components/ui/Table'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'

const FORMAT_LABEL: Record<Report['format'], string> = {
  json: 'JSON (full export)',
  csv: 'CSV (zipped)',
  pdf: 'PDF (readable report)',
}

/** Report export page, per PROJECT_PLAN.md section 10: JSON (full case
 * export), CSV (zipped timeline + parse errors), and PDF (human-readable
 * report) -- all generated from the same real DB rows shown elsewhere in
 * the app, no separate invented statistics. */
export function Reports() {
  const [searchParams, setSearchParams] = useSearchParams()
  const caseId = searchParams.get('case_id') ?? ''
  const queryClient = useQueryClient()

  const { data: cases, isLoading: casesLoading } = useQuery({
    queryKey: ['cases'],
    queryFn: () => api.get<Case[]>('/api/cases'),
  })

  const {
    data: reports,
    isLoading: reportsLoading,
    error: reportsError,
  } = useQuery({
    queryKey: ['reports', caseId],
    queryFn: () => api.get<Report[]>(`/api/cases/${caseId}/reports`),
    enabled: Boolean(caseId),
  })

  const generate = useMutation({
    mutationFn: (format: Report['format']) =>
      api.post<Report>(`/api/cases/${caseId}/reports?format=${format}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports', caseId] })
    },
  })

  async function handleDownload(reportId: string, format: Report['format']) {
    const ext = format === 'csv' ? 'zip' : format
    const { blob, filename } = await api.download(`/api/reports/${reportId}/download`)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename ?? `cybertrace_report.${ext}`
    link.click()
    URL.revokeObjectURL(url)
  }

  const columns: Column<Report>[] = [
    { key: 'format', header: 'Format', render: (row) => FORMAT_LABEL[row.format] },
    {
      key: 'generated_at',
      header: 'Generated (UTC)',
      render: (row) => (
        <span className="font-mono text-xs">{new Date(row.generated_at).toISOString()}</span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <Button variant="secondary" onClick={() => handleDownload(row.id, row.format)}>
          Download
        </Button>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-slate-100">Reports</h1>

      <Card title="Select case">
        {casesLoading ? (
          <p className="text-sm text-slate-400">Loading cases…</p>
        ) : (
          <select
            value={caseId}
            onChange={(e) => setSearchParams(e.target.value ? { case_id: e.target.value } : {})}
            className="w-full max-w-md rounded-md border border-slate-700 bg-navy-950 px-3 py-2 text-sm text-slate-100"
          >
            <option value="">— Select a case —</option>
            {(cases ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
                {c.is_synthetic ? ' (synthetic)' : ''}
              </option>
            ))}
          </select>
        )}
      </Card>

      {caseId && (
        <Card title="Generate a new report">
          <div className="flex flex-wrap gap-3">
            <Button onClick={() => generate.mutate('json')} disabled={generate.isPending}>
              Generate JSON
            </Button>
            <Button onClick={() => generate.mutate('csv')} disabled={generate.isPending}>
              Generate CSV
            </Button>
            <Button onClick={() => generate.mutate('pdf')} disabled={generate.isPending}>
              Generate PDF
            </Button>
          </div>
          {generate.isPending && (
            <p role="status" className="mt-2 text-sm text-slate-400">
              Generating report…
            </p>
          )}
          {generate.isError && (
            <div
              role="alert"
              className="mt-2 max-w-md rounded border border-status-critical/40 bg-status-critical/10 px-3 py-2 text-sm text-status-critical"
            >
              {generate.error instanceof ApiError ? generate.error.message : 'Failed to generate report'}
            </div>
          )}
        </Card>
      )}

      {!caseId ? (
        <p className="text-sm text-slate-400">Select a case above to generate or download reports.</p>
      ) : (
        <Table
          columns={columns}
          rows={reports ?? []}
          rowKey={(row) => row.id}
          isLoading={reportsLoading}
          error={reportsError ? 'Failed to load reports' : null}
          emptyMessage="No reports generated yet for this case."
        />
      )}
    </div>
  )
}
