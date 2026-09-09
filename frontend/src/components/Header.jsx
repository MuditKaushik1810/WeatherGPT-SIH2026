import { useEffect, useState } from 'react'
import { useI18n } from '../i18n'
import { setPersona } from '../lib/preferences'

// "Updated just now" was misleading — the weather isn't re-fetched every second.
// Show how long ago the data was actually fetched, refreshed live, and give the
// user a reload button to pull fresh data on demand (spins while fetching).
function formatRelative(ts, t) {
  const secs = Math.max(0, Math.floor((Date.now() - ts) / 1000))
  if (secs < 45) return t('header.justNow')
  const mins = Math.round(secs / 60)
  if (mins < 60) return t('header.minAgo', { n: mins })
  const hrs = Math.round(mins / 60)
  return hrs === 1 ? t('header.hrAgo1') : t('header.hrAgo', { n: hrs })
}

function Header({ location, updatedAt = null, loading = false, onReload }) {
  const { t } = useI18n()
  const [, setTick] = useState(0)
  const [menuOpen, setMenuOpen] = useState(false)

  // Re-render every 30s so the relative "updated" label stays truthful.
  useEffect(() => {
    if (!updatedAt) return undefined
    const id = setInterval(() => setTick((tk) => tk + 1), 30000)
    return () => clearInterval(id)
  }, [updatedAt])

  const showReload = Boolean(updatedAt) || loading

  // Enter the farmer persona (a separate mode, not a tab). Persist it so the app
  // reopens into Farmer Mode, and land on Crop Watch — its internal nav takes over.
  const enterFarmerMode = () => {
    setPersona('farmer')
    setMenuOpen(false)
    window.location.hash = 'farmer/watch'
  }

  const openSettings = () => {
    setMenuOpen(false)
    window.location.hash = 'settings'
  }

  return (
    <header className="header">
      <div className="header-menu-wrap">
        <button
          className="icon-button"
          type="button"
          aria-label={t('header.menu')}
          title={t('header.menu')}
          aria-haspopup="menu"
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((open) => !open)}
        >
          <span className="hamburger-line" />
          <span className="hamburger-line" />
          <span className="hamburger-line" />
        </button>

        {menuOpen && (
          <>
            <button
              type="button"
              className="header-menu-overlay"
              aria-label="Close menu"
              onClick={() => setMenuOpen(false)}
            />
            <div className="header-menu" role="menu">
              <button type="button" role="menuitem" className="header-menu-item" onClick={enterFarmerMode}>
                <span aria-hidden="true">🌾</span> {t('menu.farmerMode')}
              </button>
              <button type="button" role="menuitem" className="header-menu-item" onClick={openSettings}>
                <span aria-hidden="true">⚙</span> {t('settings.title')}
              </button>
            </div>
          </>
        )}
      </div>

      <div className="location-block">
        <div className="location-row">
          <span className="location-pin" aria-hidden="true">⌖</span>
          <span className="location-name">{location || t('header.setLocation')}</span>
        </div>
        {updatedAt && <span className="updated-text">{t('header.updated', { when: formatRelative(updatedAt, t) })}</span>}
      </div>

      {showReload ? (
        <button
          className={`icon-button reload-button${loading ? ' spinning' : ''}`}
          type="button"
          aria-label={t('header.refresh')}
          title={t('header.refresh')}
          onClick={onReload}
          disabled={loading}
        >
          <span className="reload-glyph" aria-hidden="true">↻</span>
        </button>
      ) : (
        <span aria-hidden="true" />
      )}
    </header>
  )
}

export default Header
