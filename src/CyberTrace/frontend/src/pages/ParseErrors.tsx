import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Case } from '../types/case'
import type { ParseErrorItem, ParseIssuesResponse, ParsingGapItem } from '../types/parseIssues'
import { Table, type Column } from '../components/ui/Table'
import { Card } from '../components/ui/Card'

/** "Parse Errors & Limitations" view, per PROJECT_PLAN.md section 1A.C:
 * malformed records and detected gaps are first-class, visible UI --
 * never buried or omitted from navigation. Real data from
 * GET /api/cases/{id}/parse-issues, no placeholder content. */
export function ParseErrors() {
  const [searchParams, setSearchParams] = useSearchParams()
  const caseId = searchParams.get('case_id') ?? ''

  const { data: cases, isLoading: casesLoading } = useQuery({
    queryKey: ['cases'],
    queryFn: () => api.get<Case[]>('/api/cases'),
  })

  const {
    data: issues,
    isLoading: issuesLoading,
    error: issuesError,
  } = useQuery({
    queryKey: ['parse-issues', caseId],
    queryFn: () => api.get<ParseIssuesResponse>(`/api/cases/${caseId}/parse-issues`),
    enabled: Boolean(caseId),
  })

  const errorColumns: Column<ParseErrorItem>[] = [
    { key: 'evidence_filename', header: 'Source evidence', render: (row) => row.evidence_filename },
    { key: 'line_number', header: 'Line', render: (row) => row.line_number },
    {
      key: 'raw_line',
      header: 'Raw line',
      render: (row) => <code className="font-mono text-xs">{row.raw_line}</code>,
    },
    { key: 'reason', header: 'Reason', render: (row) => row.reason },
    { key: 'parser_name', header: 'Parser', render: (row) => row.parser_name },
  ]

  const gapColumns: Column<ParsingGapItem>[] = [
    { key: 'evidence_filename', header: 'Source evidence', render: (row) => row.evidence_filename },
    {
      key: 'range',
      header: 'Line range',
      render: (row) => `${row.gap_start_line ?? '?'} – ${row.gap_end_line ?? '?'}`,
    },
    { key: 'description', header: 'Description', render: (row) => row.description },
  ]

  const errorCount = issues?.parse_errors.length ?? 0
  const gapCount = issues?.parsing_gaps.length ?? 0

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-slate-100">Parse Errors &amp; Limitations</h1>

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

      {!caseId ? (
        <p className="text-sm text-slate-400">
          Select a case above to view its parse errors and detected gaps.
        </p>
      ) : (
        <>
          <p className="text-xs text-slate-400">
            {errorCount} malformed line{errorCount === 1 ? '' : 's'}, {gapCount} detected gap
            {gapCount === 1 ? '' : 's'} for this case.
          </p>

          <Card title="Malformed records">
            <Table
              columns={errorColumns}
              rows={issues?.parse_errors ?? []}
              rowKey={(row) => row.id}
              isLoading={issuesLoading}
              error={issuesError ? 'Failed to load parse errors' : null}
              emptyMessage="No malformed records for this case."
            />
          </Card>

          <Card title="Detected parsing gaps">
            <Table
              columns={gapColumns}
              rows={issues?.parsing_gaps ?? []}
              rowKey={(row) => row.id}
              isLoading={issuesLoading}
              error={issuesError ? 'Failed to load parsing gaps' : null}
              emptyMessage="No gaps detected for this case."
            />
          </Card>
        </>
      )}
    </div>
  )
}
