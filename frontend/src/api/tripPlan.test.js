import { fetchTripPlan } from './tripPlan'
import fixture from '../mocks/travelPlan.json'

afterEach(() => vi.restoreAllMocks())

it('POSTs from/to to the trip-plan endpoint and returns the plan', async () => {
  const reply = { route: { from: 'Noida', to: 'Jaipur' }, checkpoints: [], data_tier: 'exact' }
  global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => reply })

  const out = await fetchTripPlan({ from: 'Noida', to: 'Jaipur' })

  expect(out).toEqual(reply)
  const [url, init] = global.fetch.mock.calls[0]
  expect(url).toContain('/trip-plan')
  expect(init.method).toBe('POST')
  expect(JSON.parse(init.body)).toEqual({ from: 'Noida', to: 'Jaipur', departure: null })
})

it('fails soft to the demo fixture when the service errors', async () => {
  global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 500 })
  const out = await fetchTripPlan({ from: 'Noida', to: 'Jaipur' })
  expect(out).toEqual(fixture)
})

it('fails soft to the demo fixture on a network error', async () => {
  global.fetch = vi.fn().mockRejectedValue(new Error('offline'))
  const out = await fetchTripPlan({ from: 'Noida', to: 'Jaipur' })
  expect(out).toEqual(fixture)
})
