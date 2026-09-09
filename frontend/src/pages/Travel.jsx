import { useState } from 'react'
import Header from '../components/Header'
import travelPlan from '../mocks/travelPlan.json'

const statusLabels = {
  good: 'Good stop',
  caution: 'Use caution',
  not_recommended: 'Not recommended',
}

const weatherSymbols = {
  sunny: '☀',
  'partly cloudy': '⛅',
  'light rain': '🌦',
  rain: '🌧',
}

function Travel() {
  const [selectedIndex, setSelectedIndex] = useState(1)

  const checkpoints = travelPlan.checkpoints
  const selected = checkpoints[selectedIndex]

  const selectCheckpoint = (index) => {
    if (index >= 0 && index < checkpoints.length) {
      setSelectedIndex(index)
    }
  }

  return (
    <main className="app-shell travel-shell">
      <div className="travel-page">
        <Header location="Noida, Uttar Pradesh" />

        <section className="travel-content">
          <div className="travel-title-row">
            <div>
              <span className="eyebrow">Trip planner</span>
              <h1>Travel</h1>
            </div>

            <span className="travel-demo-badge">Demo data</span>
          </div>

          <section className="trip-card" aria-label="Trip details">
            <div className="trip-location">
              <span className="trip-marker from-marker">A</span>
              <div>
                <span className="trip-label">From</span>
                <strong>{travelPlan.route.from}</strong>
              </div>
            </div>

            <button
              className="trip-swap"
              type="button"
              aria-label="Swap origin and destination"
              onClick={() => {}}
            >
              ↕
            </button>

            <div className="trip-location">
              <span className="trip-marker to-marker">B</span>
              <div>
                <span className="trip-label">To</span>
                <strong>{travelPlan.route.to}</strong>
              </div>
            </div>

            <div className="trip-divider" />

            <div className="departure-row">
              <span className="departure-icon" aria-hidden="true">
                ◷
              </span>

              <div>
                <span className="trip-label">Departure</span>
                <strong>
                  {travelPlan.departure.label}, {travelPlan.departure.time}
                </strong>
              </div>
            </div>

            <button className="edit-trip-button" type="button">
              Edit
            </button>
          </section>

          <section className="journey-overview" aria-label="Journey overview">
            <span className="eyebrow">Journey overview</span>

            <div className="journey-stats">
              <div className="journey-stat">
                <span className="journey-stat-icon">↔</span>
                <strong>{travelPlan.route.distance_km} km</strong>
                <span>Distance</span>
              </div>

              <div className="journey-stat">
                <span className="journey-stat-icon">◷</span>
                <strong>{travelPlan.route.estimated_time}</strong>
                <span>Est. time</span>
              </div>

              <div className="journey-stat">
                <span className="journey-stat-icon">⌁</span>
                <strong>{travelPlan.route.route_name}</strong>
                <span>Best route</span>
              </div>

              <div className="journey-condition">
                <span className="journey-condition-dot" />
                <div>
                  <strong>{travelPlan.route.condition}</strong>
                  <span>Travel conditions</span>
                </div>
              </div>
            </div>
          </section>

          <section className="checkpoint-section" aria-label="Journey checkpoints">
            <div className="travel-title-row">
              <div>
                <span className="eyebrow">Journey checkpoints</span>
              </div>

              <span className="checkpoint-count">
                {selectedIndex + 1} / {checkpoints.length}
              </span>
            </div>

            <div className="checkpoint-scroll">
              <div className="checkpoint-track">
                {checkpoints.map((checkpoint, index) => (
                  <button
                    key={checkpoint.id}
                    type="button"
                    className={`checkpoint-item ${
                      index === selectedIndex ? 'selected' : ''
                    }`}
                    onClick={() => selectCheckpoint(index)}
                    aria-label={`${checkpoint.name}, ${statusLabels[checkpoint.status]}`}
                    aria-pressed={index === selectedIndex}
                  >
                    <span
                      className={`checkpoint-dot ${checkpoint.status}`}
                      aria-hidden="true"
                    />

                    <span className="checkpoint-name">
                      {checkpoint.name}
                    </span>

                    <span className="checkpoint-distance">
                      {checkpoint.distance_km} km
                    </span>

                    <span className="checkpoint-weather" aria-hidden="true">
                      {weatherSymbols[checkpoint.weather] ?? '•'}
                    </span>

                    <strong>{checkpoint.temperature}°</strong>
                  </button>
                ))}
              </div>
            </div>

            <div className="checkpoint-controls">
              <button
                type="button"
                aria-label="Previous checkpoint"
                disabled={selectedIndex === 0}
                onClick={() => selectCheckpoint(selectedIndex - 1)}
              >
                ←
              </button>

              <div className="checkpoint-legend">
                <span>
                  <i className="good" />
                  Good stop
                </span>

                <span>
                  <i className="caution" />
                  Use caution
                </span>

                <span>
                  <i className="not-recommended" />
                  Not recommended
                </span>
              </div>

              <button
                type="button"
                aria-label="Next checkpoint"
                disabled={selectedIndex === checkpoints.length - 1}
                onClick={() => selectCheckpoint(selectedIndex + 1)}
              >
                →
              </button>
            </div>
          </section>

          <section className="selected-checkpoint" aria-label="Selected checkpoint">
            <div className="selected-checkpoint-top">
              <div>
                <span className="eyebrow">Selected checkpoint</span>
                <h2>{selected.name}</h2>
              </div>

              <span className={`checkpoint-status-pill ${selected.status}`}>
                {statusLabels[selected.status]}
              </span>
            </div>

            <div className="checkpoint-main-weather">
              <span className="selected-weather-icon" aria-hidden="true">
                {weatherSymbols[selected.weather] ?? '•'}
              </span>

              <strong>{selected.temperature}°</strong>

              <div>
                <span>ETA</span>
                <strong>{selected.eta}</strong>
              </div>

              <div>
                <span>From start</span>
                <strong>{selected.distance_km} km</strong>
              </div>
            </div>

            <div className="rain-risk">
              <span>Rain probability</span>
              <strong>{selected.rain_probability}%</strong>
            </div>

            <p className="checkpoint-note">{selected.note}</p>

            <span className="eyebrow facility-heading">
              Nearby facilities
            </span>

            <div className="facility-grid">
              <div>
                <span>🍴</span>
                <strong>{selected.facilities.restaurants}</strong>
                <small>Restaurants</small>
              </div>

              <div>
                <span>⛽</span>
                <strong>{selected.facilities.fuel_stations}</strong>
                <small>Fuel stations</small>
              </div>

              <div>
                <span>🛏</span>
                <strong>{selected.facilities.hotels}</strong>
                <small>Hotels</small>
              </div>

              <div>
                <span>🏥</span>
                <strong>{selected.facilities.hospitals}</strong>
                <small>Hospitals</small>
              </div>

              <div>
                <span>🅿</span>
                <strong>{selected.facilities.parking ? 'Yes' : 'No'}</strong>
                <small>Parking</small>
              </div>
            </div>

            <p className="travel-source-note">
              Demo values only · Weather via Open-Meteo · Routing &amp; facilities via Geoapify (planned)
            </p>
          </section>
        </section>
      </div>
    </main>
  )
}

export default Travel
