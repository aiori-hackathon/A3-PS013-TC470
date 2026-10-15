import type { ReactNode } from 'react'

interface CardProps {
  title?: string
  children: ReactNode
  className?: string
}

/** Used only for grouping forms/details -- not as a decorative dashboard
 * tile (PROJECT_PLAN.md section 1). */
export function Card({ title, children, className = '' }: CardProps) {
  return (
    <section
      className={`rounded-2xl border border-white/[0.08] bg-[#101a2b]/85 p-5 shadow-[0_12px_32px_rgba(0,0,0,0.12)] sm:p-6 ${className}`}
    >
      {title && (
        <h3 className="mb-4 text-[13px] font-semibold tracking-wide text-slate-200">{title}</h3>
      )}
      {children}
    </section>
  )
}
