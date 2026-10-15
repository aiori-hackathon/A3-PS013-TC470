import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { useAuth } from '../../hooks/useAuth'

export function AppLayout() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-navy-950 md:flex">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-30 border-b border-white/[0.06] bg-navy-950/85 backdrop-blur-xl">
          <div className="mx-auto flex h-[68px] max-w-screen-2xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-10">
            <div className="flex min-w-0 items-center gap-3">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-accent/20 bg-accent/10 text-accent-light">
                <svg viewBox="0 0 24 24" className="h-[18px] w-[18px]" fill="none" aria-hidden="true">
                  <path d="M12 3 20 6v5c0 5-3.4 8.3-8 10-4.6-1.7-8-5-8-10V6l8-3Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
                  <path d="m9 12 2 2 4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </span>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold tracking-tight text-slate-100">
                  Incident workspace
                </p>
                <p className="hidden text-[11px] text-slate-500 sm:block">
                  Evidence-led security investigations
                </p>
              </div>
            </div>
            <div className="flex min-w-0 items-center gap-3">
              <span className="hidden items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-[11px] font-medium text-slate-400 sm:inline-flex">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.7)]" />
                PRIVATE WORKSPACE
              </span>
              <span className="hidden max-w-48 truncate text-xs text-slate-500 lg:block" title={user?.email}>
                {user?.email}
              </span>
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-accent/25 bg-accent/10 text-xs font-semibold text-accent-light" aria-label="Signed-in user">
                {user?.email?.slice(0, 1).toUpperCase() ?? '?'}
              </span>
            </div>
          </div>
        </header>
        <main className="mx-auto min-h-[calc(100vh-68px)] max-w-screen-2xl px-4 pb-28 pt-7 sm:px-6 sm:pt-9 md:pb-10 lg:px-10">
          <Outlet />
          <footer className="mt-16 border-t border-white/[0.06] pt-5 text-[11px] text-slate-600">
            CyberTrace <span className="px-1.5 text-slate-700">/</span> Evidence first. Context always.
          </footer>
        </main>
      </div>
    </div>
  )
}
