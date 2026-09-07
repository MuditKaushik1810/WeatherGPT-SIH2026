import { fetchHomeView } from './home'

afterEach(() => {
  vi.restoreAllMocks()
})

it('requests the home endpoint for the given location', async () => {
  const view = { location: 'Delhi', current: {}, hourly: [], recommendation: {}, data_tier: 'exact' }
  global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => view })

  const result = await fetchHomeView('Delhi')

  expect(result).toEqual(view)
  expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/home/Delhi'))
})

it('throws when the server responds with an error status', async () => {
  global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 503 })

  await expect(fetchHomeView('Delhi')).rejects.toThrow(/503/)
})
