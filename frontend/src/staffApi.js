import { apiFetch } from './api.js'

// Staff-only calls. The server checks the role on every request.
export const getHistory = (id) => apiFetch('/complaints/' + id + '/history')

export const changeStatus = (id, newStatus, note) =>
  apiFetch('/complaints/' + id + '/status', {
    method: 'PATCH',
    json: { new_status: newStatus, note: note && note.trim() ? note.trim() : null },
  })