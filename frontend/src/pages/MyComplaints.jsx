import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getCategories, listComplaints } from '../complaintsApi'
import StatusBadge from '../components/StatusBadge.jsx'
import { PRIVACY_MODES } from '../labels.js'
import { formatDate } from '../format.js'

export default function MyComplaints() {
  const [items, setItems] = useState(null)
  const [cats, setCats] = useState({})
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([listComplaints(), getCategories()])
      .then(([complaints, categories]) => {
        setCats(Object.fromEntries(categories.map((c) => [c.id, c.name])))
        setItems(complaints)
      })
      .catch((e) => setError(e.message))
  }, [])

  const modeLabel = (v) => (PRIVACY_MODES.find((m) => m.value === v) || {}).label || v

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-800">My complaints</h1>
        <Link to="/complaints/new" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700">
          File a complaint
        </Link>
      </div>

      {error && <p className="text-sm text-red-700">{error}</p>}
      {items === null && !error && <p className="text-sm text-slate-600">Loading...</p>}
      {items && items.length === 0 && (
        <p className="rounded-xl bg-white p-6 text-sm text-slate-600 shadow">You have not filed any complaints yet.</p>
      )}

      {items && items.length > 0 && (
        <ul className="space-y-3">
          {items.map((c) => (
            <li key={c.id}>
              <Link to={'/complaints/' + c.id} className="block rounded-xl bg-white p-4 shadow hover:bg-slate-50">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="flex-1 font-medium text-slate-800">{c.title}</span>
                  <StatusBadge status={c.status} />
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  {cats[c.category_id] || 'Category ' + c.category_id} - {modeLabel(c.privacy_mode)} - filed {formatDate(c.created_at)}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}