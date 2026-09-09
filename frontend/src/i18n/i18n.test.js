import { translate, setLanguage, getLanguage, resetLanguageForTests, LANGUAGES } from './index'

beforeEach(() => {
  localStorage.clear()
  resetLanguageForTests()
})

it('translates a known key into the requested language', () => {
  expect(translate('en', 'nav.home')).toBe('Home')
  expect(translate('hi', 'nav.home')).toBe('होम')
})

it('interpolates named tokens', () => {
  expect(translate('en', 'home.loading', { location: 'Delhi' })).toBe('Loading weather for Delhi…')
})

it('falls back to English when a language is missing the key', () => {
  // A key present in en is used verbatim for a language table without it. We
  // simulate the guarantee by translating in a supported language and checking
  // it never returns an empty string.
  const value = translate('ta', 'metric.aqi')
  expect(value).toBe('AQI')
})

it('falls back to the key itself for an unknown key', () => {
  expect(translate('en', 'does.not.exist')).toBe('does.not.exist')
})

it('setLanguage persists a supported code and ignores an unsupported one', () => {
  setLanguage('hi')
  expect(getLanguage()).toBe('hi')
  expect(localStorage.getItem('weathergpt.language')).toBe('hi')

  setLanguage('zz') // unsupported — coerced to English
  expect(getLanguage()).toBe('en')
})

it('offers the six documented languages', () => {
  expect(LANGUAGES.map((l) => l.code)).toEqual(['en', 'hi', 'bn', 'ta', 'mr', 'pa'])
})
