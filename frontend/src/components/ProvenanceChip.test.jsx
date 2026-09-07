import { render, screen } from '@testing-library/react'
import ProvenanceChip from './ProvenanceChip'

it('shows the source and a friendly tier label', () => {
  render(<ProvenanceChip source="Open-Meteo" dataTier="exact" />)
  expect(screen.getByText(/Open-Meteo · Exact/)).toBeInTheDocument()
})

it('maps a degraded tier to its readable label', () => {
  render(<ProvenanceChip source="IMD" dataTier="source_unavailable" />)
  expect(screen.getByText(/IMD · Source unavailable/)).toBeInTheDocument()
})

it('falls back gracefully when source/tier are missing', () => {
  render(<ProvenanceChip source={null} dataTier={undefined} />)
  expect(screen.getByText(/No source · Unknown/)).toBeInTheDocument()
})
