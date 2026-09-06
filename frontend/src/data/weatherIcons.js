// Weather icon registry.
// Intentionally empty for now.
// Add fixed icon mappings here when the final SVG assets are added.
//
// Keys are the backend's WMO condition strings (see the Open-Meteo connector's
// WEATHER_CODE_MAP) so lookups match real data — e.g. "clear sky",
// "partly cloudy", "overcast", "slight rain", "thunderstorm".
//
// Example later:
// import clearSky from '../assets/weather/clear-sky.svg'
// export const weatherIcons = { 'clear sky': clearSky }

export const weatherIcons = {}

export function getWeatherIcon(condition) {
  return weatherIcons[condition] ?? null
}
