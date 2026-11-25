// Calls for the employee screens. All of them go through apiFetch, so the JWT is added for us.
import { apiFetch } from './api'

export const getCategories = () => apiFetch('/categories')
export const createComplaint = (data) => apiFetch('/complaints', { method: 'POST', json: data })
export const listComplaints = () => apiFetch('/complaints')
export const getComplaint = (id) => apiFetch('/complaints/' + id)
export const listEvidence = (id) => apiFetch('/complaints/' + id + '/evidence')

export function uploadEvidence(id, file) {
  const fd = new FormData()
  fd.append('file', file) // the backend expects the field name "file"
  return apiFetch('/complaints/' + id + '/evidence', { method: 'POST', body: fd })
}

export const verifyEvidence = (id, evidenceId) =>
  apiFetch('/complaints/' + id + '/evidence/' + evidenceId + '/verify', { method: 'POST' })