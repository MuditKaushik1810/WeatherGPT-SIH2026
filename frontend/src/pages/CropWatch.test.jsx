import { render, screen } from '@testing-library/react'
import CropWatch from './CropWatch'

it('renders Crop Watch as a separate Farmer Mode with only farmer-local navigation', () => {
  render(<CropWatch />)

  expect(screen.getByRole('heading', { name: 'Crop Watch' })).toBeInTheDocument()
  expect(screen.getByRole('tab', { name: 'Crop Planning' })).toBeInTheDocument()
  expect(screen.getByRole('tab', { name: 'Crop Watch' })).toHaveAttribute('aria-selected', 'true')
  expect(screen.queryByText('Home')).not.toBeInTheDocument()
  expect(screen.queryByText('Travel')).not.toBeInTheDocument()
  expect(screen.queryByText('Disaster')).not.toBeInTheDocument()
})

it('renders crop stage, threats, action and climate context from the demo fixture', () => {
  render(<CropWatch />)

  expect(screen.getByText('Wheat')).toBeInTheDocument()
  expect(screen.getByText('48 days')).toBeInTheDocument()
  expect(screen.getByText('Weather Threats')).toBeInTheDocument()
  expect(screen.getByText('Disease')).toBeInTheDocument()
  expect(screen.getByText('Recommended Action')).toBeInTheDocument()
  expect(screen.getByText('El Niño influence')).toBeInTheDocument()
  expect(screen.getByText(/Demo data/)).toBeInTheDocument()
})
