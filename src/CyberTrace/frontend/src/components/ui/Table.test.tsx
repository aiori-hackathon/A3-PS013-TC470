import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Table, type Column } from './Table'

interface Row {
  id: string
  name: string
}

const columns: Column<Row>[] = [{ key: 'name', header: 'Name', render: (row) => row.name }]

describe('Table', () => {
  it('shows the empty state when there are no rows', () => {
    render(
      <Table columns={columns} rows={[]} rowKey={(r) => r.id} emptyMessage="No evidence yet" />,
    )
    expect(screen.getByText('No evidence yet')).toBeInTheDocument()
  })

  it('shows skeleton rows while loading', () => {
    const { container } = render(
      <Table columns={columns} rows={[]} rowKey={(r) => r.id} isLoading />,
    )
    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0)
  })

  it('shows an error message when error is set', () => {
    render(
      <Table columns={columns} rows={[]} rowKey={(r) => r.id} error="Failed to load records" />,
    )
    expect(screen.getByText('Failed to load records')).toBeInTheDocument()
  })

  it('renders row data when rows are provided', () => {
    render(
      <Table columns={columns} rows={[{ id: '1', name: 'auth.log' }]} rowKey={(r) => r.id} />,
    )
    expect(screen.getByText('auth.log')).toBeInTheDocument()
  })
})
