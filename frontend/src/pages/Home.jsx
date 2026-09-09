import { useEffect, useState } from 'react'
import Header from '../components/Header'
import WeatherPostcard from '../components/WeatherPostcard'
import RecommendationCard from '../components/RecommendationCard'
import HourlyForecast from '../components/HourlyForecast'
import WeatherGPTCard from '../components/WeatherGPTCard'
import FloatingChatButton from '../components/FloatingChatButton'
import { fetchHomeView } from '../api/home'
import { getSavedLocation, saveLocation } from '../lib/savedLocation'
import { useI18n } from '../i18n'

const openChat = () => { window.location.hash = 'chat' }

function Home() {
  const { t } = useI18n()
  const [location, setLocation] = useState(() => getSavedLocation())
  const [input, setInput] = useState(location ?? '')
  const [status, setStatus] = useState('idle') // idle | loading | success | error
  const [data, setData] = useState(null)
  const [updatedAt, setUpdatedAt] = useState(null) // when real weather last loaded
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    if (!location) return undefined

    // `active` guards against a slower earlier request resolving after a newer
    // one (fast re-submits, or React StrictMode's dev double-invoke).
    let active = true
    setStatus('loading')
    fetchHomeView(location)
      .then((view) => {
        if (!active) return
        setData(view)
        setStatus('success')
        // Only remember a location we could resolve, and only stamp "updated"
        // when we actually got real weather (not a gap).
        if (view.data_tier !== 'unresolved_location') {
          saveLocation(location)
          setUpdatedAt(Date.now())
        } else {
          setUpdatedAt(null)
        }
      })
      .catch(() => {
        if (active) setStatus('error')
      })

    return () => {
      active = false
    }
  }, [location, reloadKey])

  const submitLocation = (event) => {
    event.preventDefault()
    const name = input.trim()
    if (!name) return
    if (name === location) {
      setReloadKey((key) => key + 1) // same name — force a refetch
    } else {
      setLocation(name)
    }
  }

  const retry = () => setReloadKey((key) => key + 1)

  const notFound = status === 'success' && data?.data_tier === 'unresolved_location'

  return (
    <main className="app-shell">
      <div className="home-page">
        <Header
          location={location}
          updatedAt={updatedAt}
          loading={status === 'loading'}
          onReload={retry}
        />

        <form className="location-bar" onSubmit={submitLocation}>
          <input
            className="location-input"
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={t('home.locationPlaceholder')}
            aria-label={t('home.locationLabel')}
          />
          <button className="location-go" type="submit">{t('home.go')}</button>
        </form>

        <section className="home-content">
          {!location && (
            <p className="home-hint">{t('home.firstRun')}</p>
          )}

          {location && status === 'loading' && (
            <p className="home-status" role="status">{t('home.loading', { location })}</p>
          )}

          {location && status === 'error' && (
            <div className="home-error" role="alert">
              <p>{t('home.errorTitle')}</p>
              <button type="button" className="location-go" onClick={retry}>
                {t('home.retry')}
              </button>
            </div>
          )}

          {notFound && (
            <div className="home-error" role="alert">
              <p>{t('home.notFound', { location })}</p>
            </div>
          )}

          {status === 'success' && !notFound && data && (
            <>
              <WeatherPostcard weather={data.current} />
              <RecommendationCard recommendation={data.recommendation} />
              {data.hourly?.length > 0 && <HourlyForecast forecast={data.hourly} />}
            </>
          )}

          <WeatherGPTCard onOpenChat={openChat} />
        </section>
      </div>

      <FloatingChatButton />
    </main>
  )
}

export default Home
