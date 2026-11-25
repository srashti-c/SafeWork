import { useState } from 'react'
import { changeStatus } from '../staffApi.js'
import { STATUS_LABELS } from '../labels.js'

// Allowed steps (same as the server rules). The SERVER is the real check.
const NEXT_STEPS = {
  submitted: ['under_review'],
  under_review: ['escalated_to_ic', 'closed'],
  escalated_to_ic: ['closed'],
  closed: [],
}

export default function StatusChanger({ complaintId, status, onChanged }) {
  const steps = NEXT_STEPS[status] || []
  const [target, setTarget] = useState('')
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState('')

  async function onSubmit(e) {
    e.preventDefault()
    if (!target) return
    setError('')
    setDone('')
    setBusy(true)
    try {
      const updated = await changeStatus(complaintId, target, note)
      setDone('Status changed to ' + (STATUS_LABELS[updated.status] || updated.status) + '.')
      setTarget('')
      setNote('')
      onChanged(updated)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="space-y-3 rounded-xl bg-white p-6 shadow">
      <h2 className="text-lg font-semibold text-slate-800">Change status</h2>
      {steps.length === 0 ? (
        <p className="text-sm text-slate-600">This complaint is closed. Closed is final.</p>
      ) : (
        <form onSubmit={onSubmit} className="space-y-3">
          <label className="block text-sm text-slate-700">
            Next step
            <select
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-300 p-2 text-sm"
            >
              <option value="">Choose a step...</option>
              {steps.map((s) => (
                <option key={s} value={s}>{STATUS_LABELS[s] || s}</option>
              ))}
            </select>
          </label>
          <label className="block text-sm text-slate-700">
            Note (optional, up to 500 characters)
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              maxLength={500}
              rows={3}
              className="mt-1 block w-full rounded-lg border border-slate-300 p-2 text-sm"
            />
          </label>
          <button
            type="submit"
            disabled={!target || busy}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {busy ? 'Saving...' : 'Save status change'}
          </button>
        </form>
      )}
      {error && <p className="text-sm text-red-700">The server refused this: {error}</p>}
      {done && <p className="text-sm text-green-700">{done}</p>}
      <p className="text-xs text-slate-500">
        Only these steps are allowed. Every change is checked by the server and added to the history.
      </p>
    </section>
  )
}