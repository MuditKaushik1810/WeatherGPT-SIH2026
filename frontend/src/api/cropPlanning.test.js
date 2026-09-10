import { fetchCropPlanning } from './cropPlanning'
import fixture from '../mocks/farmerCropPlanning.json'

afterEach(() => vi.restoreAllMocks())

it('calls the crop-planning endpoint with the location', async () => {
  const reply = { season: 'Kharif', recommendations: [{ crop: 'Rice' }] }
  global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => reply })

  const out = await fetchCropPlanning('Raipur')

  expect(out).toEqual(reply)
  const url = global.fetch.mock.calls[0][0]
  expect(url).toContain('/farmer/crop-planning')
  expect(url).toContain('location=Raipur')
})

it('fails soft to the demo fixture when the service errors', async () => {
  global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 500 })
  const out = await fetchCropPlanning('Raipur')
  expect(out).toEqual(fixture)
})
