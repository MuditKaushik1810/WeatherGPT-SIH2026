import { fetchCropWatch } from './cropWatch'
import fixture from '../mocks/farmerCropWatch.json'

afterEach(() => vi.restoreAllMocks())

it('calls the crop-watch endpoint with crop, location and days-after-sowing', async () => {
  const reply = { crop: 'wheat', risk_score: 40, threats: [] }
  global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => reply })

  const out = await fetchCropWatch({ crop: 'wheat', location: 'Karnal', daysAfterSowing: 48 })

  expect(out).toEqual(reply)
  const url = global.fetch.mock.calls[0][0]
  expect(url).toContain('/farmer/crop-watch')
  expect(url).toContain('crop=wheat')
  expect(url).toContain('location=Karnal')
  expect(url).toContain('days_after_sowing=48')
})

it('omits days_after_sowing when it is not provided', async () => {
  global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) })
  await fetchCropWatch({ crop: 'wheat', location: 'Karnal' })
  expect(global.fetch.mock.calls[0][0]).not.toContain('days_after_sowing')
})

it('fails soft to the demo fixture when the service errors', async () => {
  global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 500 })
  const out = await fetchCropWatch({ crop: 'wheat', location: 'Karnal' })
  expect(out).toEqual(fixture)
})
