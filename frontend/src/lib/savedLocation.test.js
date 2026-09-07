import { getSavedLocation, saveLocation } from './savedLocation'

beforeEach(() => {
  localStorage.clear()
})

it('returns null when nothing is saved', () => {
  expect(getSavedLocation()).toBeNull()
})

it('round-trips a saved location', () => {
  saveLocation('Jaipur')
  expect(getSavedLocation()).toBe('Jaipur')
})
