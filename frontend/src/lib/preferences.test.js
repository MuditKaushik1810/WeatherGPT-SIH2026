import {
  getDefaultLocation, setDefaultLocation,
  getSavedLocations, addSavedLocation, removeSavedLocation,
  getFarmerPrefs, setFarmerPrefs,
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
  expect(getFarmerPrefs()).toEqual({ crop: '', location: '' })
  setFarmerPrefs({ crop: 'Wheat' })
  expect(getFarmerPrefs()).toEqual({ crop: 'Wheat', location: '' })
  setFarmerPrefs({ location: 'Karnal' })
  expect(getFarmerPrefs()).toEqual({ crop: 'Wheat', location: 'Karnal' })
  setFarmerPrefs({ crop: '' })
  expect(getFarmerPrefs()).toEqual({ crop: '', location: 'Karnal' })
})
