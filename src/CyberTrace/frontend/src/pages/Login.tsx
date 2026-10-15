import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { api, ApiError } from '../api/client'
import { Button } from '../components/ui/Button'
import { Logo } from '../components/layout/Logo'

export function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      if (mode === 'register') {
        await api.post('/api/auth/register', { email, password })
      }
      await login(email, password)
      navigate('/timeline')
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : mode === 'register'
              ? 'Could not create your account'
              : 'Sign in failed',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="relative grid min-h-screen overflow-hidden lg:grid-cols-[1.05fr_0.95fr]">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_18%_8%,rgba(37,99,235,0.16),transparent_34rem)]" />

      <section className="relative hidden flex-col justify-between border-r border-white/[0.06] px-12 py-10 lg:flex xl:px-20">
        <a href="/" className="flex w-fit items-center gap-3">
          <Logo size={42} />
          <div>
            <p className="text-lg font-semibold tracking-tight text-white">CyberTrace</p>
            <p className="text-[10px] font-medium uppercase tracking-[0.2em] text-slate-500">
              Incident response
            </p>
          </div>
        </a>

        <div className="relative max-w-xl pb-12">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-accent/20 bg-accent/[0.08] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.15em] text-accent-light">
            <span className="h-1.5 w-1.5 rounded-full bg-accent-light" />
            Evidence-led investigations
          </div>
          <h1 className="max-w-lg text-5xl font-semibold leading-[1.08] tracking-[-0.045em] text-white xl:text-[58px]">
            See the whole story.
            <span className="mt-2 block bg-gradient-to-r from-accent-light to-cyan-300 bg-clip-text text-transparent">
              Follow every signal.
            </span>
          </h1>
          <p className="mt-6 max-w-md text-[15px] leading-7 text-slate-400">
            Bring security evidence into one clear timeline. Preserve original files, verify their
            integrity, and investigate with the context intact.
          </p>

          <div className="mt-12 max-w-lg rounded-2xl border border-white/[0.08] bg-[#101a2b]/75 p-5 shadow-2xl shadow-black/20 backdrop-blur">
            <div className="flex items-center justify-between border-b border-white/[0.07] pb-4">
              <div className="flex items-center gap-2">
                <span className="grid h-7 w-7 place-items-center rounded-lg bg-accent/10 text-accent-light">
                  <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
                    <path d="M4 6h16M4 12h16M4 18h16" />
                    <circle cx="8" cy="6" r="2" fill="#101a2b" />
                    <circle cx="15" cy="12" r="2" fill="#101a2b" />
                    <circle cx="10" cy="18" r="2" fill="#101a2b" />
                  </svg>
                </span>
                <span className="text-xs font-semibold text-slate-200">Investigation timeline</span>
              </div>
              <span className="rounded-full border border-white/[0.08] px-2 py-1 text-[9px] font-medium uppercase tracking-wider text-slate-500">
                Workflow preview
              </span>
            </div>
            <div className="mt-4 space-y-3">
              {[
                { time: '10:42:18', label: 'Authentication anomaly', status: 'warning' },
                { time: '10:44:02', label: 'Evidence integrity verified', status: 'ok' },
                { time: '10:47:31', label: 'Related event correlated', status: 'info' },
              ].map((event, index) => (
                <div key={event.time} className="flex items-center gap-3">
                  <div className="flex flex-col items-center self-stretch">
                    <span
                      className={`mt-1 h-2 w-2 rounded-full ${
                        event.status === 'warning'
                          ? 'bg-amber-400'
                          : event.status === 'ok'
                            ? 'bg-emerald-400'
                            : 'bg-blue-400'
                      }`}
                    />
                    {index < 2 && <span className="mt-1 w-px flex-1 bg-slate-700/70" />}
                  </div>
                  <span className="w-14 font-mono text-[10px] text-slate-500">{event.time}</span>
                  <span className="text-xs text-slate-300">{event.label}</span>
                </div>
              ))}
            </div>
            <p className="mt-4 border-t border-white/[0.06] pt-3 text-[10px] text-slate-600">
              Illustrative workflow · no real incident data
            </p>
          </div>
        </div>

        <p className="text-[11px] text-slate-600">
          CyberTrace <span className="px-1.5 text-slate-700">/</span> Keep the evidence. Find the story.
        </p>
      </section>

      <section className="relative flex min-h-screen items-center justify-center px-5 py-10 sm:px-8">
        <div className="w-full max-w-[420px]">
          <a href="/" className="mb-12 flex items-center gap-3 lg:hidden">
            <Logo size={38} />
            <div>
              <p className="font-semibold tracking-tight text-white">CyberTrace</p>
              <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-slate-500">
                Incident response
              </p>
            </div>
          </a>

          <div className="mb-8">
            <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-accent-light">
              Secure workspace
            </p>
            <h2 className="text-3xl font-semibold tracking-tight text-white">
              {mode === 'login' ? 'Welcome back' : 'Create your account'}
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              {mode === 'login'
                ? 'Sign in to continue your investigations.'
                : 'Set up an analyst account to start investigating.'}
            </p>
          </div>

          <div className="rounded-2xl border border-white/[0.08] bg-[#101a2b]/75 p-5 shadow-[0_24px_80px_rgba(0,0,0,0.25)] sm:p-7">
            <form onSubmit={handleSubmit} className="space-y-5" noValidate>
              <div>
                <label htmlFor="email" className="mb-2 block text-xs font-medium text-slate-300">
                  Work email
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@organization.com"
                  className="h-11 w-full rounded-xl border px-3.5 text-sm placeholder:text-slate-600"
                  autoComplete="username"
                />
              </div>
              <div>
                <div className="mb-2 flex items-center justify-between">
                  <label htmlFor="password" className="block text-xs font-medium text-slate-300">
                    Password
                  </label>
                  {mode === 'register' && (
                    <span className="text-[10px] text-slate-600">At least 8 characters</span>
                  )}
                </div>
                <input
                  id="password"
                  type="password"
                  required
                  minLength={mode === 'register' ? 8 : undefined}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={mode === 'register' ? 'Choose a strong password' : 'Enter your password'}
                  className="h-11 w-full rounded-xl border px-3.5 text-sm placeholder:text-slate-600"
                  autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
                />
              </div>

              {error && (
                <div
                  role="alert"
                  aria-live="assertive"
                  className="rounded-xl border border-status-critical/25 bg-status-critical/[0.08] px-3.5 py-3 text-sm text-red-300"
                >
                  {error}
                </div>
              )}

              <Button type="submit" disabled={submitting} className="w-full">
                {submitting
                  ? mode === 'register'
                    ? 'Creating account…'
                    : 'Signing in…'
                  : mode === 'register'
                    ? 'Create account'
                    : 'Sign in'}
                {!submitting && (
                  <svg viewBox="0 0 20 20" className="ml-1 h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
                    <path d="M3.5 10h13M11 4.5l5.5 5.5-5.5 5.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </Button>
            </form>

            <div className="my-5 flex items-center gap-3">
              <span className="h-px flex-1 bg-white/[0.07]" />
              <span className="text-[10px] uppercase tracking-[0.14em] text-slate-600">or</span>
              <span className="h-px flex-1 bg-white/[0.07]" />
            </div>

            <p className="text-center text-xs text-slate-500">
              {mode === 'login' ? 'New to CyberTrace?' : 'Already have an account?'}{' '}
              <button
                type="button"
                onClick={() => {
                  setMode(mode === 'login' ? 'register' : 'login')
                  setError(null)
                }}
                className="font-medium text-accent-light transition-colors hover:text-blue-300"
              >
                {mode === 'login' ? 'Create an account' : 'Sign in'}
              </button>
            </p>
          </div>

          <p className="mt-6 text-center text-[10px] leading-5 text-slate-600">
            By continuing, you agree to keep sensitive evidence protected and handle it
            responsibly.
          </p>
        </div>
      </section>
    </main>
  )
}
