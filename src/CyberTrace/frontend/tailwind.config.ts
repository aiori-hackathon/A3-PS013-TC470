import type { Config } from 'tailwindcss'

// CyberTrace design system palette (PROJECT_PLAN.md section 1):
// dark navy background, slate surfaces, muted blue accent, restrained
// green reserved for "verified / ok" status only.
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#0B1220',
          900: '#111827',
        },
        slate: {
          800: '#1E293B',
          700: '#334155',
        },
        accent: {
          DEFAULT: '#3B82F6',
          light: '#60A5FA',
        },
        status: {
          ok: '#22C55E',
          warning: '#EAB308',
          critical: '#EF4444',
          info: '#64748B',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Courier New"', 'monospace'],
      },
    },
  },
  plugins: [],
} satisfies Config
