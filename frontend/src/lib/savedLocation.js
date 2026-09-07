// Remembers the user's chosen location on this device across visits.
//
// localStorage is used deliberately (not the backend) because there are no user
// accounts yet — per-device persistence is the honest scope for now. When user
// profiles exist, this migrates to DB-backed saved locations (architecture doc
// Section 8.2). Every access is guarded: localStorage can throw in private mode
// or when site data is blocked, and must never crash the app.
const KEY = 'weathergpt.location'

export function getSavedLocation() {
  try {
    return localStorage.getItem(KEY) || null
  } catch {
    return null
  }
}

export function saveLocation(name) {
  try {
    localStorage.setItem(KEY, name)
  } catch {
    // Ignore — remembering the location is a convenience, not a requirement.
  }
}
