// Trip Planner data — the live route-aware planner POST /trip-plan (Architecture
// §3.10). Single swap-point (same pattern as api/cropPlanning / api/cropWatch): it
// POSTs {from, to} and, if the service is unreachable, fails soft to the
// provenance-labelled demo fixture so the Travel tab always renders something
// honest — never a blank error. The fixture carries `data_tier: "demo"`, which the
// UI surfaces.
import fixture from '../mocks/travelPlan.json'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function fetchTripPlan({ from, to, departure } = {}) {
  try {
    const response = await fetch(`${BASE_URL}/trip-plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ from: from || '', to: to || '', departure: departure || null }),
    })
    if (!response.ok) throw new Error(`Trip service returned ${response.status}`)
    return await response.json()
  } catch {
    return fixture // fail soft to the labelled demo fixture
  }
}
