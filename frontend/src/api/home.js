// Calls the backend's composite Home endpoint (GET /home/{location}) and returns
// the { location, current, hourly, recommendation, data_tier } view.
//
// Base URL comes from VITE_API_BASE_URL so the deployed frontend can point at a
// deployed backend without a code change; defaults to the local dev backend.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function fetchHomeView(location) {
  const response = await fetch(`${BASE_URL}/home/${encodeURIComponent(location)}`)
  if (!response.ok) {
    // Network reached the server but it errored (5xx/4xx). The caller shows the
    // error state; it never renders a half-broken screen.
    throw new Error(`Weather service returned ${response.status}`)
  }
  return response.json()
}
