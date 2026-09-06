// Presentation data for the Home screen only.
// Replace this object with the backend view model when the Home API is connected.

export const homeWeather = {
  location: 'Noida, Uttar Pradesh',
  temperature: 28,
  condition: 'Partly Cloudy',
  feelsLike: 31,
  rainChance: 30,
  humidity: 72,
  windSpeed: 12,
  aqi: 86,
  recommendation: {
    title: 'Good time for a short outing',
    message: 'The weather is comfortable right now. Keep an umbrella nearby in case the rain chance increases.',
  },
  hourlyForecast: [
    { time: 'Now', temperature: 28, condition: 'partly_cloudy' },
    { time: '9 AM', temperature: 29, condition: 'sunny' },
    { time: '12 PM', temperature: 30, condition: 'cloudy' },
    { time: '3 PM', temperature: 29, condition: 'cloudy' },
    { time: '6 PM', temperature: 27, condition: 'thunderstorm' },
  ],
}
