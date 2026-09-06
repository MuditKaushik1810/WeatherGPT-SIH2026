// Weather icon registry.
// Intentionally empty for now.
// Add fixed icon mappings here when the final SVG assets are added.
//
// Example later:
// import sunny from '../assets/weather/sunny.svg'
// export const weatherIcons = { sunny }

export const weatherIcons = {}

export function getWeatherIcon(condition) {
  return weatherIcons[condition] ?? null
}
