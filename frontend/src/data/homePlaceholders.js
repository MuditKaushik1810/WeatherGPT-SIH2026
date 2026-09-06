// Presentation-only placeholder data for the Home screen.
//
// These two blocks are NOT yet backed by a real endpoint in the API contract
// (Architecture doc, Section 3.10) — the normalized weather record is
// current-conditions only:
//   - hourlyForecast  → awaits a forecast-series endpoint. The Open-Meteo
//     connector already fetches the hourly arrays (`_raw_hourly`); exposing them
//     as a contract shape is future work.
//   - recommendation  → awaits the advisory / grounded-LLM endpoint.
//
// Until those endpoints exist, this stays clearly-labeled mock data, kept
// SEPARATE from the contract-faithful current-conditions mock in
// ../mocks/homeWeather.json (which mirrors the real /weather record exactly).
//
// `condition` values use the backend's WMO vocabulary (see the Open-Meteo
// connector's WEATHER_CODE_MAP) so the icon lookup keys will match real data
// when these are wired to a live endpoint.

export const hourlyForecast = [
  { time: 'Now', temp: 28, condition: 'partly cloudy' },
  { time: '9 AM', temp: 29, condition: 'clear sky' },
  { time: '12 PM', temp: 30, condition: 'overcast' },
  { time: '3 PM', temp: 29, condition: 'overcast' },
  { time: '6 PM', temp: 27, condition: 'thunderstorm' },
]

export const recommendation = {
  title: 'Good time for a short outing',
  message:
    'The weather is comfortable right now. Keep an umbrella nearby in case the rain chance increases.',
}
