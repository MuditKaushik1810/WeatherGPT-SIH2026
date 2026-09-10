import { render, screen } from '@testing-library/react'
import CropWatch from './CropWatch'
import { fetchCropWatch } from '../api/cropWatch'

vi.mock('../api/cropWatch')

beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
  window.location.hash = ''
})

const view = {
  data_tier: 'exact', source: 'WeatherAPI + Open-Meteo (soil moisture)', provisional: false,
  location: 'Karnal', crop: 'wheat', days_after_sowing: 48,
  crop_stage: 'Vegetative', next_stage: 'Flowering',
  risk_score: 43, risk_level: 'Moderate',
  components: { temperature: 0.4, soil_moisture: 1.0 },
  threats: [{ id: 'heat', label: 'Heat Stress', level: 'High', detail: '34°C is above the 12–25°C comfort range for this crop.' }],
  recommended_action: { title: 'Protect the crop from heat stress', items: ['Irrigate in the cooler evening'] },
  climate_context: { title: 'Current-season conditions', level: 'Moderate', detail: 'Based on live weather.' },
}

it('renders Crop Watch as a separate Farmer Mode with only farmer-local navigation', async () => {
  fetchCropWatch.mockResolvedValue(view)
  render(<CropWatch />)

  expect(await screen.findByRole('heading', { name: 'Crop Watch' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Crop Planning' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Crop Watch' })).toHaveAttribute('aria-current', 'page')
  expect(screen.queryByText('Home')).not.toBeInTheDocument()
  expect(screen.queryByText('Travel')).not.toBeInTheDocument()
  expect(screen.queryByText('Disaster')).not.toBeInTheDocument()
})

it('renders the live crop-watch composite: crop, stage, risk, explained threats, action, provenance', async () => {
  fetchCropWatch.mockResolvedValue(view)
  render(<CropWatch />)

  expect(await screen.findByText('wheat')).toBeInTheDocument()
  expect(screen.getByText('48 days')).toBeInTheDocument()
  expect(screen.getByText(/Risk Moderate · 43/)).toBeInTheDocument()
  expect(screen.getByText('Heat Stress')).toBeInTheDocument()
  expect(screen.getByText(/comfort range for this crop/)).toBeInTheDocument()   // threat is explained
  expect(screen.getByText('Protect the crop from heat stress')).toBeInTheDocument()
  expect(screen.getByText(/Live · WeatherAPI/)).toBeInTheDocument()             // provenance
})

it('surfaces the demo provenance when the composite comes back as the fixture', async () => {
  fetchCropWatch.mockResolvedValue({ ...view, data_tier: 'demo', source: 'Frontend demo fixture' })
  render(<CropWatch />)

  expect(await screen.findByText(/Demo data/)).toBeInTheDocument()
})

it('prompts for a sowing date when the crop stage is unknown', async () => {
  fetchCropWatch.mockResolvedValue({ ...view, crop_stage: null, next_stage: null, days_after_sowing: null })
  render(<CropWatch />)

  expect(await screen.findByText(/Add your sowing date in Settings/i)).toBeInTheDocument()
})
