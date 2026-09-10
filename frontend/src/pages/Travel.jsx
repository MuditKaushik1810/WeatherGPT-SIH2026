import { useEffect, useState } from 'react'
import Header from '../components/Header'
import { fetchTripPlan } from '../api/tripPlan'
import { getDefaultLocation } from '../lib/preferences'
import { getSavedLocation } from '../lib/savedLocation'

const statusLabels = {
  good: 'Good stop',
  caution: 'Use caution',
  not_recommended: 'Not recommended',
}

const weatherSymbols = {
  sunny: '☀',
  'clear sky': '☀',
  'mainly clear': '🌤',
  'partly cloudy': '⛅',
  overcast: '☁',
  'light rain': '🌦',
  'slight rain': '🌦',
  rain: '🌧',
  'moderate rain': '🌧',
  'heavy rain': '⛈',
  thunderstorm: '⛈',
}

// Facility counts come through as a number, a capped "20+" string, or null when
// the lookup was unavailable — render a dash for the null case.
const facilityValue = (value) => (value == null ? '—' : value)

function Travel() {
  const initialOrigin = getDefaultLocation() || getSavedLocation() || 'Noida, Uttar Pradesh'

  // Committed origin/destination drive the fetch; the draft pair backs the inline
  // editor so typing doesn't re-fetch on every keystroke.
  const [origin, setOrigin] = useState(initialOrigin)
  const [destination, setDestination] = useState('Jaipur, Rajasthan')
  const [draftFrom, setDraftFrom] = useState(initialOrigin)
  const [draftTo, setDraftTo] = useState('Jaipur, Rajasthan')
  const [editing, setEditing] = useState(false)

  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedIndex, setSelectedIndex] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true)
    fetchTripPlan({ from: origin, to: destination })
      .then((view) => {
        if (!active) return
        setPlan(view)
        setSelectedIndex(0)
      })
      .catch(() => {})
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [origin, destination])

  const commitEdit = (event) => {
    event.preventDefault()
    setOrigin(draftFrom.trim() || origin)
    setDestination(draftTo.trim() || destination)
    setEditing(false)
  }

  const swap = () => {
    setDraftFrom(draftTo)
    setDraftTo(draftFrom)
    setOrigin(destination)
    setDestination(origin)
  }

  if (loading && !plan) {
    return (
      <main className="app-shell travel-shell">
        <div className="travel-page">
          <Header location={origin} />
          <section className="travel-content">
            <p className="travel-source-note" role="status">Planning your route…</p>
          </section>
        </div>
      </main>
    )
  }

  const isDemo = plan.data_tier === 'demo'
  const checkpoints = plan.checkpoints || []
  const hasCheckpoints = checkpoints.length > 0
  const selected = hasCheckpoints ? checkpoints[Math.min(selectedIndex, checkpoints.length - 1)] : null

  const selectCheckpoint = (index) => {
    if (index >= 0 && index < checkpoints.length) setSelectedIndex(index)
  }

  const provenance = isDemo
    ? 'Demo values — live trip service unavailable · routing & facilities via Geoapify, weather via WeatherAPI (Open-Meteo fallback)'
    : `Weather via ${plan.weather_source} · Routing & facilities via ${plan.routing_source}`

  return (
    <main className="app-shell travel-shell">
      <div className="travel-page">
        <Header location={origin} />

        <section className="travel-content">
          <div className="travel-title-row">
            <div>
              <span className="eyebrow">Trip planner</span>
              <h1>Travel</h1>
            </div>

            {isDemo && <span className="travel-demo-badge">Demo data</span>}
          </div>

          <section className="trip-card" aria-label="Trip details">
            {editing ? (
              <form className="trip-edit" onSubmit={commitEdit}>
                <label className="trip-edit-field">
                  <span className="trip-label">From</span>
                  <input
                    className="location-input"
                    value={draftFrom}
                    onChange={(e) => setDraftFrom(e.target.value)}
                    aria-label="Origin"
                  />
                </label>
                <label className="trip-edit-field">
                  <span className="trip-label">To</span>
                  <input
                    className="location-input"
                    value={draftTo}
                    onChange={(e) => setDraftTo(e.target.value)}
                    aria-label="Destination"
                  />
                </label>
                <div className="trip-edit-actions">
                  <button type="submit" className="trip-edit-plan">Plan trip</button>
                  <button
                    type="button"
                    className="trip-edit-cancel"
                    onClick={() => { setDraftFrom(origin); setDraftTo(destination); setEditing(false) }}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <>
                <div className="trip-location">
                  <span className="trip-marker from-marker">A</span>
                  <div>
                    <span className="trip-label">From</span>
                    <strong>{plan.route.from}</strong>
                  </div>
                </div>

                <button
                  className="trip-swap"
                  type="button"
                  aria-label="Swap origin and destination"
                  onClick={swap}
                >
                  ↕
                </button>

                <div className="trip-location">
                  <span className="trip-marker to-marker">B</span>
                  <div>
                    <span className="trip-label">To</span>
                    <strong>{plan.route.to}</strong>
                  </div>
                </div>

                <div className="trip-divider" />

                <div className="departure-row">
                  <span className="departure-icon" aria-hidden="true">◷</span>
                  <div>
                    <span className="trip-label">Departure</span>
                    <strong>{plan.departure.label}, {plan.departure.time}</strong>
                  </div>
                </div>

                <button
                  className="edit-trip-button"
                  type="button"
                  onClick={() => { setDraftFrom(origin); setDraftTo(destination); setEditing(true) }}
                >
                  Edit
                </button>
              </>
            )}
          </section>

          <section className="journey-overview" aria-label="Journey overview">
            <span className="eyebrow">Journey overview</span>

            <div className="journey-stats">
              <div className="journey-stat">
                <span className="journey-stat-icon">↔</span>
                <strong>{plan.route.distance_km != null ? `${plan.route.distance_km} km` : '—'}</strong>
                <span>Distance</span>
              </div>

              <div className="journey-stat">
                <span className="journey-stat-icon">◷</span>
                <strong>{plan.route.estimated_time ?? '—'}</strong>
                <span>Est. time</span>
              </div>

              <div className="journey-stat">
                <span className="journey-stat-icon">⌁</span>
                <strong>{plan.route.route_name ?? '—'}</strong>
                <span>Best route</span>
              </div>

              <div className="journey-condition">
                <span className="journey-condition-dot" />
                <div>
                  <strong>{plan.route.condition}</strong>
                  <span>Travel conditions</span>
                </div>
              </div>
            </div>
          </section>

          {hasCheckpoints ? (
            <>
              <section className="checkpoint-section" aria-label="Journey checkpoints">
                <div className="travel-title-row">
                  <div>
                    <span className="eyebrow">Journey checkpoints</span>
                  </div>
                  <span className="checkpoint-count">
                    {Math.min(selectedIndex, checkpoints.length - 1) + 1} / {checkpoints.length}
                  </span>
                </div>

                <div className="checkpoint-scroll">
                  <div className="checkpoint-track">
                    {checkpoints.map((checkpoint, index) => (
                      <button
                        key={checkpoint.id}
                        type="button"
                        className={`checkpoint-item ${index === selectedIndex ? 'selected' : ''}`}
                        onClick={() => selectCheckpoint(index)}
                        aria-label={`${checkpoint.name}, ${statusLabels[checkpoint.status]}`}
                        aria-pressed={index === selectedIndex}
                      >
                        <span className={`checkpoint-dot ${checkpoint.status}`} aria-hidden="true" />
                        <span className="checkpoint-name">{checkpoint.name}</span>
                        <span className="checkpoint-distance">{checkpoint.distance_km} km</span>
                        <span className="checkpoint-weather" aria-hidden="true">
                          {weatherSymbols[checkpoint.weather] ?? '•'}
                        </span>
                        <strong>{checkpoint.temperature != null ? `${checkpoint.temperature}°` : '—'}</strong>
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
                    <span><i className="good" />Good stop</span>
                    <span><i className="caution" />Use caution</span>
                    <span><i className="not-recommended" />Not recommended</span>
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
                  <strong>{selected.temperature != null ? `${selected.temperature}°` : '—'}</strong>
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
                  <strong>{selected.rain_probability != null ? `${selected.rain_probability}%` : '—'}</strong>
                </div>

                <p className="checkpoint-note">{selected.note}</p>

                <span className="eyebrow facility-heading">Nearby facilities</span>

                <div className="facility-grid">
                  <div>
                    <span>🍴</span>
                    <strong>{facilityValue(selected.facilities.restaurants)}</strong>
                    <small>Restaurants</small>
                  </div>
                  <div>
                    <span>⛽</span>
                    <strong>{facilityValue(selected.facilities.fuel_stations)}</strong>
                    <small>Fuel stations</small>
                  </div>
                  <div>
                    <span>🛏</span>
                    <strong>{facilityValue(selected.facilities.hotels)}</strong>
                    <small>Hotels</small>
                  </div>
                  <div>
                    <span>🏥</span>
                    <strong>{facilityValue(selected.facilities.hospitals)}</strong>
                    <small>Hospitals</small>
                  </div>
                  <div>
                    <span>🅿</span>
                    <strong>{selected.facilities.parking ? 'Yes' : 'No'}</strong>
                    <small>Parking</small>
                  </div>
                </div>

                <p className="travel-source-note">{provenance}</p>
              </section>
            </>
          ) : (
            <section className="selected-checkpoint" aria-label="Trip status">
              <p className="checkpoint-note">{plan.summary}</p>
              <p className="travel-source-note">{provenance}</p>
            </section>
          )}
        </section>
      </div>
    </main>
  )
}

export default Travel
