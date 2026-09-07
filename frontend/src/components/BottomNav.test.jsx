import { render, screen } from '@testing-library/react'
import BottomNav from './BottomNav'

it('renders the three primary tabs', () => {
  render(<BottomNav active="home" />)
  expect(screen.getByText('Home')).toBeInTheDocument()
  expect(screen.getByText('Travel')).toBeInTheDocument()
  expect(screen.getByText('Disaster')).toBeInTheDocument()
})

it('marks the active tab with aria-current', () => {
  render(<BottomNav active="disaster" />)
  expect(screen.getByRole('button', { name: /Disaster/ })).toHaveAttribute('aria-current', 'page')
  expect(screen.getByRole('button', { name: /Home/ })).not.toHaveAttribute('aria-current')
})
