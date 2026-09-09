import { fetchChatAnswer } from './chat'

afterEach(() => {
  vi.restoreAllMocks()
})

it('POSTs the query (and language) to the chat endpoint', async () => {
  const reply = {
    answer: 'Clear skies in Delhi, about 31°C.', data_tier: 'exact',
    source: 'WeatherAPI', query_class: 'realtime', audio_url: null,
  }
  global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => reply })

  const result = await fetchChatAnswer('weather in Delhi')

  expect(result).toEqual(reply)
  const [url, opts] = global.fetch.mock.calls[0]
  expect(url).toContain('/chat')
  expect(opts.method).toBe('POST')
  // Context fields are sent (null when absent) — backward-compatible with §3.10.
  expect(JSON.parse(opts.body)).toEqual({
    query: 'weather in Delhi', language: 'en', context_location: null, history: null,
  })
})

it('forwards context location and history when provided', async () => {
  const reply = { answer: 'ok', data_tier: 'exact', source: 'WeatherAPI', query_class: 'realtime', audio_url: null }
  global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => reply })

  await fetchChatAnswer('what about tomorrow?', 'hi', {
    contextLocation: 'Delhi',
    history: [{ role: 'user', content: 'weather in Delhi' }],
  })

  const body = JSON.parse(global.fetch.mock.calls[0][1].body)
  expect(body).toEqual({
    query: 'what about tomorrow?', language: 'hi', context_location: 'Delhi',
    history: [{ role: 'user', content: 'weather in Delhi' }],
  })
})

it('throws when the server responds with an error status', async () => {
  global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 500 })
  await expect(fetchChatAnswer('hi')).rejects.toThrow(/500/)
})
