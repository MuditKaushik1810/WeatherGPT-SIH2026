import { useState } from 'react'
import { useI18n, LANGUAGES } from '../i18n'
import { saveLocation } from '../lib/savedLocation'
import {
  getDefaultLocation, setDefaultLocation,
  getSavedLocations, addSavedLocation, removeSavedLocation,
  getFarmerPrefs, setFarmerPrefs,
} from '../lib/preferences'

// User Settings — the home for device-scoped preferences: app language, the
// default/saved locations, and Farmer Mode preferences. Reached from the header
// menu (a focused screen with its own back control, like Chat — not a nav tab).
// All values persist via ../lib/preferences (localStorage); language lives in the
// i18n store. Everything here migrates to a user profile when accounts exist.
function Settings() {
  const { t, lang, setLang } = useI18n()

  const [defaultLoc, setDefaultLoc] = useState(() => getDefaultLocation() || '')
  const [saved, setSaved] = useState(() => getSavedLocations())
  const [addField, setAddField] = useState('')
  const initialFarmer = getFarmerPrefs()
  const [crop, setCrop] = useState(initialFarmer.crop)
  const [farmLoc, setFarmLoc] = useState(initialFarmer.location)
  const [sowDate, setSowDate] = useState(initialFarmer.sowingDate || '')
  const [flash, setFlash] = useState('') // which section just saved: 'default' | 'farmer'

  const saveDefault = (event) => {
    event.preventDefault()
    const name = defaultLoc.trim()
    setDefaultLocation(name)
    if (name) setSaved(addSavedLocation(name)) // keep the default visible in the list too
    setFlash('default')
  }

  const addPlace = (event) => {
    event.preventDefault()
    if (!addField.trim()) return
    setSaved(addSavedLocation(addField))
    setAddField('')
  }

  const showPlace = (name) => {
    saveLocation(name) // make it the active location Home reads on mount
    window.location.hash = 'home'
  }

  const saveFarmer = (event) => {
    event.preventDefault()
    setFarmerPrefs({ crop, location: farmLoc, sowingDate: sowDate })
    setFlash('farmer')
  }

  return (
    <main className="app-shell settings-shell">
      <div className="settings-page">
        <header className="settings-header">
          <button
            className="icon-button"
            type="button"
            aria-label={t('chat.back')}
            title={t('chat.backShort')}
            onClick={() => { window.location.hash = 'home' }}
          >
            ←
          </button>
          <h1 className="settings-title">{t('settings.title')}</h1>
          <span aria-hidden="true" />
        </header>

        <section className="settings-card">
          <h2>{t('settings.langHeading')}</h2>
          <p className="settings-help">{t('settings.langHelp')}</p>
          <label className="settings-field">
            <span className="settings-field-label">{t('settings.langHeading')}</span>
            <select
              className="settings-select"
              value={lang}
              onChange={(event) => setLang(event.target.value)}
              aria-label={t('settings.langHeading')}
            >
              {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
            </select>
          </label>
        </section>

        <section className="settings-card">
          <h2>{t('settings.locHeading')}</h2>

          <form className="settings-field" onSubmit={saveDefault}>
            <span className="settings-field-label">{t('settings.defaultLabel')}</span>
            <p className="settings-help">{t('settings.defaultHelp')}</p>
            <div className="settings-inline">
              <input
                className="settings-input"
                type="text"
                value={defaultLoc}
                onChange={(event) => { setDefaultLoc(event.target.value); setFlash('') }}
                placeholder={t('settings.placeholderCity')}
                aria-label={t('settings.defaultLabel')}
              />
              <button className="settings-save" type="submit">
                {flash === 'default' ? t('settings.saved') : t('settings.save')}
              </button>
            </div>
          </form>

          <div className="settings-field">
            <span className="settings-field-label">{t('settings.savedHeading')}</span>
            {saved.length === 0 ? (
              <p className="settings-help">{t('settings.noSaved')}</p>
            ) : (
              <ul className="settings-saved-list">
                {saved.map((name) => (
                  <li key={name} className="settings-saved-item">
                    <span className="settings-saved-name">{name}</span>
                    <button type="button" className="settings-chip" onClick={() => showPlace(name)}>
                      {t('settings.show')}
                    </button>
                    <button
                      type="button"
                      className="settings-chip settings-chip-danger"
                      onClick={() => setSaved(removeSavedLocation(name))}
                      aria-label={`${t('settings.remove')} ${name}`}
                    >
                      {t('settings.remove')}
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <form className="settings-inline" onSubmit={addPlace}>
              <input
                className="settings-input"
                type="text"
                value={addField}
                onChange={(event) => setAddField(event.target.value)}
                placeholder={t('settings.addPlaceholder')}
                aria-label={t('settings.addPlaceholder')}
              />
              <button className="settings-save" type="submit" disabled={!addField.trim()}>
                {t('settings.add')}
              </button>
            </form>
          </div>
        </section>

        <section className="settings-card">
          <h2>{t('settings.farmerHeading')}</h2>
          <p className="settings-help">{t('settings.farmerHelp')}</p>
          <form onSubmit={saveFarmer}>
            <label className="settings-field">
              <span className="settings-field-label">{t('settings.cropLabel')}</span>
              <input
                className="settings-input"
                type="text"
                value={crop}
                onChange={(event) => { setCrop(event.target.value); setFlash('') }}
                placeholder={t('settings.placeholderCrop')}
                aria-label={t('settings.cropLabel')}
              />
            </label>
            <label className="settings-field">
              <span className="settings-field-label">{t('settings.farmLocationLabel')}</span>
              <input
                className="settings-input"
                type="text"
                value={farmLoc}
                onChange={(event) => { setFarmLoc(event.target.value); setFlash('') }}
                placeholder={t('settings.placeholderFarm')}
                aria-label={t('settings.farmLocationLabel')}
              />
            </label>
            <label className="settings-field">
              <span className="settings-field-label">{t('settings.sowingDate')}</span>
              <input
                className="settings-input"
                type="date"
                value={sowDate}
                onChange={(event) => { setSowDate(event.target.value); setFlash('') }}
                aria-label={t('settings.sowingDate')}
              />
            </label>
            <button className="settings-save" type="submit">
              {flash === 'farmer' ? t('settings.saved') : t('settings.save')}
            </button>
          </form>
        </section>
      </div>
    </main>
  )
}

export default Settings
