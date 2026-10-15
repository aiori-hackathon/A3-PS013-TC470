import type { ReactNode } from 'react'

export interface Column<T> {
  key: string
  header: string
  render: (row: T) => ReactNode
  className?: string
}

interface TableProps<T> {
  columns: Column<T>[]
  rows: T[]
  rowKey: (row: T) => string
  isLoading?: boolean
  error?: string | null
  emptyMessage?: string
  onRowClick?: (row: T) => void
}

/** Shared Table component with explicit loading / error / empty states
 * (PROJECT_PLAN.md section 1): every data view must define all three, not
 * just a happy path. */
export function Table<T>({
  columns,
  rows,
  rowKey,
  isLoading = false,
  error = null,
  emptyMessage = 'No records found.',
  onRowClick,
}: TableProps<T>) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-white/[0.08] bg-[#101a2b]/70">
      <table className="w-full min-w-[640px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-white/[0.08] bg-white/[0.025] text-left text-[10px] uppercase tracking-[0.12em] text-slate-500">
            {columns.map((col) => (
              <th key={col.key} className={`whitespace-nowrap px-4 py-3.5 font-semibold ${col.className ?? ''}`}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {isLoading &&
            Array.from({ length: 4 }).map((_, i) => (
              <tr key={`skeleton-${i}`} className="border-b border-white/[0.05]">
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-3">
                    <div className="h-4 w-3/4 animate-pulse rounded-md bg-slate-700/60" />
                  </td>
                ))}
              </tr>
            ))}

          {!isLoading && error && (
            <tr>
              <td colSpan={columns.length} className="px-4 py-4">
                <div className="rounded border border-status-critical/40 bg-status-critical/10 px-3 py-2 text-status-critical">
                  {error}
                </div>
              </td>
            </tr>
          )}

          {!isLoading && !error && rows.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="px-4 py-12 text-center text-sm text-slate-500">
                {emptyMessage}
              </td>
            </tr>
          )}

          {!isLoading &&
            !error &&
            rows.map((row) => (
              <tr
                key={rowKey(row)}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={`border-b border-white/[0.05] last:border-0 ${
                  onRowClick ? 'cursor-pointer transition-colors hover:bg-white/[0.035]' : ''
                }`}
              >
                {columns.map((col) => (
                  <td key={col.key} className={`px-4 py-3.5 text-slate-300 ${col.className ?? ''}`}>
                    {col.render(row)}
                  </td>
                ))}
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  )
}
