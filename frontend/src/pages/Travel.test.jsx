import { render, screen, waitFor } from '@testing-library/react'
import { fireEvent } from '@testing-library/react'
import Travel from './Travel'
import { fetchTripPlan } from '../api/tripPlan'

vi.mock('../api/tripPlan')

beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
})

const demoView = {
  route: { from: 'Noida, Uttar Pradesh', to: 'Jaipur, Rajasthan', distance_km: 280,
           estimated_time: '5h 20m', route_name: 'NH48', condition: 'Good' },
  departure: { label: 'Tomorrow', time: '8:00 AM' },
  checkpoints: [
    { id: 'noida', name: 'Noida', distance_km: 0, eta: '8:00 AM', temperature: 29,
      weather: 'partly cloudy', rain_probability: 15, status: 'good', note: 'Good start.',
      facilities: { restaurants: '20+', fuel_stations: 8, hotels: '10+', hospitals: 5, parking: 1 } },
    { id: 'gurugram', name: 'Gurugram', distance_km: 42, eta: '8:45 AM', temperature: 30,
      weather: 'partly cloudy', rain_probability: 20, status: 'good', note: 'Low rain.',
      facilities: { restaurants: '20+', fuel_stations: 6, hotels: '10+', hospitals: 4, parking: 1 } },
  ],
  summary: 'Good travel conditions expected from Noida to Jaipur.',
  weather_source: 'Frontend demo fixture', routing_source: 'Frontend demo fixture',
  data_tier: 'demo', fetched_at: '2026-09-07T08:00:00',
}

it('renders the live trip plan: route, checkpoints, and the selected stop', async () => {
  fetchTripPlan.mockResolvedValue({ ...demoView, data_tier: 'exact',
    weather_source: 'WeatherAPI', routing_source: 'Geoapify' })
  render(<Travel />)

  expect(await screen.findByText('NH48')).toBeInTheDocument() // best route (route_name)
  expect(screen.getByRole('heading', { name: 'Noida' })).toBeInTheDocument() // first stop selected
  // split provenance from the live shape — never collapsed to one source
  expect(screen.getByText(/Weather via WeatherAPI · Routing & facilities via Geoapify/)).toBeInTheDocument()
  expect(screen.queryByText('Demo data')).not.toBeInTheDocument() // live, so no demo badge
})

it('surfaces the demo badge and honest note when it fails soft to the fixture', async () => {
  fetchTripPlan.mockResolvedValue(demoView)
  render(<Travel />)

  expect(await screen.findByText('Demo data')).toBeInTheDocument()
  expect(screen.getByText(/Demo values/)).toBeInTheDocument()
})

it('editing the destination re-fetches for the new route', async () => {
  fetchTripPlan.mockResolvedValue(demoView)
  render(<Travel />)
  await screen.findByText('NH48')

  fireEvent.click(screen.getByRole('button', { name: 'Edit' }))
  fireEvent.change(screen.getByLabelText('Destination'), { target: { value: 'Agra' } })
  fireEvent.click(screen.getByRole('button', { name: 'Plan trip' }))

  await waitFor(() =>
    expect(fetchTripPlan).toHaveBeenLastCalledWith(expect.objectContaining({ to: 'Agra' })),
  )
})

it('shows an honest notice when the backend returns a route with no checkpoints', async () => {
  fetchTripPlan.mockResolvedValue({
    route: { from: 'Nowhere', to: 'Jaipur', distance_km: null, estimated_time: null,
             route_name: null, condition: 'Unknown' },
    departure: { label: 'Today', time: '9:00 AM' },
    checkpoints: [],
    summary: "Couldn't locate 'Nowhere'. Try a nearby major city or district name.",
    weather_source: 'Unavailable', routing_source: 'Geoapify',
    data_tier: 'unresolved_location', fetched_at: '2026-09-10T09:00:00',
  })
  render(<Travel />)

  expect(await screen.findByText(/Couldn't locate 'Nowhere'/)).toBeInTheDocument()
})
