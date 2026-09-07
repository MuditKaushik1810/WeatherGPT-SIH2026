import { render, screen } from '@testing-library/react'
import WeatherPostcard from './WeatherPostcard'

const weather = {
  temp: 28.4,
  condition: 'partly cloudy',
  feels_like: 31,
  humidity: 72,
  precipitation_chance: 0.3,
  wind_speed: 12,
  aqi: 86,
  source: 'Open-Meteo',
  data_tier: 'exact',
}

it('renders the contract metrics with correct units and rain %', () => {
  render(<WeatherPostcard weather={weather} />)
  expect(screen.getByText('28.4°C')).toBeInTheDocument()
  expect(screen.getByText('72%')).toBeInTheDocument()
  expect(screen.getByText('30%')).toBeInTheDocument() // precipitation_chance 0.3 -> 30%
  expect(screen.getByText('12 km/h')).toBeInTheDocument()
  expect(screen.getByText('86')).toBeInTheDocument()
  // provenance chip is present
  expect(screen.getByText(/Open-Meteo · Exact/)).toBeInTheDocument()
})

it('shows an em dash for a null metric instead of "null"', () => {
  render(<WeatherPostcard weather={{ ...weather, humidity: null }} />)
  expect(screen.getByText('—')).toBeInTheDocument()
})
