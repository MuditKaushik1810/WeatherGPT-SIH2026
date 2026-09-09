// App-wide internationalization.
//
// Deliberately dependency-free and Provider-free: the current language lives in
// a small module-level store that every component reads through `useI18n()` via
// React's useSyncExternalStore. Calling `setLang(code)` updates the store and
// re-renders the whole app at once — so switching language anywhere (the Chat
// selector today, the Settings screen next) instantly re-renders every screen.
//
// Why no React Context Provider: the existing component tests render screens in
// isolation with no wrapper. A module store keeps `useI18n()` working (and
// switchable) in those tests without threading a Provider through every render,
// while production behaves identically.
//
// Language choice persists on the device (localStorage), mirroring the honest
// per-device scope of savedLocation.js — it migrates to a user profile when
// accounts exist (architecture doc §8.2).
import { useSyncExternalStore } from 'react'
import { CATALOG } from './catalog'

// The languages offered in the UI. `label` is the native name (shown in the
// selector); `bcp47` drives browser voice output (speechSynthesis) and <html lang>.
export const LANGUAGES = [
  { code: 'en', label: 'English', bcp47: 'en-IN' },
  { code: 'hi', label: 'हिन्दी', bcp47: 'hi-IN' },
  { code: 'bn', label: 'বাংলা', bcp47: 'bn-IN' },
  { code: 'ta', label: 'தமிழ்', bcp47: 'ta-IN' },
  { code: 'mr', label: 'मराठी', bcp47: 'mr-IN' },
  { code: 'pa', label: 'ਪੰਜਾਬੀ', bcp47: 'pa-IN' },
]

const STORAGE_KEY = 'weathergpt.language'
const SUPPORTED = new Set(LANGUAGES.map((l) => l.code))

function readInitial() {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    if (value && SUPPORTED.has(value)) return value
  } catch {
    // localStorage can throw in private mode / when site data is blocked — the
    // app must still render, so fall through to the English default.
  }
  return 'en'
}

let currentLang = readInitial()
const listeners = new Set()

function emit() {
  listeners.forEach((listener) => listener())
}

function subscribe(listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

function getSnapshot() {
  return currentLang
}

// Keep <html lang> truthful for screen readers / the browser. Guarded for the
// (non-DOM) server snapshot path and any environment without `document`.
function syncDocumentLang(code) {
  try {
    if (typeof document !== 'undefined' && document.documentElement) {
      document.documentElement.lang = code
    }
  } catch {
    // ignore
  }
}

syncDocumentLang(currentLang)

export function setLanguage(code) {
  const next = SUPPORTED.has(code) ? code : 'en'
  if (next === currentLang) return
  currentLang = next
  try {
    localStorage.setItem(STORAGE_KEY, next)
  } catch {
    // Remembering the choice is a convenience, not a requirement.
  }
  syncDocumentLang(next)
  emit()
}

export function getLanguage() {
  return currentLang
}

// Test helper: reset to English in-memory (the module store outlives a single
// test), without persisting. Call from a test's beforeEach after localStorage.clear().
export function resetLanguageForTests() {
  currentLang = 'en'
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
  syncDocumentLang('en')
  emit()
}

function interpolate(template, vars) {
  if (!vars) return template
  return template.replace(/\{(\w+)\}/g, (match, key) => (key in vars ? String(vars[key]) : match))
}

// Resolve a key for a language, falling back to English, then to the key itself
// (so a missing string is never a blank — it degrades to a visible English value).
export function translate(lang, key, vars) {
  const table = CATALOG[lang] || CATALOG.en
  let value
  if (key in table) value = table[key]
  else if (key in CATALOG.en) value = CATALOG.en[key]
  else value = key
  return interpolate(value, vars)
}

// The hook every component uses. `lang` is reactive (app-wide re-render on
// change); `t(key, vars)` translates into the current language.
export function useI18n() {
  const lang = useSyncExternalStore(subscribe, getSnapshot, getSnapshot)
  const t = (key, vars) => translate(lang, key, vars)
  return { lang, setLang: setLanguage, t, languages: LANGUAGES }
}
