// Device-scoped user preferences (localStorage) — the same honest scope as
// savedLocation.js: no accounts yet, so preferences live per device and migrate
// to a user profile when accounts exist (architecture doc §8.2). Every access is
// guarded because localStorage can throw in private mode / when site data is
// blocked, and must never crash the app.
//
// `weathergpt.location` (the active/last-shown location) stays in savedLocation.js;
// this module adds the *default* location (what Home loads on open), a curated
// list of *saved* places, and Farmer Mode preferences.
const KEYS = {
  defaultLocation: 'weathergpt.defaultLocation',
  savedLocations: 'weathergpt.savedLocations',
  farmerCrop: 'weathergpt.farmer.crop',
  farmerLocation: 'weathergpt.farmer.location',
  farmerSowingDate: 'weathergpt.farmer.sowingDate',
  persona: 'weathergpt.persona',
}

function read(key) {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function write(key, value) {
  try {
    localStorage.setItem(key, value)
  } catch {
    // Persisting a preference is a convenience, not a requirement.
  }
}

function remove(key) {
  try {
    localStorage.removeItem(key)
  } catch {
    // ignore
  }
}

export function getDefaultLocation() {
  return read(KEYS.defaultLocation) || null
}

export function setDefaultLocation(name) {
  const value = (name || '').trim()
  if (value) write(KEYS.defaultLocation, value)
  else remove(KEYS.defaultLocation)
}

export function getSavedLocations() {
  try {
    const raw = localStorage.getItem(KEYS.savedLocations)
    const list = raw ? JSON.parse(raw) : []
    return Array.isArray(list) ? list.filter((item) => typeof item === 'string' && item.trim()) : []
  } catch {
    return []
  }
}

export function addSavedLocation(name) {
  const value = (name || '').trim()
  const list = getSavedLocations()
  // Case-insensitive de-dupe, keeping the first spelling the user entered.
  if (value && !list.some((item) => item.toLowerCase() === value.toLowerCase())) {
    list.push(value)
    write(KEYS.savedLocations, JSON.stringify(list))
  }
  return list
}

export function removeSavedLocation(name) {
  const target = (name || '').toLowerCase()
  const list = getSavedLocations().filter((item) => item.toLowerCase() !== target)
  write(KEYS.savedLocations, JSON.stringify(list))
  return list
}

export function getFarmerPrefs() {
  return {
    crop: read(KEYS.farmerCrop) || '',
    location: read(KEYS.farmerLocation) || '',
    sowingDate: read(KEYS.farmerSowingDate) || '',
  }
}

// Whole days since the sowing date (ISO "YYYY-MM-DD"), or null when it's unset,
// invalid, or in the future. Used to derive the crop's growth stage in Crop Watch.
export function daysAfterSowing(sowingDate = read(KEYS.farmerSowingDate)) {
  if (!sowingDate) return null
  const sown = new Date(sowingDate)
  if (Number.isNaN(sown.getTime())) return null
  const days = Math.floor((Date.now() - sown.getTime()) / 86400000)
  return days >= 0 ? days : null
}

// The active product persona. Farmer Mode is a separate persona (not a nav tab);
// it persists so a farmer reopens the app straight into Farmer Mode. Default is
// the normal user; 'farmer' is the only value we store.
export function getPersona() {
  return read(KEYS.persona) === 'farmer' ? 'farmer' : 'normal'
}

export function setPersona(persona) {
  if (persona === 'farmer') write(KEYS.persona, 'farmer')
  else remove(KEYS.persona)
}

export function setFarmerPrefs({ crop, location, sowingDate }) {
  if (crop !== undefined) {
    const value = (crop || '').trim()
    if (value) write(KEYS.farmerCrop, value)
    else remove(KEYS.farmerCrop)
  }
  if (location !== undefined) {
    const value = (location || '').trim()
    if (value) write(KEYS.farmerLocation, value)
    else remove(KEYS.farmerLocation)
  }
  if (sowingDate !== undefined) {
    const value = (sowingDate || '').trim()
    if (value) write(KEYS.farmerSowingDate, value)
    else remove(KEYS.farmerSowingDate)
  }
}
