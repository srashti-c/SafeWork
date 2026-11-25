import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getCategories, getComplaint } from '../complaintsApi'
import EvidencePanel from '../components/EvidencePanel.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { PRIVACY_MODES } from '../labels.js'
import { formatDate, formatDateTime } from '../format.js'

export default function ComplaintDetail() {
  const { id } = useParams()
  const [c, setC] = useState(null)
  const [catName, setCatName] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getComplaint(id), getCategories()])
      .then(([item, cats]) => {
        setC(item)
        const found = cats.find((x) => x.id === item.category_id)
        setCatName(found ? found.name : '')
      })
      .catch((e) => setError(e.message))
  }, [id])

  if (error) {
    return (
      <div className="space-y-3 rounded-xl bg-white p-6 shadow">
        <p className="text-sm text-red-700">{error}</p>
        <Link to="/complaints" className="text-sm text-indigo-700 underline">Back to my complaints</Link>
      </div>
    )
  }
  if (!c) return <p className="text-sm text-slate-600">Loading...</p>

  const mode = PRIVACY_MODES.find((m) => m.value === c.privacy_mode)

  return (
    <div className="space-y-6">
      <Link to="/complaints" className="text-sm text-indigo-700 underline">Back to my complaints</Link>

      <section className="rounded-xl bg-white p-6 shadow space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="flex-1 text-xl font-semibold text-slate-800">{c.title}</h1>
          <StatusBadge status={c.status} />
        </div>
        <dl className="grid grid-cols-1 gap-x-6 gap-y-1 text-sm text-slate-700 sm:grid-cols-2">
          <div><dt className="inline text-slate-500">Category: </dt><dd className="inline">{catName}</dd></div>
          <div><dt className="inline text-slate-500">Identity handling: </dt><dd className="inline">{mode ? mode.label : c.privacy_mode}</dd></div>
          {c.pseudonym && (
            <div><dt className="inline text-slate-500">Alias: </dt><dd className="inline">{c.pseudonym}</dd></div>
          )}
          {c.incident_date && (
            <div><dt className="inline text-slate-500">Incident date: </dt><dd className="inline">{formatDate(c.incident_date)}</dd></div>
          )}
          <div><dt className="inline text-slate-500">Filed: </dt><dd className="inline">{formatDateTime(c.created_at)}</dd></div>
          <div><dt className="inline text-slate-500">Last update: </dt><dd className="inline">{formatDateTime(c.updated_at)}</dd></div>
        </dl>
        <p className="whitespace-pre-wrap border-t border-slate-200 pt-3 text-sm text-slate-800">{c.description}</p>
      </section>

      <EvidencePanel complaintId={c.id} />
    </div>
  )
}