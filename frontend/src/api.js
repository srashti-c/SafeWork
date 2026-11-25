const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
const TOKEN_KEY = 'safework_token'

export function getToken() {
  try { return sessionStorage.getItem(TOKEN_KEY) } catch { return null }
}
export function setToken(token) {
  try { sessionStorage.setItem(TOKEN_KEY, token) } catch { /* ignore */ }
}
export function clearToken() {
  try { sessionStorage.removeItem(TOKEN_KEY) } catch { /* ignore */ }
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function detailToText(detail) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((d) => (d && d.msg ? d.msg : JSON.stringify(d))).join('; ')
  }
  return ''
}

export async function apiFetch(path, { method = 'GET', json, form, body } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers['Authorization'] = 'Bearer ' + token
  let payload
  if (json !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(json)
  } else if (form !== undefined) {
    payload = form instanceof FormData || form instanceof URLSearchParams ? form : new URLSearchParams(form)
  } else if (body !== undefined) {
    payload = body
  }
  let res
  try {
    res = await fetch(BASE_URL + path, { method, headers, body: payload })
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Is the backend running?')
  }
  let data = null
  const text = await res.text()
  if (text) {
    try { data = JSON.parse(text) } catch { data = text }
  }
  if (!res.ok) {
    if (res.status === 401 && token) {
      clearToken()
      window.dispatchEvent(new Event('safework-unauthorized'))
    }
    const msg = (data && typeof data === 'object' ? detailToText(data.detail) : '') || 'Request failed (' + res.status + ')'
    throw new ApiError(res.status, msg)
  }
  return data
}

export async function login(email, password) {
  const data = await apiFetch('/auth/login', { method: 'POST', form: { username: email, password } })
  if (data && data.access_token) setToken(data.access_token)
  return data
}

export function register(email, full_name, password) {
  return apiFetch('/auth/register', { method: 'POST', json: { email, full_name, password } })
}

export function getMe() {
  return apiFetch('/users/me')
}