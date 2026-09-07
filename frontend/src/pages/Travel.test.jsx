import { render, screen } from '@testing-library/react'
import Travel from './Travel'

it('renders the trip planner with route, checkpoints, and honest provenance', () => {
  render(<Travel />)

  expect(screen.getByText('Demo data')).toBeInTheDocument()
  expect(screen.getByText('NH48')).toBeInTheDocument() // best route (route_name)
  // selected checkpoint (index 1) heading
  expect(screen.getByRole('heading', { name: 'Gurugram' })).toBeInTheDocument()
  // corrected provenance note names the real per-source origins, not "Open-Meteo" for everything
  expect(screen.getByText(/Routing & facilities via Geoapify/)).toBeInTheDocument()
})
