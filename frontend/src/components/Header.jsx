import { useEffect, useState } from 'react'
import { useI18n } from '../i18n'

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

  // Re-render every 30s so the relative "updated" label stays truthful.
  useEffect(() => {
    if (!updatedAt) return undefined
    const id = setInterval(() => setTick((tk) => tk + 1), 30000)
    return () => clearInterval(id)
  }, [updatedAt])

  const showReload = Boolean(updatedAt) || loading

  return (
    <header className="header">
      <button className="icon-button" type="button" aria-label={t('header.menu')} title={t('header.menu')} onClick={() => { window.location.hash = 'settings' }}>
        <span className="hamburger-line" />
        <span className="hamburger-line" />
        <span className="hamburger-line" />
      </button>

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
