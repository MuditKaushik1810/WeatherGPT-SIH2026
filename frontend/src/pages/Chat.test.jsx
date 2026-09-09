import { render, screen, fireEvent } from '@testing-library/react'
import Chat from './Chat'
import { fetchChatAnswer } from '../api/chat'
import { fetchHomeView } from '../api/home'

vi.mock('../api/chat')
vi.mock('../api/home')

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
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
  expect(fetchChatAnswer).toHaveBeenCalledWith(first.textContent)
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
