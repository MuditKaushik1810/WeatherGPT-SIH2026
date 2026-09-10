import { useEffect, useState } from 'react'
import { fetchCropWatch } from '../api/cropWatch'
import { getSavedLocation } from '../lib/savedLocation'
import { getFarmerPrefs, getDefaultLocation, daysAfterSowing, setPersona } from '../lib/preferences'
import { useI18n } from '../i18n'

// The five growth stages the backend reports (§3.7). English keys drive the
// current-stage matching against `crop_stage`; the labels are localized for display.
const STAGES = ['Germination', 'Vegetative', 'Flowering', 'Yield Formation', 'Maturity']
const STAGE_KEY = {
  Germination: 'farmer.stageGermination', Vegetative: 'farmer.stageVegetative',
  Flowering: 'farmer.stageFlowering', 'Yield Formation': 'farmer.stageYieldFormation',
  Maturity: 'farmer.stageMaturity',
}

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
  const { t } = useI18n()
  const [data, setData] = useState(null)

  // Localize a stage name for display, keep unknown values (e.g. "Harvest") as-is.
  const stageLabel = (s) => (STAGE_KEY[s] ? t(STAGE_KEY[s]) : s)

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
          <p className="farmer-demo-note" role="status">{t('farmer.loadingWatch')}</p>
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
          <button className="farmer-menu-button" type="button" aria-label={t('farmer.openMenu')} title={t('farmer.openMenu')} onClick={() => {}}>
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
            aria-label={t('farmer.modeSwitchAria')}
          >
            <span aria-hidden="true">◆</span>
            {t('farmer.modeSwitch')}
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
            <h1>{t('farmer.cropWatch')}</h1>
            <p>{t('farmer.watchTagline')}</p>
            <span>{t('farmer.watchIntro')}</span>
          </div>
          {data.risk_score != null && (
            <span className={`crop-risk-badge risk-${String(data.risk_level || '').toLowerCase().replace(/ /g, '-')}`}>
              {t('farmer.risk')} {data.risk_level} · {data.risk_score}
            </span>
          )}
        </section>

        <section className="crop-details-card" aria-labelledby="crop-details-heading">
          <div className="farmer-section-heading">
            <span className="section-icon crop-icon" aria-hidden="true">✦</span>
            <h2 id="crop-details-heading">{t('farmer.yourCropDetails')}</h2>
          </div>

          <div className="crop-detail-grid">
            <div>
              <span>{t('farmer.cropType')}</span>
              <strong style={{ textTransform: 'capitalize' }}>{data.crop}</strong>
            </div>
            <div>
              <span>{t('farmer.daysAfterSowing')}</span>
              <strong>{data.days_after_sowing != null ? t('farmer.daysValue', { n: data.days_after_sowing }) : '—'}</strong>
            </div>
            <div>
              <span>{t('farmer.cropStage')}</span>
              <strong>{data.crop_stage ? `${stageLabel(data.crop_stage)} → ${stageLabel(data.next_stage)}` : t('farmer.setSowingDate')}</strong>
            </div>
          </div>

          <div className="crop-stage-timeline" aria-label="Crop growth stage">
            {stages.map((stage, index) => (
              <div key={stage.label} className={`crop-stage ${stage.state}`}>
                <span className="crop-stage-node">{stage.symbol}</span>
                <span>{stageLabel(stage.label)}</span>
                {index < stages.length - 1 && <i aria-hidden="true" />}
              </div>
            ))}
          </div>
          {!data.crop_stage && (
            <p className="farmer-demo-note">{t('farmer.stageHint')}</p>
          )}
        </section>

        <section className="weather-threats-card" aria-labelledby="threats-heading">
          <div className="farmer-section-heading">
            <span className="section-icon alert-icon" aria-hidden="true">!</span>
            <div>
              <h2 id="threats-heading">{t('farmer.weatherThreats')}</h2>
              <p>{t('farmer.threatsSubtitle')}</p>
            </div>
          </div>

          {threats.length === 0 ? (
            <p className="farmer-demo-note">{t('farmer.noThreats', { crop: data.crop })}</p>
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
            <h2 id="action-heading">{t('farmer.recommendedAction')}</h2>
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
              <h2 id="climate-heading">{t('farmer.climateContext')}</h2>
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
            ? t('farmer.demoNote')
            : `${t('farmer.livePrefix')}${data.source || 'WeatherGPT'}${data.provisional ? ` · ${t('farmer.provisionalThresholds')}` : ''}`}
        </p>

        <nav className="farmer-bottom-nav" aria-label="Farmer Mode navigation">
          <button type="button" onClick={() => goTo('#farmer/planning')} aria-label={t('farmer.cropPlanning')}>
            <span aria-hidden="true">◇</span>
            <span>{t('farmer.cropPlanning')}</span>
          </button>
          <button type="button" className="active" aria-current="page">
            <span aria-hidden="true">◆</span>
            <span>{t('farmer.cropWatch')}</span>
          </button>
        </nav>
      </div>
    </main>
  )
}

export default CropWatch
