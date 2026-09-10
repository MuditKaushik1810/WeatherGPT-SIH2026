import { render, screen, fireEvent } from '@testing-library/react'
import Home from './Home'
import { fetchHomeView } from '../api/home'

vi.mock('../api/home')

const view = {
  location: 'Delhi',
  data_tier: 'exact',
  current: {
    temp: 30, condition: 'clear sky', feels_like: 32, humidity: 40,
    precipitation_chance: 0.1, wind_speed: 8, aqi: 55,
    source: 'WeatherAPI', data_tier: 'exact',
  },
  hourly: [{ time: '2026-09-07T09:00', temp: 30, condition: 'clear sky', precipitation_chance: 0.1 }],
  recommendation: { title: 'Good time for a short outing', message: 'Nice out.' },
}

beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
})

it('shows a location prompt on first run and does not fetch', () => {
  render(<Home />)
  expect(screen.getByText(/enter a city or district above/i)).toBeInTheDocument()
  expect(fetchHomeView).not.toHaveBeenCalled()
})

it('fetches and renders weather for a saved location', async () => {
  localStorage.setItem('weathergpt.location', 'Delhi')
  fetchHomeView.mockResolvedValue(view)

  render(<Home />)

  expect(await screen.findByText('30°C')).toBeInTheDocument()
  expect(screen.getByText(/Good time for a short outing/)).toBeInTheDocument()
  expect(fetchHomeView).toHaveBeenCalledWith('Delhi')
})

it('shows an error state with retry when the fetch fails, then recovers on retry', async () => {
  localStorage.setItem('weathergpt.location', 'Delhi')
  fetchHomeView.mockRejectedValueOnce(new Error('network'))

  render(<Home />)

  const retry = await screen.findByRole('button', { name: /retry/i })
  expect(screen.getByText(/couldn.t reach the weather service/i)).toBeInTheDocument()

  fetchHomeView.mockResolvedValueOnce(view)
  fireEvent.click(retry)

  expect(await screen.findByText('30°C')).toBeInTheDocument()
})

it('prompts a retype when the location cannot be resolved', async () => {
  localStorage.setItem('weathergpt.location', 'Zzzz')
  fetchHomeView.mockResolvedValue({
    location: 'Zzzz',
    data_tier: 'unresolved_location',
    current: { data_tier: 'unresolved_location', temp: null, source: null },
    hourly: [],
    recommendation: { title: 'Limited data right now', message: '...' },
  })

  render(<Home />)

  expect(await screen.findByText(/couldn.t find/i)).toBeInTheDocument()
})

it('remembers a location only after it resolves successfully', async () => {
  fetchHomeView.mockResolvedValue(view)

  render(<Home />)

  fireEvent.change(screen.getByLabelText('Location'), { target: { value: 'Delhi' } })
  fireEvent.click(screen.getByRole('button', { name: /^Go$/ }))

  expect(await screen.findByText('30°C')).toBeInTheDocument()
  expect(localStorage.getItem('weathergpt.location')).toBe('Delhi')
})

it('does not remember an unresolvable location', async () => {
  fetchHomeView.mockResolvedValue({
    location: 'Zzz',
    data_tier: 'unresolved_location',
    current: { data_tier: 'unresolved_location', temp: null, source: null },
    hourly: [],
    recommendation: { title: 'Limited data right now', message: '...' },
  })

  render(<Home />)

  fireEvent.change(screen.getByLabelText('Location'), { target: { value: 'Zzz' } })
  fireEvent.click(screen.getByRole('button', { name: /^Go$/ }))

  expect(await screen.findByText(/couldn.t find/i)).toBeInTheDocument()
  expect(localStorage.getItem('weathergpt.location')).toBeNull()
})
