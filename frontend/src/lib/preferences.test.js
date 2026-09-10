import {
  getDefaultLocation, setDefaultLocation,
  getSavedLocations, addSavedLocation, removeSavedLocation,
  getFarmerPrefs, setFarmerPrefs, daysAfterSowing,
  getPersona, setPersona,
} from './preferences'

beforeEach(() => localStorage.clear())

it('stores and clears the default location', () => {
  expect(getDefaultLocation()).toBeNull()
  setDefaultLocation('  Delhi  ')
  expect(getDefaultLocation()).toBe('Delhi') // trimmed
  setDefaultLocation('')
  expect(getDefaultLocation()).toBeNull()
})

it('adds saved places, de-dupes case-insensitively, and removes them', () => {
  addSavedLocation('Jaipur')
  addSavedLocation('jaipur') // duplicate — ignored
  addSavedLocation('Mumbai')
  expect(getSavedLocations()).toEqual(['Jaipur', 'Mumbai'])

  removeSavedLocation('JAIPUR')
  expect(getSavedLocations()).toEqual(['Mumbai'])
})

it('tolerates a corrupt saved-locations value', () => {
  localStorage.setItem('weathergpt.savedLocations', 'not json')
  expect(getSavedLocations()).toEqual([])
})

it('stores farmer preferences independently', () => {
  expect(getFarmerPrefs()).toEqual({ crop: '', location: '', sowingDate: '' })
  setFarmerPrefs({ crop: 'Wheat' })
  expect(getFarmerPrefs()).toEqual({ crop: 'Wheat', location: '', sowingDate: '' })
  setFarmerPrefs({ location: 'Karnal' })
  expect(getFarmerPrefs()).toEqual({ crop: 'Wheat', location: 'Karnal', sowingDate: '' })
  setFarmerPrefs({ crop: '' })
  expect(getFarmerPrefs()).toEqual({ crop: '', location: 'Karnal', sowingDate: '' })
})

it('stores a sowing date and derives days-after-sowing', () => {
  setFarmerPrefs({ sowingDate: '2026-01-01' })
  expect(getFarmerPrefs().sowingDate).toBe('2026-01-01')

  const d = daysAfterSowing('2026-01-01')
  expect(typeof d).toBe('number')
  expect(d).toBeGreaterThan(0)
  expect(daysAfterSowing('')).toBeNull()          // unset
  expect(daysAfterSowing('2999-01-01')).toBeNull() // future date
})

it('defaults to the normal persona and persists the farmer persona', () => {
  expect(getPersona()).toBe('normal')
  setPersona('farmer')
  expect(getPersona()).toBe('farmer')
  setPersona('normal')
  expect(getPersona()).toBe('normal')
  expect(localStorage.getItem('weathergpt.persona')).toBeNull()
})
