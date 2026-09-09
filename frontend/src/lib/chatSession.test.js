import { loadSession, saveSession, clearSession } from './chatSession'

beforeEach(() => localStorage.clear())

it('returns null when there is no stored session', () => {
  expect(loadSession()).toBeNull()
})

it('round-trips a saved session', () => {
  saveSession({ messages: [{ id: 1, role: 'user', text: 'hi' }], lastLocation: 'Delhi' })
  const restored = loadSession()
  expect(restored.messages).toHaveLength(1)
  expect(restored.lastLocation).toBe('Delhi')
})

it('drops a session older than a day', () => {
  const twoDaysAgo = Date.now() - 2 * 24 * 60 * 60 * 1000
  localStorage.setItem('weathergpt.chatSession', JSON.stringify({
    messages: [{ id: 1, role: 'user', text: 'stale' }], lastLocation: 'Delhi', savedAt: twoDaysAgo,
  }))
  expect(loadSession()).toBeNull()
  expect(localStorage.getItem('weathergpt.chatSession')).toBeNull() // pruned
})

it('clears a session', () => {
  saveSession({ messages: [{ id: 1, role: 'user', text: 'hi' }], lastLocation: null })
  clearSession()
  expect(loadSession()).toBeNull()
})

it('tolerates a corrupt stored value', () => {
  localStorage.setItem('weathergpt.chatSession', 'not json')
  expect(loadSession()).toBeNull()
})
