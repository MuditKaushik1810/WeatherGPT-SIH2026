import ProvenanceChip from './ProvenanceChip'

// Show a metric value with its unit, or an em dash when it's null. The contract
// allows any metric to be null when its source is unavailable (see CLAUDE.md),
// so the UI must tolerate that rather than render "null%".
function show(value, unit = '') {
  return value == null ? '—' : `${value}${unit}`
}

function WeatherPostcard({ weather }) {
  const rain =
    weather.precipitation_chance == null
      ? '—'
      : `${Math.round(weather.precipitation_chance * 100)}%`

  return (
    <section className="weather-postcard">
      <div className="postcard-artwork" aria-label="City postcard artwork placeholder">
        <div className="postcard-sun" />
        <div className="postcard-skyline">
          <span className="minaret" />
          <span className="dome" />
          <span className="building building-one" />
          <span className="building building-two" />
          <span className="building building-three" />
        </div>
        <span className="postcard-placeholder">Postcard artwork</span>

        <div className="postcard-weather">
          <ProvenanceChip source={weather.source} dataTier={weather.data_tier} />

          <div className="temperature">{show(weather.temp, '°C')}</div>
          <div className="condition">{weather.condition ?? 'Unavailable'}</div>
          <div className="feels-like">Feels like {show(weather.feels_like, '°C')}</div>
        </div>
      </div>

      <div className="weather-metrics">
        <div className="metric">
          <span className="metric-icon">💧</span>
          <div>
            <strong>{show(weather.humidity, '%')}</strong>
            <span>Humidity</span>
          </div>
        </div>

        <div className="metric">
          <span className="metric-icon">🌧</span>
          <div>
            <strong>{rain}</strong>
            <span>Rain</span>
          </div>
        </div>

        <div className="metric">
          <span className="metric-icon">💨</span>
          <div>
            <strong>{show(weather.wind_speed, ' km/h')}</strong>
            <span>Wind</span>
          </div>
        </div>

        <div className="metric">
          <span className="metric-icon">◌</span>
          <div>
            <strong>{show(weather.aqi)}</strong>
            <span>AQI</span>
          </div>
        </div>
      </div>
    </section>
  )
}

export default WeatherPostcard
