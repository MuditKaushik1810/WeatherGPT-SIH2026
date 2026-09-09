import { render, screen, fireEvent } from '@testing-library/react'
import Chat from './Chat'
import { fetchChatAnswer } from '../api/chat'
import { fetchHomeView } from '../api/home'
import { resetLanguageForTests } from '../i18n'

vi.mock('../api/chat')
vi.mock('../api/home')

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  // The language store is a module-level singleton that outlives one test —
  // reset it so a language switched in one test doesn't leak into the next.
  resetLanguageForTests()
  // Live-conditions upgrade: default to no notable conditions, so tests are
  // deterministic on the fallback suggestions.
  fetchHomeView.mockResolvedValue({ current: {} })
})

it('shows dynamic suggestions and a back control in the empty state', () => {
  const { container } = render(<Chat />)
  expect(screen.getByText(/ask me about the weather/i)).toBeInTheDocument()
  // Reached from the Ask WeatherGPT button, so it offers a way back — not a nav tab.
  expect(screen.getByRole('button', { name: /back to home/i })).toBeInTheDocument()
  expect(container.querySelectorAll('.chat-suggestion')).toHaveLength(3)
})

it('tailors suggestions to the saved location', () => {
  localStorage.setItem('weathergpt.location', 'Jaipur')
  render(<Chat />)
  expect(screen.getAllByText(/Jaipur/).length).toBeGreaterThan(0)
})

it('sends a clicked suggestion to the chat endpoint', async () => {
  fetchChatAnswer.mockResolvedValue({
    answer: 'Clear skies.', data_tier: 'exact', source: 'WeatherAPI',
    query_class: 'realtime', audio_url: null,
  })
  const { container } = render(<Chat />)
  const first = container.querySelector('.chat-suggestion')

  fireEvent.click(first)

  expect(await screen.findByText(/Clear skies/)).toBeInTheDocument()
  // Localized label doubles as the (English) query in English mode; context is
  // empty on the first turn.
  expect(fetchChatAnswer).toHaveBeenCalledWith(first.textContent, 'en', { contextLocation: null, history: [] })
})

it('sends the selected language to the chat endpoint', async () => {
  fetchChatAnswer.mockResolvedValue({
    answer: 'दिल्ली में साफ आसमान।', data_tier: 'exact', source: 'WeatherAPI',
    query_class: 'realtime', audio_url: null,
  })
  render(<Chat />)

  // Switching the selector re-renders the whole screen in the chosen language,
  // so grab the controls (by their English labels) BEFORE the switch — the DOM
  // nodes persist across the re-render, only their text/labels localize.
  fireEvent.change(screen.getByLabelText('Your question'), { target: { value: 'weather in Delhi' } })
  const sendButton = screen.getByRole('button', { name: /^Send$/ })
  fireEvent.change(screen.getByLabelText('Answer language'), { target: { value: 'hi' } })
  fireEvent.click(sendButton)

  expect(await screen.findByText(/साफ आसमान/)).toBeInTheDocument()
  expect(fetchChatAnswer).toHaveBeenCalledWith('weather in Delhi', 'hi', { contextLocation: null, history: [] })
})

it('sends a typed question and shows the grounded answer with provenance', async () => {
  fetchChatAnswer.mockResolvedValue({
    answer: 'Clear skies in Delhi, about 31°C.', data_tier: 'exact',
    source: 'WeatherAPI', query_class: 'realtime', audio_url: null,
  })
  render(<Chat />)

  fireEvent.change(screen.getByLabelText('Your question'), { target: { value: 'weather in Delhi' } })
  fireEvent.click(screen.getByRole('button', { name: /^Send$/ }))

  expect(screen.getByText('weather in Delhi')).toBeInTheDocument()
  expect(await screen.findByText(/Clear skies in Delhi/)).toBeInTheDocument()
  expect(screen.getByText(/WeatherAPI · Exact/)).toBeInTheDocument()
})

it('never bare-refuses — shows a friendly fallback if the service is unreachable', async () => {
  fetchChatAnswer.mockRejectedValue(new Error('network down'))
  render(<Chat />)

  fireEvent.change(screen.getByLabelText('Your question'), { target: { value: 'weather in Delhi' } })
  fireEvent.click(screen.getByRole('button', { name: /^Send$/ }))

  expect(await screen.findByText(/couldn't reach the weather service/i)).toBeInTheDocument()
})

function seedSession(messages, lastLocation = 'Delhi') {
  localStorage.setItem('weathergpt.chatSession', JSON.stringify({
    messages, lastLocation, savedAt: Date.now(),
  }))
}

it('restores the previous conversation on mount (within a day)', () => {
  seedSession([
    { id: 1, role: 'user', text: 'weather in Delhi' },
    { id: 2, role: 'assistant', text: 'It is 31°C in Delhi.', source: 'WeatherAPI', dataTier: 'exact' },
  ])
  render(<Chat />)
  // The old turns are shown, and the empty-state suggestions are not.
  expect(screen.getByText('weather in Delhi')).toBeInTheDocument()
  expect(screen.getByText(/It is 31°C in Delhi/)).toBeInTheDocument()
  expect(screen.queryByText(/ask me about the weather/i)).not.toBeInTheDocument()
})

it('carries the last location as context on a follow-up', async () => {
  seedSession([
    { id: 1, role: 'user', text: 'weather in Delhi' },
    { id: 2, role: 'assistant', text: 'It is 31°C in Delhi.', source: 'WeatherAPI', dataTier: 'exact' },
  ], 'Delhi')
  fetchChatAnswer.mockResolvedValue({
    answer: 'Tomorrow: high 34°C.', data_tier: 'exact', source: 'WeatherAPI',
    query_class: 'realtime', audio_url: null, location: 'Delhi',
  })
  render(<Chat />)

  fireEvent.change(screen.getByLabelText('Your question'), { target: { value: 'what about tomorrow?' } })
  fireEvent.click(screen.getByRole('button', { name: /^Send$/ }))

  await screen.findByText(/Tomorrow: high 34/)
  expect(fetchChatAnswer).toHaveBeenCalledWith('what about tomorrow?', 'en', {
    contextLocation: 'Delhi',
    history: [
      { role: 'user', content: 'weather in Delhi' },
      { role: 'assistant', content: 'It is 31°C in Delhi.' },
    ],
  })
})

it('starts a fresh conversation with New chat', () => {
  seedSession([{ id: 1, role: 'user', text: 'weather in Delhi' }])
  render(<Chat />)
  expect(screen.getByText('weather in Delhi')).toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: 'New chat' }))

  expect(screen.queryByText('weather in Delhi')).not.toBeInTheDocument()
  expect(screen.getByText(/ask me about the weather/i)).toBeInTheDocument()
  expect(localStorage.getItem('weathergpt.chatSession')).toBeNull()
})
