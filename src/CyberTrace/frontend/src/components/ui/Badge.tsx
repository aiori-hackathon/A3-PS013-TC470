import type { ReactNode } from 'react'

type Status = 'ok' | 'warning' | 'critical' | 'info' | 'synthetic'

interface BadgeProps {
  status: Status
  children: ReactNode
}

const statusClasses: Record<Status, string> = {
  ok: 'bg-status-ok/[0.1] text-emerald-300 border-status-ok/20',
  warning: 'bg-status-warning/[0.1] text-amber-300 border-status-warning/20',
  critical: 'bg-status-critical/[0.1] text-red-300 border-status-critical/20',
  info: 'bg-white/[0.04] text-slate-300 border-white/[0.1]',
  // Synthetic scenario badge uses the accent color, not status colors, so
  // it reads as a label rather than a pass/fail indicator.
  synthetic: 'bg-accent/[0.1] text-accent-light border-accent/20',
}

/** Shared status Badge (PROJECT_PLAN.md section 1). Used for severity,
 * parsing status, verification status, and the "Synthetic scenario" label. */
export function Badge({ status, children }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-semibold leading-none tracking-wide ${statusClasses[status]}`}
    >
      {children}
    </span>
  )
}
