interface ComingSoonProps {
  title: string
  phase: string
}

/** Used for pages whose backend endpoints are not implemented yet. Shown
 * instead of fake/placeholder data, per the anti-pattern checklist in
 * PROJECT_PLAN.md section 1A: never ship a page with only mock data. */
export function ComingSoon({ title, phase }: ComingSoonProps) {
  return (
    <div className="max-w-xl">
      <h1 className="mb-2 text-xl font-semibold text-slate-100">{title}</h1>
      <div className="rounded-lg border border-slate-700 bg-slate-800/60 p-4 text-sm text-slate-400">
        This page will be built in {phase}, once the corresponding backend
        endpoints exist. It intentionally shows no data yet rather than
        placeholder content.
      </div>
    </div>
  )
}
