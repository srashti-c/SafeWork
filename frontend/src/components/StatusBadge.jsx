import { STATUS_LABELS } from '../labels.js'

const COLORS = {
  submitted: 'bg-sky-100 text-sky-800',
  under_review: 'bg-amber-100 text-amber-800',
  escalated_to_ic: 'bg-purple-100 text-purple-800',
  closed: 'bg-slate-200 text-slate-700',
}

// The status is always written as text, so colour is never the only signal.
export default function StatusBadge({ status }) {
  return (
    <span className={'rounded-full px-2 py-0.5 text-xs font-medium ' + (COLORS[status] || 'bg-slate-100 text-slate-700')}>
      {STATUS_LABELS[status] || status}
    </span>
  )
}