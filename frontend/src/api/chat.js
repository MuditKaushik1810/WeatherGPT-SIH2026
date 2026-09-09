// Calls the backend's grounded chat endpoint (POST /chat) and returns the
// { answer, data_tier, source, query_class, audio_url } contract shape
// (Architecture doc §3.10). The backend never bare-refuses — even with no live
// data it returns a grounded/honest answer — so the only failure the caller
// handles is the network/server being unreachable.
//
// Base URL comes from VITE_API_BASE_URL so the deployed frontend can point at a
// deployed backend without a code change; defaults to the local dev backend.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// `contextLocation` is the place the conversation is carrying forward (the last
// resolved location, or the user's default) so a location-less follow-up resolves
// instead of dead-ending; `history` is the recent turns for phrasing coherence.
// Both are optional and backward-compatible with the §3.10 contract.
export async function fetchChatAnswer(query, language = 'en', { contextLocation = null, history = null } = {}) {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, language, context_location: contextLocation, history }),
  })
  if (!response.ok) {
    throw new Error(`Chat service returned ${response.status}`)
  }
  return response.json()
}
