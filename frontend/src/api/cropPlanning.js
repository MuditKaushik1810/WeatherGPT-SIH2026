// Crop Planning data — currently the demo fixture, served behind the documented
// GET /farmer/crop-planning shape (Architecture doc §3.10). Keeping the fixture
// behind this async function is the single swap point: when the backend lands,
// replace the body with a real fetch and no screen code changes.
//
// The fixture is provenance-labelled (`data_tier: "demo"`), and the UI surfaces
// that — it is never presented as live agronomic advice.
import fixture from '../mocks/farmerCropPlanning.json'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// eslint-disable-next-line no-unused-vars -- `location` is part of the real
// signature; the demo fixture ignores it until the backend exists.
export async function fetchCropPlanning(location) {
  // Demo: resolve the local fixture. Real backend (later):
  //   const r = await fetch(`${BASE_URL}/farmer/crop-planning?location=${encodeURIComponent(location)}`)
  //   if (!r.ok) throw new Error(`Crop planning service returned ${r.status}`)
  //   return r.json()
  void BASE_URL
  return fixture
}
