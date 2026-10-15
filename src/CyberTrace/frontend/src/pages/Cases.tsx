import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../api/client'
import type { Case } from '../types/case'
import { Table, type Column } from '../components/ui/Table'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'

/** Cases list + create form. Case detail / delete happens inline here since
 * there is no dedicated case-detail route yet (Evidence page links back to
 * a case by id). Real data only -- no placeholder rows. */
export function Cases() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const {
    data: cases,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['cases'],
    queryFn: () => api.get<Case[]>('/api/cases'),
  })

  const createCase = useMutation({
    mutationFn: (payload: { name: string; description: string | null }) =>
      api.post<Case>('/api/cases', payload),
    onSuccess: () => {
      setName('')
      setDescription('')
      setFormError(null)
      queryClient.invalidateQueries({ queryKey: ['cases'] })
    },
    onError: (err) => {
      setFormError(err instanceof ApiError ? err.message : 'Failed to create case')
    },
  })

  const deleteCase = useMutation({
    mutationFn: (caseId: string) => api.delete<void>(`/api/cases/${caseId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cases'] }),
  })

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) {
      setFormError('Case name is required')
      return
    }
    createCase.mutate({ name: name.trim(), description: description.trim() || null })
  }

  const columns: Column<Case>[] = [
    {
      key: 'name',
      header: 'Name',
      render: (row) => (
        <div className="flex items-center gap-2">
          <span>{row.name}</span>
          {row.is_synthetic && <Badge status="synthetic">Synthetic scenario</Badge>}
        </div>
      ),
    },
    {
      key: 'description',
      header: 'Description',
      render: (row) => row.description ?? <span className="text-slate-500">—</span>,
    },
    {
      key: 'created_at',
      header: 'Created (UTC)',
      render: (row) => (
        <span className="font-mono text-xs">{new Date(row.created_at).toISOString()}</span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={(e) => {
              e.stopPropagation()
              navigate(`/evidence?case_id=${row.id}`)
            }}
          >
            View evidence
          </Button>
          {!row.is_synthetic && (
            <Button
              variant="destructive"
              onClick={(e) => {
                e.stopPropagation()
                if (confirm(`Delete case "${row.name}"? This cannot be undone.`)) {
                  deleteCase.mutate(row.id)
                }
              }}
            >
              Delete
            </Button>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-slate-100">Cases</h1>

      <Card title="New case">
        <form onSubmit={handleSubmit} className="space-y-3" noValidate>
          <div>
            <label htmlFor="case-name" className="mb-1 block text-sm text-slate-300">
              Name
            </label>
            <input
              id="case-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full max-w-md rounded-md border border-slate-700 bg-navy-950 px-3 py-2 text-sm text-slate-100"
            />
          </div>
          <div>
            <label htmlFor="case-description" className="mb-1 block text-sm text-slate-300">
              Description (optional)
            </label>
            <textarea
              id="case-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full max-w-md rounded-md border border-slate-700 bg-navy-950 px-3 py-2 text-sm text-slate-100"
            />
          </div>
          {formError && (
            <div
              role="alert"
              className="max-w-md rounded border border-status-critical/40 bg-status-critical/10 px-3 py-2 text-sm text-status-critical"
            >
              {formError}
            </div>
          )}
          <Button type="submit" disabled={createCase.isPending}>
            {createCase.isPending ? 'Creating…' : 'Create case'}
          </Button>
        </form>
      </Card>

      <Table
        columns={columns}
        rows={cases ?? []}
        rowKey={(row) => row.id}
        isLoading={isLoading}
        error={error ? 'Failed to load cases' : null}
        emptyMessage="No cases yet. Create one above to get started."
      />
    </div>
  )
}
