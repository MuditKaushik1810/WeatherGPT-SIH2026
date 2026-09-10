import { useEffect, useState } from 'react'
import { fetchCropWatch } from '../api/cropWatch'
import { getSavedLocation } from '../lib/savedLocation'
import { getFarmerPrefs, getDefaultLocation, daysAfterSowing, setPersona } from '../lib/preferences'

// The five growth stages the backend reports (§3.7). The timeline is driven by the
// crop's actual `crop_stage` — complete before it, current, next, then future.
const STAGES = ['Germination', 'Vegetative', 'Flowering', 'Yield Formation', 'Maturity']

function stageTimeline(currentStage) {
  const idx = STAGES.indexOf(currentStage)
  return STAGES.map((label, i) => ({
    label,
    symbol: String(i + 1).padStart(2, '0'),
    state: idx < 0 ? 'future' : i < idx ? 'complete' : i === idx ? 'current' : i === idx + 1 ? 'next' : 'future',
  }))
}

const THREAT_SYMBOLS = { heat: 'H', cold: 'C', dry_soil: 'M', waterlogging: 'W', disease: 'D', rain: 'R' }
const symbolFor = (id) => THREAT_SYMBOLS[id] || '!'

function goTo(hash) {
  window.location.hash = hash
}

// Leaving Farmer Mode switches the persona back to normal (persisted).
function exitFarmerMode() {
  setPersona('normal')
  goTo('#home')
}

function CropWatch() {
  const [data, setData] = useState(null)

  useEffect(() => {
    let active = true
    const prefs = getFarmerPrefs()
    const crop = prefs.crop || 'wheat'
    const location = prefs.location || getDefaultLocation() || getSavedLocation() || 'Delhi'
    fetchCropWatch({ crop, location, daysAfterSowing: daysAfterSowing(prefs.sowingDate) })
      .then((view) => { if (active) setData(view) })
      .catch(() => {})
    return () => { active = false }
  }, [])

  if (!data) {
    return (
      <main className="app-shell farmer-shell">
        <section className="farmer-page">
          <p className="farmer-demo-note" role="status">Loading crop status…</p>
        </section>
      </main>
    )
  }

  const isDemo = data.data_tier === 'demo'
  const stages = stageTimeline(data.crop_stage)
  const threats = data.threats || []
  const action = data.recommended_action || { title: '', items: [] }

  return (
    <main className="app-shell farmer-shell">
      <div className="farmer-page">
        <header className="farmer-header">
          <button className="farmer-menu-button" type="button" aria-label="Open menu" title="Menu" onClick={() => {}}>
            <span />
            <span />
            <span />
          </button>

          <div className="farmer-brand" aria-label="WeatherGPT">
            <span className="farmer-brand-mark" aria-hidden="true">W</span>
            <strong>WeatherGPT</strong>
          </div>

          <button
            className="farmer-mode-switch"
            type="button"
            onClick={exitFarmerMode}
            aria-label="Switch to normal WeatherGPT mode"
          >
            <span aria-hidden="true">◆</span>
            Farmer Mode
            <span aria-hidden="true">⌄</span>
          </button>
        </header>

        <section className="farmer-location-card" aria-label="Farm location">
          <div className="farmer-landscape" aria-hidden="true">
            <span className="farmer-sun" />
            <span className="farmer-mountain mountain-one" />
            <span className="farmer-mountain mountain-two" />
            <span className="farmer-field field-back" />
            <span className="farmer-field field-front" />
          </div>
          <div className="farmer-location-label">
            <span aria-hidden="true">●</span>
            {data.location}
          </div>
        </section>

        <section className="farmer-title-card">
          <div className="farmer-leaf-mark" aria-hidden="true">✦</div>
          <div>
            <h1>Crop Watch</h1>
            <p>Protect what you're growing</p>
            <span>Real-time insights on weather risks, crop health and personalised actions for your farm.</span>
          </div>
          {data.risk_score != null && (
            <span className={`crop-risk-badge risk-${String(data.risk_level || '').toLowerCase().replace(/ /g, '-')}`}>
              Risk {data.risk_level} · {data.risk_score}
            </span>
          )}
        </section>

        <section className="crop-details-card" aria-labelledby="crop-details-heading">
          <div className="farmer-section-heading">
            <span className="section-icon crop-icon" aria-hidden="true">✦</span>
            <h2 id="crop-details-heading">Your Crop Details</h2>
          </div>

          <div className="crop-detail-grid">
            <div>
              <span>Crop Type</span>
              <strong style={{ textTransform: 'capitalize' }}>{data.crop}</strong>
            </div>
            <div>
              <span>Days After Sowing</span>
              <strong>{data.days_after_sowing != null ? `${data.days_after_sowing} days` : '—'}</strong>
            </div>
            <div>
              <span>Crop Stage</span>
              <strong>{data.crop_stage ? `${data.crop_stage} → ${data.next_stage}` : 'Set a sowing date'}</strong>
            </div>
          </div>

          <div className="crop-stage-timeline" aria-label="Crop growth stage">
            {stages.map((stage, index) => (
              <div key={stage.label} className={`crop-stage ${stage.state}`}>
                <span className="crop-stage-node">{stage.symbol}</span>
                <span>{stage.label}</span>
                {index < stages.length - 1 && <i aria-hidden="true" />}
              </div>
            ))}
          </div>
          {!data.crop_stage && (
            <p className="farmer-demo-note">Add your sowing date in Settings to see the growth stage and stage-specific disease risk.</p>
          )}
        </section>

        <section className="weather-threats-card" aria-labelledby="threats-heading">
          <div className="farmer-section-heading">
            <span className="section-icon alert-icon" aria-hidden="true">!</span>
            <div>
              <h2 id="threats-heading">Weather Threats</h2>
              <p>Based on current conditions, forecast and crop stage</p>
            </div>
          </div>

          {threats.length === 0 ? (
            <p className="farmer-demo-note">No notable weather threats for {data.crop} right now.</p>
          ) : (
            <div className="threat-list">
              {threats.map((threat) => (
                <button key={threat.id} className="threat-row" type="button">
                  <span className={`threat-icon ${threat.id}`} aria-hidden="true">{symbolFor(threat.id)}</span>
                  <span className="threat-copy">
                    <strong>{threat.label}</strong>
                    <small>{threat.detail}</small>
                  </span>
                  <span className={`threat-level ${String(threat.level).toLowerCase()}`}>{threat.level}</span>
                  <span className="threat-arrow" aria-hidden="true">›</span>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="farmer-action-card" aria-labelledby="action-heading">
          <span className="action-icon" aria-hidden="true">!</span>
          <div>
            <h2 id="action-heading">Recommended Action</h2>
            <strong>{action.title}</strong>
            <ul>
              {(action.items || []).map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
          <span className="action-arrow" aria-hidden="true">›</span>
        </section>

        {data.climate_context && (
          <section className="climate-context-card" aria-labelledby="climate-heading">
            <span className="climate-icon" aria-hidden="true">◎</span>
            <div>
              <h2 id="climate-heading">Climate Context</h2>
              <div className="climate-title-row">
                <strong>{data.climate_context.title}</strong>
                {data.climate_context.level && (
                  <span className="threat-level moderate">{data.climate_context.level}</span>
                )}
              </div>
              <p>{data.climate_context.detail}</p>
            </div>
            <span className="action-arrow" aria-hidden="true">›</span>
          </section>
        )}

        <p className="farmer-demo-note">
          {isDemo
            ? 'Demo data · showing a frontend fixture (the live service was unreachable).'
            : `Live · ${data.source || 'WeatherGPT'}${data.provisional ? ' · provisional crop thresholds' : ''}`}
        </p>

        <nav className="farmer-bottom-nav" aria-label="Farmer Mode navigation">
          <button type="button" onClick={() => goTo('#farmer/planning')} aria-label="Crop Planning">
            <span aria-hidden="true">◇</span>
            <span>Crop Planning</span>
          </button>
          <button type="button" className="active" aria-current="page">
            <span aria-hidden="true">◆</span>
            <span>Crop Watch</span>
          </button>
        </nav>
      </div>
    </main>
  )
}

export default CropWatch
