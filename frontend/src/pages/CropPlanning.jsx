import { useEffect, useState } from 'react'
import { fetchCropPlanning } from '../api/cropPlanning'
import { getSavedLocation } from '../lib/savedLocation'
import { getFarmerPrefs, getDefaultLocation, setPersona } from '../lib/preferences'
import { useI18n } from '../i18n'

// Suitability + season are small backend enums — localized for display via a map,
// falling back to the raw value + English suffix for anything unexpected.
const SUIT_KEY = {
  Excellent: 'farmer.suitExcellent', Good: 'farmer.suitGood',
  Fair: 'farmer.suitFair', Marginal: 'farmer.suitMarginal',
}
const SEASON_KEY = { Kharif: 'farmer.seasonKharif', Rabi: 'farmer.seasonRabi' }

function goTo(hash) {
  window.location.hash = hash
}

// Leaving Farmer Mode switches the persona back to normal (persisted).
function exitFarmerMode() {
  setPersona('normal')
  goTo('#home')
}

export default function CropPlanning() {
  const { t } = useI18n()
  // Data comes through the api module (live GET /farmer/crop-planning, demo fixture
  // as fail-soft fallback — §3.10). The screen is built against that stable shape.
  const [data, setData] = useState(null)

  useEffect(() => {
    let active = true
    const prefs = getFarmerPrefs()
    const location = prefs.location || getDefaultLocation() || getSavedLocation() || 'Delhi'
    fetchCropPlanning(location)
      .then((view) => { if (active) setData(view) })
      .catch(() => {})
    return () => { active = false }
  }, [])

  if (!data) {
    return (
      <main className="app-shell farmer-shell">
        <section className="farmer-page">
          <p className="farmer-demo-note" role="status">{t('farmer.loadingPlanning')}</p>
        </section>
      </main>
    )
  }

  const suitLabel = (s) => (SUIT_KEY[s] ? t(SUIT_KEY[s]) : `${s} fit`)
  const seasonLabel = (s) => (SEASON_KEY[s] ? t(SEASON_KEY[s]) : `${s} season`)

  return (
    <main className="app-shell farmer-shell">
      <section className="farmer-page">
        <header className="farmer-header">
          <button className="farmer-menu-button" type="button" aria-label={t('farmer.openMenu')}>
            ☰
          </button>

          <div className="farmer-brand">
            <span className="farmer-brand-mark">W</span>
            <span>WeatherGPT</span>
          </div>

          <button
            className="farmer-mode-switch"
            type="button"
            onClick={exitFarmerMode}
            aria-label={t('farmer.modeSwitchAria')}
          >
            {t('farmer.modeSwitch')}
          </button>
        </header>

        <section className="farmer-location-card">
          <div className="farmer-landscape" aria-hidden="true">
            <div className="farmer-sun" />
            <div className="farmer-hill farmer-hill-back" />
            <div className="farmer-hill farmer-hill-front" />
            <div className="farmer-field" />
          </div>

          <div className="farmer-location-content">
            <span>{t('farmer.currentLocation')}</span>
            <strong>{data.location}</strong>
          </div>
        </section>

        <section className="farmer-title-card">
          <div className="farmer-leaf-mark" aria-hidden="true">
            🌱
          </div>

          <div>
            <h1>{t('farmer.cropPlanning')}</h1>
            <p>{t('farmer.planningTagline')}</p>
          </div>
        </section>

        <section className="crop-planning-intro">
          <p>{t('farmer.planningIntro')}</p>
        </section>

        <section className="crop-recommendation-card">
          <div className="farmer-section-heading">
            <span className="section-icon" aria-hidden="true">✦</span>
            <div>
              <h2>{t('farmer.recommendedCrops')}</h2>
              <p>{t('farmer.bestFit')}</p>
            </div>
          </div>

          <div className="crop-recommendation-list">
            {data.recommendations.map((crop, index) => (
              <article
                className={`crop-recommendation-item ${index === 0 ? 'featured' : ''}`}
                key={crop.crop}
              >
                <div className="crop-recommendation-main">
                  <h3>{crop.crop}</h3>
                  <span className="crop-suitability">{suitLabel(crop.suitability)}</span>
                </div>

                <p>{crop.reason}</p>

                <div className="crop-harvest-window">
                  <span>{t('farmer.approxHarvest')}</span>
                  <strong>{crop.harvest_window}</strong>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="climate-context-card climate-context-block">
          <div className="farmer-section-heading">
            <span className="climate-icon" aria-hidden="true">☁</span>
            <div>
              <h2>{t('farmer.climateFit')}</h2>
              <p>{seasonLabel(data.season)}</p>
            </div>
          </div>

          <p>{data.climate_context.summary}</p>

          <div className="historical-climate-note">
            <strong>{t('farmer.historicalClimate')}</strong>
            <span>{data.climate_context.historical_note}</span>
          </div>
        </section>

        <p className="farmer-demo-note">
          {data.data_tier === 'demo'
            ? t('farmer.demoNote')
            : `${t('farmer.livePrefix')}${data.source || 'WeatherGPT'} · ${t('farmer.planningLiveNote')}`}
        </p>

        <nav className="farmer-bottom-nav" aria-label="Farmer Mode navigation">
          <button className="active" type="button" aria-current="page">
            <span aria-hidden="true">🌱</span>
            <span>{t('farmer.cropPlanning')}</span>
          </button>

          <button type="button" onClick={() => goTo('#farmer/watch')}>
            <span aria-hidden="true">◉</span>
            <span>{t('farmer.cropWatch')}</span>
          </button>
        </nav>
      </section>
    </main>
  )
}
