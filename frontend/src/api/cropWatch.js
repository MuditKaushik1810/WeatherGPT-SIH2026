// Crop Watch data — the live composite GET /farmer/crop-watch (Architecture §3.10).
// This is the single swap-point (same pattern as api/cropPlanning): it calls the
// real endpoint and, if the service is unreachable, fails soft to the provenance-
// labelled demo fixture so the screen always renders something honest — never a
// blank error. The fixture carries `data_tier: "demo"`, which the UI surfaces.
import fixture from '../mocks/farmerCropWatch.json'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function fetchCropWatch({ crop, location, daysAfterSowing } = {}) {
  const params = new URLSearchParams({ crop: crop || '', location: location || '' })
  if (daysAfterSowing != null) params.set('days_after_sowing', String(daysAfterSowing))
  try {
    const response = await fetch(`${BASE_URL}/farmer/crop-watch?${params.toString()}`)
    if (!response.ok) throw new Error(`Crop watch service returned ${response.status}`)
    return await response.json()
  } catch {
    return fixture // fail soft to the labelled demo fixture
  }
}
