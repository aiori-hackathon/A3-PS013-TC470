import type { ReactNode } from 'react'

interface DrawerProps {
  open: boolean
  title: string
  onClose: () => void
  children: ReactNode
}

/** Right-side detail drawer, used for record/evidence detail views
 * (PROJECT_PLAN.md section 1A: row-click opens detail incl. raw_line). */
export function Drawer({ open, title, onClose, children }: DrawerProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true">
      <button
        aria-label="Close panel"
        onClick={onClose}
        className="absolute inset-0 bg-black/50"
      />
      <div className="relative h-full w-full max-w-lg overflow-y-auto border-l border-slate-700 bg-navy-900 p-5 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-100">{title}</h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}
