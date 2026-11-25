import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getCategories, listComplaints } from '../complaintsApi.js'
import { PRIVACY_MODES } from '../labels.js'
import { formatDate } from '../format.js'
import StatusBadge from '../components/StatusBadge.jsx'

function privacyLabel(value) {
  const p = PRIVACY_MODES.find((m) => m.value === value)
  return p ? p.label : value
}

export default function ReviewQueue() {
  const [rows, setRows] = useState(null)
  const [categories, setCategories] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    Promise.all([listComplaints(), getCategories()])
      .then(([list, cats]) => {
        if (!alive) return
        setRows([...list].sort((a, b) => (a.created_at < b.created_at ? 1 : -1)))
        setCategories(cats)
      })
      .catch((e) => { if (alive) setError(e.message) })
    return () => { alive = false }
  }, [])

  const catName = (id) => (categories.find((c) => c.id === id) || {}).name || 'Unknown'

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-slate-800">Review queue</h1>
      <p className="text-sm text-slate-600">
        All complaints, newest first. This screen shows case content only, no names. Complaint text is shown as the
        employee wrote it. Identity is role-gated and audited.
      </p>
      {error && <p className="text-sm text-red-700">{error}</p>}
      {rows === null && !error && <p className="text-sm text-slate-600">Loading...</p>}
      {rows && rows.length === 0 && <p className="text-sm text-slate-600">No complaints yet.</p>}
      {rows && rows.length > 0 && (
        <div className="overflow-x-auto rounded-xl bg-white shadow">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Privacy mode</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Filed</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {rows.map((c) => (
                <tr key={c.id}>
                  <td className="px-4 py-3">
                    <Link to={'/review/' + c.id} className="font-medium text-indigo-700 hover:underline">
                      {c.title}
                    </Link>
                    {c.pseudonym && <div className="text-xs text-slate-500">Alias: {c.pseudonym}</div>}
                  </td>
                  <td className="px-4 py-3 text-slate-700">{catName(c.category_id)}</td>
                  <td className="px-4 py-3 text-slate-700">{privacyLabel(c.privacy_mode)}</td>
                  <td className="px-4 py-3"><StatusBadge status={c.status} /></td>
                  <td className="px-4 py-3 text-slate-700">{formatDate(c.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}