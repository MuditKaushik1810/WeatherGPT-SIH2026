import { render, screen } from '@testing-library/react'
import CropPlanning from './CropPlanning'
import { fetchCropPlanning } from '../api/cropPlanning'
import { getPersona, setPersona } from '../lib/preferences'

vi.mock('../api/cropPlanning')

beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
  window.location.hash = ''
})

const view = {
  data_tier: 'demo',
  source: 'Frontend demo fixture',
  location: 'Noida, Uttar Pradesh',
  season: 'Rabi',
  climate_context: { summary: 'Cool Rabi conditions.', historical_note: 'Typical for the region.' },
  recommendations: [
    { crop: 'Wheat', suitability: 'Excellent', reason: 'Suited to the cool Rabi season.', harvest_window: 'March–April' },
  ],
}

it('renders recommended crops from the crop-planning shape and labels the demo data', async () => {
  fetchCropPlanning.mockResolvedValue(view)
  render(<CropPlanning />)

  expect(await screen.findByText('Wheat')).toBeInTheDocument()
  expect(screen.getByText(/March–April/)).toBeInTheDocument()
  expect(screen.getByText(/Demo data/i)).toBeInTheDocument() // demo provenance is visible
})

it('shows live provenance when the composite comes back from the backend', async () => {
  fetchCropPlanning.mockResolvedValue({
    ...view, data_tier: 'exact', source: 'WeatherAPI + WeatherGPT crop rules',
  })
  render(<CropPlanning />)

  expect(await screen.findByText('Wheat')).toBeInTheDocument()
  expect(screen.getByText(/Live · WeatherAPI/)).toBeInTheDocument()
})

it('leaving Farmer Mode switches the persona back to normal', async () => {
  setPersona('farmer')
  fetchCropPlanning.mockResolvedValue(view)
  const { findByRole } = render(<CropPlanning />)

  const modeSwitch = await findByRole('button', { name: /Switch to normal WeatherGPT mode/i })
  modeSwitch.click()

  expect(getPersona()).toBe('normal')
  expect(window.location.hash).toBe('#home')
})
