// Calls the backend's grounded chat endpoint (POST /chat) and returns the
// { answer, data_tier, source, query_class, audio_url } contract shape
// (Architecture doc §3.10). The backend never bare-refuses — even with no live
// data it returns a grounded/honest answer — so the only failure the caller
// handles is the network/server being unreachable.
//
// Base URL comes from VITE_API_BASE_URL so the deployed frontend can point at a
// deployed backend without a code change; defaults to the local dev backend.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function fetchChatAnswer(query, language = 'en') {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, language }),
  })
  if (!response.ok) {
    throw new Error(`Chat service returned ${response.status}`)
  }
  return response.json()
}
