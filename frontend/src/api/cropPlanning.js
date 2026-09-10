// Crop Planning data — the live composite GET /farmer/crop-planning (Architecture
// §3.10). Single swap-point (same pattern as api/cropWatch): it calls the real
// endpoint and, if the service is unreachable, fails soft to the provenance-
// labelled demo fixture so the screen always renders something honest. The fixture
// carries `data_tier: "demo"`, which the UI surfaces.
import fixture from '../mocks/farmerCropPlanning.json'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function fetchCropPlanning(location) {
  const params = new URLSearchParams({ location: location || '' })
  try {
    const response = await fetch(`${BASE_URL}/farmer/crop-planning?${params.toString()}`)
    if (!response.ok) throw new Error(`Crop planning service returned ${response.status}`)
    return await response.json()
  } catch {
    return fixture // fail soft to the labelled demo fixture
  }
}
