const KEY = 'welllog-session'

function emitChange() {
  window.dispatchEvent(new Event('welllog-session-change'))
}

export function getSession() {
  const raw = localStorage.getItem(KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    localStorage.removeItem(KEY)
    return null
  }
}

export function setSession(user) {
  localStorage.setItem(KEY, JSON.stringify(user))
  emitChange()
}

export function clearSession() {
  localStorage.removeItem(KEY)
  emitChange()
}

export function isAuthenticated() {
  return Boolean(getSession()?.id)
}
