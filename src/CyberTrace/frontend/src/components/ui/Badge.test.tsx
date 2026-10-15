import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Badge } from './Badge'

describe('Badge', () => {
  it('renders the provided label', () => {
    render(<Badge status="ok">Verified</Badge>)
    expect(screen.getByText('Verified')).toBeInTheDocument()
  })

  it('renders synthetic scenario label distinctly', () => {
    render(<Badge status="synthetic">Synthetic scenario</Badge>)
    expect(screen.getByText('Synthetic scenario')).toBeInTheDocument()
  })
})
