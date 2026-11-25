import { apiFetch } from './api.js'

// Staff-only analysis calls. The server checks the role on every request.
export const suggestCategory = (id) =>
  apiFetch('/analysis/complaints/' + id + '/suggest-category', { method: 'POST' })

export const calculateRisk = (id, frequency, powerImbalance) =>
  apiFetch('/analysis/complaints/' + id + '/risk', {
    method: 'POST',
    json: { frequency, power_imbalance: powerImbalance },
  })