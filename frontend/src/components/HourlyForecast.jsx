import { getWeatherIcon } from '../data/weatherIcons'

function HourlyForecast({ forecast }) {
  return (
    <section className="forecast-section">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Next few hours</span>
          <h2>Hourly Forecast</h2>
        </div>
        <span className="section-note">3-hour intervals</span>
      </div>

      <div className="forecast-card">
        {forecast.map((item, index) => (
          <div className={`forecast-item ${index === 0 ? 'current' : ''}`} key={item.time}>
            <span className="forecast-time">{item.time}</span>
            <div className="forecast-icon">
              {getWeatherIcon(item.condition) || <span className="icon-placeholder">○</span>}
            </div>
            <strong>{item.temperature}°</strong>
          </div>
        ))}

        <button
          className="forecast-arrow"
          type="button"
          aria-label="More hourly forecast"
          title="More forecast"
          onClick={() => {}}
        >
          →
        </button>
      </div>
    </section>
  )
}

export default HourlyForecast
