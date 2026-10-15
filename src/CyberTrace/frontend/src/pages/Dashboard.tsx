import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { HealthStatus } from '../types/health'
import type { Case } from '../types/case'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'

function ArrowIcon() {
  return (
    <svg viewBox="0 0 20 20" className="h-4 w-4 transition-transform group-hover:translate-x-0.5" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
      <path d="M3.5 10h13M11 4.5l5.5 5.5-5.5 5.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

/** Overview uses live case and health data rather than invented activity metrics. */
export function Dashboard() {
  const {
    data: health,
    isLoading: healthLoading,
    error: healthError,
  } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get<HealthStatus>('/api/health'),
  })
  const {
    data: cases,
    isLoading: casesLoading,
    error: casesError,
  } = useQuery({
    queryKey: ['cases'],
    queryFn: () => api.get<Case[]>('/api/cases'),
  })

  const ownedCases = cases?.filter((item) => !item.is_synthetic).length ?? 0
  const syntheticCases = cases?.filter((item) => item.is_synthetic).length ?? 0

  return (
    <div className="space-y-7">
      <section className="relative isolate overflow-hidden rounded-[26px] border border-white/[0.09] bg-gradient-to-br from-[#14233a] via-[#101c2e] to-[#0e1726] px-6 py-7 shadow-[0_24px_80px_rgba(0,0,0,0.2)] sm:px-9 sm:py-9">
        <div className="pointer-events-none absolute -right-16 -top-28 -z-10 h-80 w-80 rounded-full border border-blue-400/[0.08] bg-blue-400/[0.025] shadow-[0_0_0_40px_rgba(96,165,250,0.02),0_0_0_80px_rgba(96,165,250,0.015)]" />
        <div className="pointer-events-none absolute bottom-0 right-0 -z-10 h-48 w-1/2 bg-[radial-gradient(ellipse_at_bottom_right,rgba(59,130,246,0.13),transparent_70%)]" />

        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-accent/20 bg-accent/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.15em] text-accent-light">
            Incident response
          </span>
          <span className="text-[11px] text-slate-500">Evidence first. Context always.</span>
        </div>
        <div className="mt-6 max-w-2xl">
          <h1 className="text-3xl font-semibold leading-tight tracking-[-0.04em] text-white sm:text-[40px]">
            Every signal has a story.
            <span className="mt-1 block text-slate-400">Make yours easier to investigate.</span>
          </h1>
          <p className="mt-4 max-w-xl text-sm leading-6 text-slate-400 sm:text-[15px]">
            Preserve the original evidence, bring events into one searchable timeline, and keep
            every finding traceable back to its source.
          </p>
        </div>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link
            to="/cases"
            className="group inline-flex min-h-11 items-center gap-2 rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-white shadow-[0_6px_20px_rgba(59,130,246,0.24)] transition-all hover:-translate-y-0.5 hover:bg-blue-500"
          >
            Open investigations <ArrowIcon />
          </Link>
          <Link
            to="/scenarios"
            className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-white/[0.1] bg-white/[0.035] px-4 py-2.5 text-sm font-medium text-slate-200 transition-colors hover:bg-white/[0.08]"
          >
            Explore demo scenarios
          </Link>
        </div>
      </section>

      <section aria-label="Workspace summary" className="grid gap-4 sm:grid-cols-3">
        <Link
          to="/cases"
          className="group rounded-2xl border border-white/[0.08] bg-[#101a2b]/75 p-5 transition-all hover:-translate-y-0.5 hover:border-white/[0.14] hover:bg-[#121f33]"
        >
          <div className="flex items-start justify-between">
            <span className="grid h-10 w-10 place-items-center rounded-xl border border-blue-400/10 bg-blue-400/[0.08] text-blue-300">
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
                <rect x="3.5" y="5.5" width="17" height="15" rx="2" />
                <path d="M8 5.5V4.7A1.7 1.7 0 0 1 9.7 3h4.6A1.7 1.7 0 0 1 16 4.7v.8M3.5 10h17" />
              </svg>
            </span>
            <span className="text-slate-600 transition-colors group-hover:text-slate-300">
              <ArrowIcon />
            </span>
          </div>
          <p className="mt-5 text-3xl font-semibold tracking-tight text-white">
            {casesLoading ? '—' : casesError ? '!' : ownedCases}
          </p>
          <p className="mt-1 text-xs text-slate-500">Your investigations</p>
        </Link>

        <Link
          to="/scenarios"
          className="group rounded-2xl border border-white/[0.08] bg-[#101a2b]/75 p-5 transition-all hover:-translate-y-0.5 hover:border-white/[0.14] hover:bg-[#121f33]"
        >
          <div className="flex items-start justify-between">
            <span className="grid h-10 w-10 place-items-center rounded-xl border border-violet-400/10 bg-violet-400/[0.08] text-violet-300">
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
                <path d="M4 19V5M4 19h16M7 15l3.5-4 3 2 4.5-6" />
                <circle cx="7" cy="15" r="1" /><circle cx="10.5" cy="11" r="1" /><circle cx="13.5" cy="13" r="1" /><circle cx="18" cy="7" r="1" />
              </svg>
            </span>
            <span className="text-slate-600 transition-colors group-hover:text-slate-300">
              <ArrowIcon />
            </span>
          </div>
          <p className="mt-5 text-3xl font-semibold tracking-tight text-white">
            {casesLoading ? '—' : casesError ? '!' : syntheticCases}
          </p>
          <p className="mt-1 text-xs text-slate-500">Shared demo investigations</p>
        </Link>

        <Card className="p-5 sm:p-5">
          <div className="flex items-start justify-between">
            <span className="grid h-10 w-10 place-items-center rounded-xl border border-emerald-400/10 bg-emerald-400/[0.08] text-emerald-300">
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
                <path d="M12 3 20 6v5c0 5-3.4 8.3-8 10-4.6-1.7-8-5-8-10V6l8-3Z" strokeLinejoin="round" />
                <path d="m9 12 2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </span>
            <Badge
              status={
                healthLoading
                  ? 'info'
                  : health?.db_connected
                    ? 'ok'
                    : 'critical'
              }
            >
              {healthLoading ? 'Checking' : health?.db_connected ? 'Operational' : 'Attention'}
            </Badge>
          </div>
          <p className="mt-5 text-sm font-semibold text-slate-100">Platform health</p>
          <p className="mt-1 text-xs text-slate-500">
            {healthError
              ? 'Could not reach the API'
              : healthLoading
                ? 'Checking API and database'
                : health?.db_connected
                  ? 'API and database connected'
                  : 'Database connection unavailable'}
          </p>
        </Card>
      </section>

      {(casesError || healthError || (health && !health.db_connected)) && (
        <div
          role="alert"
          className="rounded-2xl border border-status-critical/20 bg-status-critical/[0.06] px-4 py-3 text-sm text-red-200"
        >
          {casesError
            ? 'Your investigations could not be loaded. Check the API connection and try again.'
            : healthError
              ? 'Could not reach the CyberTrace API.'
              : health?.db_error ?? 'The database connection is unavailable.'}
        </div>
      )}

      <section>
        <div className="mb-4 flex items-end justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-600">
              Investigation tools
            </p>
            <h2 className="mt-1 text-lg font-semibold tracking-tight text-white">Pick up where it matters</h2>
          </div>
          <span className="hidden text-xs text-slate-600 sm:block">Your evidence stays yours</span>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {[
            {
              to: '/timeline',
              number: '01',
              title: 'Search the timeline',
              text: 'Trace events across a case with real filters, UTC timestamps, and source context.',
              color: 'text-blue-300',
              icon: <><path d="M10.5 18a7.5 7.5 0 1 1 5.3-2.2" /><path d="m16 16 4.5 4.5M7.5 10.5h6M7.5 13.5h4" /></>,
            },
            {
              to: '/evidence',
              number: '02',
              title: 'Review evidence',
              text: 'Upload original logs, inspect parsed results, and verify file integrity on demand.',
              color: 'text-emerald-300',
              icon: <><path d="M12 3.5 20 7v5c0 4.5-3 7.5-8 9-5-1.5-8-4.5-8-9V7l8-3.5Z" /><path d="m9 12 2 2 4-4" /></>,
            },
            {
              to: '/reports',
              number: '03',
              title: 'Share a report',
              text: 'Export the case as machine-readable JSON, zipped CSV, or a readable PDF.',
              color: 'text-violet-300',
              icon: <><path d="M6 3.5h8l4 4v13H6a2 2 0 0 1-2-2v-13a2 2 0 0 1 2-2Z" /><path d="M14 3.5v4h4M8 12h8M8 16h8" /></>,
            },
          ].map((tool) => (
            <Link
              key={tool.to}
              to={tool.to}
              className="group rounded-2xl border border-white/[0.07] bg-white/[0.02] p-5 transition-all hover:-translate-y-0.5 hover:border-white/[0.14] hover:bg-white/[0.035]"
            >
              <div className="flex items-center justify-between">
                <span className={`grid h-9 w-9 place-items-center rounded-xl bg-white/[0.04] ${tool.color}`}>
                  <svg viewBox="0 0 24 24" className="h-[18px] w-[18px]" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    {tool.icon}
                  </svg>
                </span>
                <span className="font-mono text-[10px] text-slate-700">{tool.number}</span>
              </div>
              <h3 className="mt-4 text-sm font-semibold text-slate-100">{tool.title}</h3>
              <p className="mt-1.5 text-xs leading-5 text-slate-500">{tool.text}</p>
              <span className="mt-4 inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 transition-colors group-hover:text-accent-light">
                Open tool <ArrowIcon />
              </span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
