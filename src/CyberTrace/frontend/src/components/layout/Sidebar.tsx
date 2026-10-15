import { NavLink } from 'react-router-dom'
import { Logo } from './Logo'
import { useAuth } from '../../hooks/useAuth'

const NAV_ITEMS = [
  {
    to: '/',
    label: 'Overview',
    end: true,
    icon: (
      <>
        <rect x="3.5" y="3.5" width="7" height="7" rx="1.5" />
        <rect x="13.5" y="3.5" width="7" height="4" rx="1.5" />
        <rect x="13.5" y="10.5" width="7" height="10" rx="1.5" />
        <rect x="3.5" y="13.5" width="7" height="7" rx="1.5" />
      </>
    ),
  },
  {
    to: '/cases',
    label: 'Cases',
    icon: (
      <>
        <rect x="3.5" y="5.5" width="17" height="15" rx="2" />
        <path d="M8 5.5V4.7A1.7 1.7 0 0 1 9.7 3h4.6A1.7 1.7 0 0 1 16 4.7v.8M3.5 10h17M10 10v2h4v-2" />
      </>
    ),
  },
  {
    to: '/evidence',
    label: 'Evidence',
    icon: (
      <>
        <path d="M12 3.5 20 7v5c0 4.5-3 7.5-8 9-5-1.5-8-4.5-8-9V7l8-3.5Z" />
        <path d="m9 12 2 2 4-4" />
      </>
    ),
  },
  {
    to: '/timeline',
    label: 'Timeline',
    icon: (
      <>
        <path d="M4 6h16M4 12h16M4 18h16" />
        <circle cx="8" cy="6" r="2" />
        <circle cx="15" cy="12" r="2" />
        <circle cx="10" cy="18" r="2" />
      </>
    ),
  },
  {
    to: '/parse-errors',
    label: 'Parse issues',
    icon: (
      <>
        <path d="M12 3.5 21 20H3l9-16.5Z" />
        <path d="M12 9v4.5M12 17h.01" />
      </>
    ),
  },
  {
    to: '/scenarios',
    label: 'Scenarios',
    icon: (
      <>
        <path d="M4 19V5M4 19h16" />
        <path d="m7 15 3.5-4 3 2 4.5-6" />
        <circle cx="7" cy="15" r="1" />
        <circle cx="10.5" cy="11" r="1" />
        <circle cx="13.5" cy="13" r="1" />
        <circle cx="18" cy="7" r="1" />
      </>
    ),
  },
  {
    to: '/reports',
    label: 'Reports',
    icon: (
      <>
        <path d="M6 3.5h8l4 4v13H6a2 2 0 0 1-2-2v-13a2 2 0 0 1 2-2Z" />
        <path d="M14 3.5v4h4M8 12h8M8 16h8" />
      </>
    ),
  },
]

export function Sidebar() {
  const { user, logout } = useAuth()

  return (
    <aside className="fixed inset-x-0 bottom-0 z-40 flex h-[72px] w-full border-t border-white/[0.08] bg-[#0d1422]/95 px-2 pb-[env(safe-area-inset-bottom)] backdrop-blur-xl md:sticky md:top-0 md:h-screen md:w-[252px] md:shrink-0 md:flex-col md:border-r md:border-t-0 md:px-4 md:py-6">
      <div className="hidden items-center gap-3 px-2 pb-8 md:flex">
        <Logo size={36} />
        <div>
          <p className="text-[15px] font-semibold tracking-tight text-white">CyberTrace</p>
          <p className="mt-0.5 text-[10px] font-medium uppercase tracking-[0.18em] text-slate-500">
            Incident response
          </p>
        </div>
      </div>

      <nav
        aria-label="Primary"
        className="flex w-full items-center justify-around gap-1 md:block md:space-y-1"
      >
        <p className="hidden px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-600 md:block">
          Workspace
        </p>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            aria-label={item.label}
            className={({ isActive }) =>
              `group flex min-w-0 flex-1 flex-col items-center justify-center gap-1 rounded-xl px-1 py-2 text-[9px] font-medium transition-colors md:flex-row md:justify-start md:gap-3 md:px-3 md:py-2.5 md:text-[13px] ${
                isActive
                  ? 'bg-accent/10 text-accent-light md:shadow-[inset_2px_0_0_#60a5fa]'
                  : 'text-slate-500 hover:bg-white/[0.04] hover:text-slate-200'
              }`
            }
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
              className="h-[18px] w-[18px] shrink-0 md:h-[17px] md:w-[17px]"
            >
              {item.icon}
            </svg>
            <span className="hidden truncate sm:inline">{item.label}</span>
          </NavLink>
        ))}
        <button
          onClick={logout}
          aria-label="Sign out"
          className="flex min-w-0 flex-1 flex-col items-center justify-center gap-1 rounded-xl px-1 py-2 text-[9px] font-medium text-slate-500 transition-colors hover:bg-white/[0.04] hover:text-slate-200 md:hidden"
        >
          <svg
            viewBox="0 0 24 24"
            className="h-[18px] w-[18px]"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.7"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M10 17l5-5-5-5M15 12H3M12 3h5a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-5" />
          </svg>
          <span className="hidden truncate sm:inline">Sign out</span>
        </button>
      </nav>

      <div className="mt-auto hidden border-t border-white/[0.07] pt-4 md:block">
        <div className="flex items-center gap-3 rounded-xl px-2 py-2">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-slate-700 bg-slate-800 text-xs font-semibold text-slate-300">
            {user?.email?.slice(0, 1).toUpperCase() ?? '?'}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-slate-200">{user?.email}</p>
            <p className="mt-0.5 text-[10px] capitalize text-slate-500">{user?.role ?? 'analyst'}</p>
          </div>
          <button
            onClick={logout}
            aria-label="Sign out"
            title="Sign out"
            className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-white/[0.06] hover:text-slate-200"
          >
            <svg
              viewBox="0 0 24 24"
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M10 17l5-5-5-5M15 12H3M12 3h5a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-5" />
            </svg>
          </button>
        </div>
      </div>
    </aside>
  )
}
