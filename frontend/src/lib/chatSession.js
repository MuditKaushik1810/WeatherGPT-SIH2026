// Chat session persistence — keeps the last conversation on the device so leaving
// the chat and coming back resumes it (a real chatbot expectation), rather than
// starting cold every time. Scope is deliberately ONE day: the summary said we
// don't need multi-day history, but a session must at least survive navigation
// and short breaks within a day. Same fail-soft localStorage discipline as
// savedLocation.js / preferences.js; migrates to a user profile with accounts.
const KEY = 'weathergpt.chatSession'
const TTL_MS = 24 * 60 * 60 * 1000 // 1 day

export function loadSession() {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return null
    const data = JSON.parse(raw)
    if (!data || typeof data.savedAt !== 'number') return null
    if (Date.now() - data.savedAt > TTL_MS) {
      localStorage.removeItem(KEY) // expired — start fresh
      return null
    }
    return {
      messages: Array.isArray(data.messages) ? data.messages : [],
      lastLocation: data.lastLocation || null,
    }
  } catch {
    return null
  }
}

export function saveSession({ messages, lastLocation }) {
  try {
    localStorage.setItem(KEY, JSON.stringify({
      messages: messages || [],
      lastLocation: lastLocation || null,
      savedAt: Date.now(),
    }))
  } catch {
    // Persisting the session is a convenience, not a requirement.
  }
}

export function clearSession() {
  try {
    localStorage.removeItem(KEY)
  } catch {
    // ignore
  }
}
