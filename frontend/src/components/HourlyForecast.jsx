import { getWeatherIcon } from '../data/weatherIcons'
import { useI18n } from '../i18n'

// Live hourly `time` values are ISO strings (e.g. "2026-09-07T09:00"). Show the
// first entry as "Now" and the rest as a local hour label. Parsing and
// formatting both happen in the browser's locale, so the hour shown matches the
// value regardless of timezone.
function formatHour(iso, index, nowLabel) {
  if (index === 0) return nowLabel
  const when = new Date(iso)
  if (Number.isNaN(when.getTime())) return iso
  return when.toLocaleTimeString('en-IN', { hour: 'numeric' })
}

function HourlyForecast({ forecast }) {
  const { t } = useI18n()
  return (
    <section className="forecast-section">
      <div className="section-heading">
        <div>
          <span className="eyebrow">{t('hourly.eyebrow')}</span>
          <h2>{t('hourly.title')}</h2>
        </div>
        <span className="section-note">{t('hourly.note')}</span>
      </div>

      <div className="forecast-card">
        {forecast.map((item, index) => (
          <div className={`forecast-item ${index === 0 ? 'current' : ''}`} key={item.time}>
            <span className="forecast-time">{formatHour(item.time, index, t('hourly.now'))}</span>
            <div className="forecast-icon">
              {getWeatherIcon(item.condition) || <span className="icon-placeholder">○</span>}
            </div>
            <strong>{item.temp}°</strong>
          </div>
        ))}

        <button
          className="forecast-arrow"
          type="button"
          aria-label={t('hourly.more')}
          title={t('hourly.more')}
          onClick={() => {}}
        >
          →
        </button>
      </div>
    </section>
  )
}

export default HourlyForecast
