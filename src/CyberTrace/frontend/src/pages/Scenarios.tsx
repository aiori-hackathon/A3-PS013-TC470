import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { api, ApiError } from '../api/client'
import type { ScenarioInfo, ScenarioLoadResult } from '../types/scenario'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'

/** Scenarios page, per PROJECT_PLAN.md section 9: explains what each of
 * the 3 synthetic demo scenarios is, makes clear it is not real incident
 * data, and loads it via the real `/api/scenarios/{key}/load` endpoint
 * (reproducible from a committed sample log, not mystery seed data). */
export function Scenarios() {
  const navigate = useNavigate()
  const [loadResult, setLoadResult] = useState<ScenarioLoadResult | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [loadingKey, setLoadingKey] = useState<string | null>(null)

  const {
    data: scenarios,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['scenarios'],
    queryFn: () => api.get<ScenarioInfo[]>('/api/scenarios'),
  })

  const load = useMutation({
    mutationFn: (key: string) => api.post<ScenarioLoadResult>(`/api/scenarios/${key}/load`),
    onSuccess: (result) => {
      setLoadResult(result)
      setLoadError(null)
      setLoadingKey(null)
    },
    onError: (err) => {
      setLoadError(err instanceof ApiError ? err.message : 'Failed to load scenario')
      setLoadResult(null)
      setLoadingKey(null)
    },
  })

  function handleLoad(key: string) {
    setLoadingKey(key)
    setLoadResult(null)
    setLoadError(null)
    load.mutate(key)
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-slate-100">Scenarios</h1>
      <p className="max-w-2xl text-sm text-slate-400">
        These are reproducible synthetic incident scenarios for demonstration and testing. They
        are clearly labeled <Badge status="synthetic">Synthetic scenario</Badge> everywhere they
        appear and are not real incident data.
      </p>

      {isLoading && <p className="text-sm text-slate-400">Loading scenarios…</p>}
      {error && (
        <div
          role="alert"
          className="max-w-md rounded border border-status-critical/40 bg-status-critical/10 px-3 py-2 text-sm text-status-critical"
        >
          Failed to load scenarios.
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {(scenarios ?? []).map((s) => (
          <Card key={s.key} title={s.name}>
            <p className="mb-3 text-sm text-slate-400">{s.description}</p>
            <Button onClick={() => handleLoad(s.key)} disabled={load.isPending}>
              {loadingKey === s.key && load.isPending ? 'Loading…' : 'Load scenario'}
            </Button>
          </Card>
        ))}
      </div>

      {loadError && (
        <div
          role="alert"
          className="max-w-md rounded border border-status-critical/40 bg-status-critical/10 px-3 py-2 text-sm text-status-critical"
        >
          {loadError}
        </div>
      )}

      {loadResult && (
        <div
          data-testid="scenario-load-summary"
          className="max-w-md space-y-2 rounded border border-status-ok/30 bg-status-ok/10 px-3 py-3 text-sm"
        >
          <p className="font-medium text-status-ok">
            Loaded case "{loadResult.case.name}"
          </p>
          <p className="text-xs text-slate-300">
            {loadResult.records_parsed} records parsed, {loadResult.records_failed} failed,{' '}
            {loadResult.gaps_detected} gaps detected.
          </p>
          <Button
            variant="secondary"
            onClick={() => navigate(`/timeline?case_id=${loadResult.case.id}`)}
          >
            View timeline
          </Button>
        </div>
      )}
    </div>
  )
}
