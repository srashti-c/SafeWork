import { STATUS_LABELS } from '../labels.js'
import { formatDateTime } from '../format.js'

// Shows what happened and when. It never shows who made the change.
export default function HistoryList({ items }) {
  if (items === null) return <p className="text-sm text-slate-600">Loading history...</p>
  if (items.length === 0) return <p className="text-sm text-slate-600">No history yet.</p>
  const rows = [...items].sort((a, b) => a.id - b.id)
  return (
    <ul className="divide-y divide-slate-200">
      {rows.map((h) => (
        <li key={h.id} className="space-y-1 py-3">
          <p className="text-sm text-slate-800">
            {h.old_status ? (STATUS_LABELS[h.old_status] || h.old_status) : 'Filed'}
            {' -> '}
            <span className="font-medium">{STATUS_LABELS[h.new_status] || h.new_status}</span>
          </p>
          {h.note && <p className="text-sm text-slate-700">Note: {h.note}</p>}
          <p className="text-xs text-slate-500">{formatDateTime(h.created_at)}</p>
        </li>
      ))}
    </ul>
  )
}