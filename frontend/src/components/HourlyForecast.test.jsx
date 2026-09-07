import { render, screen } from '@testing-library/react'
import HourlyForecast from './HourlyForecast'

it('labels the first hour "Now" and renders the temperatures', () => {
  const forecast = [
    { time: '2026-09-07T09:00', temp: 28, condition: 'clear sky' },
    { time: '2026-09-07T10:00', temp: 29, condition: 'overcast' },
  ]

  render(<HourlyForecast forecast={forecast} />)

  expect(screen.getByText('Now')).toBeInTheDocument()
  expect(screen.getByText('28°')).toBeInTheDocument()
  expect(screen.getByText('29°')).toBeInTheDocument()
})
