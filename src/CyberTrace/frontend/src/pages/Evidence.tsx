import { useRef, useState, type ChangeEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../api/client'
import type { Case } from '../types/case'
import type { EvidenceFile, EvidenceUploadResult, EvidenceVerifyResult } from '../types/evidence'
import { Table, type Column } from '../components/ui/Table'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(1)} KB`
  return `${(kb / 1024).toFixed(1)} MB`
}

function truncateHash(hash: string): string {
  return `${hash.slice(0, 12)}…${hash.slice(-8)}`
}

/** Evidence list + upload for a specific case, per PROJECT_PLAN.md section
 * 1A.B: filename, detected format, size, uploaded-at (UTC), SHA-256 (with
 * copy), timezone assumption, and a live "Verify integrity" check -- never a
 * cached pass/fail flag. */
export function Evidence() {
  const [searchParams, setSearchParams] = useSearchParams()
  const caseId = searchParams.get('case_id') ?? ''
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [lastUploadResult, setLastUploadResult] = useState<EvidenceUploadResult | null>(null)
  const [verifyResults, setVerifyResults] = useState<Record<string, EvidenceVerifyResult>>({})
  const [copiedHash, setCopiedHash] = useState<string | null>(null)

  const { data: cases, isLoading: casesLoading } = useQuery({
    queryKey: ['cases'],
    queryFn: () => api.get<Case[]>('/api/cases'),
  })

  const {
    data: evidence,
    isLoading: evidenceLoading,
    error: evidenceError,
  } = useQuery({
    queryKey: ['evidence', caseId],
    queryFn: () => api.get<EvidenceFile[]>(`/api/cases/${caseId}/evidence`),
    enabled: Boolean(caseId),
  })

  const upload = useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      return api.postForm<EvidenceUploadResult>(
        `/api/cases/${caseId}/evidence?timezone_assumption=UTC`,
        formData,
      )
    },
    onSuccess: (result) => {
      setUploadError(null)
      setLastUploadResult(result)
      if (fileInputRef.current) fileInputRef.current.value = ''
      queryClient.invalidateQueries({ queryKey: ['evidence', caseId] })
      queryClient.invalidateQueries({ queryKey: ['cases'] })
    },
    onError: (err) => {
      setLastUploadResult(null)
      setUploadError(err instanceof ApiError ? err.message : 'Upload failed')
    },
  })

  const verify = useMutation({
    mutationFn: (evidenceId: string) =>
      api.get<EvidenceVerifyResult>(`/api/evidence/${evidenceId}/verify`),
    onSuccess: (result) => {
      setVerifyResults((prev) => ({ ...prev, [result.evidence_id]: result }))
    },
  })

  async function handleDownload(id: string, fallbackName: string) {
    const { blob, filename } = await api.download(`/api/evidence/${id}/download`)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename ?? fallbackName
    link.click()
    URL.revokeObjectURL(url)
  }

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) {
      setLastUploadResult(null)
      upload.mutate(file)
    }
  }

  function handleCopyHash(hash: string) {
    navigator.clipboard.writeText(hash).then(() => {
      setCopiedHash(hash)
      setTimeout(() => setCopiedHash(null), 1500)
    })
  }

  const columns: Column<EvidenceFile>[] = [
    { key: 'original_filename', header: 'Filename', render: (row) => row.original_filename },
    {
      key: 'detected_format',
      header: 'Detected format',
      render: (row) =>
        row.detected_format === 'unknown' ? (
          <Badge status="warning">unknown</Badge>
        ) : (
          row.detected_format
        ),
    },
    { key: 'byte_size', header: 'Size', render: (row) => formatBytes(row.byte_size) },
    {
      key: 'uploaded_at',
      header: 'Uploaded (UTC)',
      render: (row) => (
        <span className="font-mono text-xs">{new Date(row.uploaded_at).toISOString()}</span>
      ),
    },
    {
      key: 'sha256_hash',
      header: 'SHA-256',
      render: (row) => (
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs">{truncateHash(row.sha256_hash)}</span>
          <button
            type="button"
            onClick={() => handleCopyHash(row.sha256_hash)}
            className="text-xs text-accent-light hover:underline"
          >
            {copiedHash === row.sha256_hash ? 'Copied!' : 'Copy'}
          </button>
        </div>
      ),
    },
    {
      key: 'source_timezone_assumption',
      header: 'Timezone assumption',
      render: (row) => row.source_timezone_assumption,
    },
    {
      key: 'verification',
      header: 'Verification',
      render: (row) => {
        const result = verifyResults[row.id]
        if (!result) return <Badge status="info">Not yet verified</Badge>
        return result.verified ? (
          <Badge status="ok">Verified</Badge>
        ) : (
          <div className="space-y-1">
            <Badge status="critical">Hash mismatch</Badge>
            {result.error && <p className="text-xs text-status-critical">{result.error}</p>}
          </div>
        )
      },
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={() => verify.mutate(row.id)}
            disabled={verify.isPending}
          >
            Verify integrity
          </Button>
          <Button variant="ghost" onClick={() => handleDownload(row.id, row.original_filename)}>
            Download
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-slate-100">Evidence</h1>

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
        <Card title="Upload evidence file">
          <div className="space-y-2">
            <input
              ref={fileInputRef}
              type="file"
              accept=".log,.txt,.json"
              onChange={handleFileChange}
              disabled={upload.isPending}
              className="block text-sm text-slate-300 file:mr-3 file:rounded-md file:border file:border-slate-700 file:bg-slate-800 file:px-3 file:py-1.5 file:text-sm file:text-slate-100"
            />
            {upload.isPending && (
              <p role="status" className="text-sm text-slate-400">
                Uploading and parsing…
              </p>
            )}
            {uploadError && (
              <div
                role="alert"
                className="max-w-md rounded border border-status-critical/40 bg-status-critical/10 px-3 py-2 text-sm text-status-critical"
              >
                {uploadError}
              </div>
            )}
            {lastUploadResult && (
              <div
                data-testid="ingestion-summary"
                className="max-w-md space-y-1 rounded border border-status-ok/30 bg-status-ok/10 px-3 py-2 text-sm"
              >
                <p className="font-medium text-status-ok">
                  Uploaded "{lastUploadResult.evidence.original_filename}"
                </p>
                <dl className="grid grid-cols-3 gap-2 text-xs text-slate-300">
                  <div>
                    <dt className="text-slate-400">Records parsed</dt>
                    <dd className="font-mono">{lastUploadResult.records_parsed}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Records failed</dt>
                    <dd className="font-mono">{lastUploadResult.records_failed}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-400">Gaps detected</dt>
                    <dd className="font-mono">{lastUploadResult.gaps_detected}</dd>
                  </div>
                </dl>
                <p className="pt-1 text-[11px] text-slate-400">
                  Automated parsing took{' '}
                  <span className="font-mono">
                    {lastUploadResult.automated_seconds.toFixed(2)}s
                  </span>{' '}
                  (measured). Manual triage of this many lines is estimated at{' '}
                  <span className="font-mono">
                    {Math.round(lastUploadResult.manual_estimate_seconds / 60)} min
                  </span>{' '}
                  (assumption: ~15s/line reviewed by hand, not measured).
                </p>
              </div>
            )}
          </div>
        </Card>
      )}

      {!caseId ? (
        <p className="text-sm text-slate-400">Select a case above to view its evidence files.</p>
      ) : (
        <Table
          columns={columns}
          rows={evidence ?? []}
          rowKey={(row) => row.id}
          isLoading={evidenceLoading}
          error={evidenceError ? 'Failed to load evidence' : null}
          emptyMessage="No evidence uploaded yet for this case."
        />
      )}
    </div>
  )
}
