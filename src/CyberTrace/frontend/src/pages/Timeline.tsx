import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Case } from '../types/case'
import type { TimelineRecord, TimelineResponse } from '../types/timeline'
import { Table, type Column } from '../components/ui/Table'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'
import { Drawer } from '../components/ui/Drawer'

const SEVERITY_TO_BADGE: Record<string, 'info' | 'warning' | 'critical'> = {
  info: 'info',
  warning: 'warning',
  critical: 'critical',
}

function buildQueryString(caseId: string, params: Record<string, string>): string {
  const qs = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value) qs.set(key, value)
  }
  return `/api/cases/${caseId}/timeline?${qs.toString()}`
}

/** Searchable, filterable incident timeline -- the primary feature of the
 * app (PROJECT_PLAN.md section 1A.A), not a dashboard. Every filter here is
 * a real `GET /api/cases/{id}/timeline` query parameter; there is no
 * client-side mock filtering. */
export function Timeline() {
  const [searchParams, setSearchParams] = useSearchParams()
  const caseId = searchParams.get('case_id') ?? ''
  const [selectedRecord, setSelectedRecord] = useState<TimelineRecord | null>(null)

  const [q, setQ] = useState('')
  const [severity, setSeverity] = useState('')
  const [eventType, setEventType] = useState('')
  const [source, setSource] = useState('')
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')
  const [order, setOrder] = useState<'asc' | 'desc'>('asc')

  const { data: cases, isLoading: casesLoading } = useQuery({
    queryKey: ['cases'],
    queryFn: () => api.get<Case[]>('/api/cases'),
  })

  const filterParams = {
    q,
    severity,
    event_type: eventType,
    source,
    start_time: startTime,
    end_time: endTime,
    sort: 'event_time_utc',
    order,
  }

  const {
    data: timeline,
    isLoading: timelineLoading,
    error: timelineError,
  } = useQuery({
    queryKey: ['timeline', caseId, filterParams],
    queryFn: () =>
      api.get<TimelineResponse>(buildQueryString(caseId, filterParams)),
    enabled: Boolean(caseId),
  })

  const columns: Column<TimelineRecord>[] = [
    {
      key: 'event_time_utc',
      header: 'Timestamp (UTC)',
      render: (row) => (
        <div>
          <div className="font-mono text-xs">{row.event_time_utc}</div>
          <div className="text-[10px] text-slate-500">{row.original_timezone}</div>
        </div>
      ),
    },
    {
      key: 'source',
      header: 'Source',
      render: (row) => row.source_ip ?? row.user_or_actor ?? <span className="text-slate-500">—</span>,
    },
    { key: 'event_type', header: 'Event type', render: (row) => row.event_type },
    {
      key: 'severity',
      header: 'Severity',
      render: (row) => (
        <Badge status={SEVERITY_TO_BADGE[row.severity] ?? 'info'}>{row.severity}</Badge>
      ),
    },
    {
      key: 'parsing_status',
      header: 'Parsing status',
      render: (row) =>
        row.near_parse_gap ? (
          <Badge status="warning">Near parse gap</Badge>
        ) : (
          <Badge status="ok">Parsed</Badge>
        ),
    },
  ]

  const recordCount = timeline?.records.length ?? 0
  const total = timeline?.total ?? 0

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-slate-100">Timeline</h1>

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
        <Card title="Filters">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <label htmlFor="tl-q" className="mb-1 block text-xs text-slate-400">
                Search (message / raw line)
              </label>
              <input
                id="tl-q"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-navy-950 px-3 py-2 text-sm text-slate-100"
              />
            </div>
            <div>
              <label htmlFor="tl-severity" className="mb-1 block text-xs text-slate-400">
                Severity
              </label>
              <select
                id="tl-severity"
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-navy-950 px-3 py-2 text-sm text-slate-100"
              >
                <option value="">Any</option>
                <option value="info">info</option>
                <option value="warning">warning</option>
                <option value="critical">critical</option>
              </select>
            </div>
            <div>
              <label htmlFor="tl-event-type" className="mb-1 block text-xs text-slate-400">
                Event type
              </label>
              <input
                id="tl-event-type"
                value={eventType}
                onChange={(e) => setEventType(e.target.value)}
                placeholder="e.g. auth_failure"
                className="w-full rounded-md border border-slate-700 bg-navy-950 px-3 py-2 text-sm text-slate-100"
              />
            </div>
            <div>
              <label htmlFor="tl-source" className="mb-1 block text-xs text-slate-400">
                Source (IP / actor)
              </label>
              <input
                id="tl-source"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-navy-950 px-3 py-2 text-sm text-slate-100"
              />
            </div>
            <div>
              <label htmlFor="tl-start" className="mb-1 block text-xs text-slate-400">
                Start time (UTC)
              </label>
              <input
                id="tl-start"
                type="datetime-local"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-navy-950 px-3 py-2 text-sm text-slate-100"
              />
            </div>
            <div>
              <label htmlFor="tl-end" className="mb-1 block text-xs text-slate-400">
                End time (UTC)
              </label>
              <input
                id="tl-end"
                type="datetime-local"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-navy-950 px-3 py-2 text-sm text-slate-100"
              />
            </div>
          </div>
          <button
            type="button"
            onClick={() => setOrder((o) => (o === 'asc' ? 'desc' : 'asc'))}
            className="mt-3 text-xs text-accent-light hover:underline"
          >
            Sort: timestamp {order === 'asc' ? '↑ ascending' : '↓ descending'} (click to flip)
          </button>
        </Card>
      )}

      {!caseId ? (
        <p className="text-sm text-slate-400">Select a case above to view its timeline.</p>
      ) : (
        <>
          {timeline && (
            <p className="text-xs text-slate-400">
              Showing {recordCount} of {total} records in range
            </p>
          )}
          <Table
            columns={columns}
            rows={timeline?.records ?? []}
            rowKey={(row) => row.id}
            isLoading={timelineLoading}
            error={timelineError ? 'Failed to load timeline' : null}
            emptyMessage="No records match the current filters."
            onRowClick={(row) => setSelectedRecord(row)}
          />
        </>
      )}

      <Drawer
        open={selectedRecord !== null}
        title="Record detail"
        onClose={() => setSelectedRecord(null)}
      >
        {selectedRecord && (
          <div className="space-y-4 text-sm">
            <div>
              <h3 className="mb-1 text-xs uppercase tracking-wide text-slate-400">Raw line</h3>
              <pre className="whitespace-pre-wrap rounded border border-slate-700 bg-navy-950 p-3 font-mono text-xs text-slate-200">
                {selectedRecord.raw_line}
              </pre>
            </div>
            <div>
              <h3 className="mb-1 text-xs uppercase tracking-wide text-slate-400">
                Source evidence
              </h3>
              <p className="text-slate-200">{selectedRecord.evidence_filename}</p>
              <p className="font-mono text-xs text-slate-400">{selectedRecord.evidence_sha256}</p>
              <p className="text-xs text-slate-400">Line {selectedRecord.line_number}</p>
            </div>
            <div>
              <h3 className="mb-1 text-xs uppercase tracking-wide text-slate-400">
                Normalized fields
              </h3>
              <dl className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <dt className="text-slate-400">Event time (UTC)</dt>
                  <dd className="font-mono">{selectedRecord.event_time_utc}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-400">Original timezone</dt>
                  <dd>{selectedRecord.original_timezone}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-400">Event type</dt>
                  <dd>{selectedRecord.event_type}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-400">Severity</dt>
                  <dd>{selectedRecord.severity}</dd>
                </div>
              </dl>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  )
}
