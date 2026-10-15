import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'secondary' | 'destructive' | 'ghost'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  children: ReactNode
}

const variantClasses: Record<Variant, string> = {
  primary:
    'bg-accent text-white shadow-[0_4px_14px_rgba(59,130,246,0.22)] hover:bg-blue-500 hover:shadow-[0_6px_18px_rgba(59,130,246,0.3)] disabled:bg-slate-700 disabled:shadow-none',
  secondary:
    'border border-white/[0.1] bg-white/[0.04] text-slate-100 hover:border-white/[0.18] hover:bg-white/[0.08] disabled:opacity-50',
  destructive:
    'bg-status-critical text-white shadow-[0_4px_14px_rgba(239,68,68,0.18)] hover:bg-red-600 disabled:opacity-50',
  ghost: 'bg-transparent text-slate-400 hover:bg-white/[0.06] hover:text-slate-100 disabled:opacity-50',
}

/** Single shared Button component (PROJECT_PLAN.md section 1). Every usage
 * must be wired to a real handler -- no decorative/no-op buttons. */
export function Button({ variant = 'primary', className = '', children, ...rest }: ButtonProps) {
  return (
    <button
      className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-medium
        transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-light focus-visible:ring-offset-2 focus-visible:ring-offset-navy-950 disabled:cursor-not-allowed ${variantClasses[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  )
}
