function WeatherPostcard({ weather }) {
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
      </div>

      <div className="postcard-info">
        <div className="temperature-row">
          <div>
            <div className="temperature">{weather.temperature}°C</div>
            <div className="condition">{weather.condition}</div>
            <div className="feels-like">Feels like {weather.feelsLike}°C</div>
          </div>
        </div>

        <div className="weather-metrics">
          <div className="metric">
            <span className="metric-icon">💧</span>
            <div>
              <strong>{weather.humidity}%</strong>
              <span>Humidity</span>
            </div>
          </div>

          <div className="metric">
            <span className="metric-icon">🌧</span>
            <div>
              <strong>{weather.rainChance}%</strong>
              <span>Rain</span>
            </div>
          </div>

          <div className="metric">
            <span className="metric-icon">💨</span>
            <div>
              <strong>{weather.windSpeed} km/h</strong>
              <span>Wind</span>
            </div>
          </div>

          <div className="metric">
            <span className="metric-icon">◌</span>
            <div>
              <strong>{weather.aqi}</strong>
              <span>AQI</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default WeatherPostcard
