import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getCategories, getComplaint } from '../complaintsApi.js'
import { getHistory } from '../staffApi.js'
import { PRIVACY_MODES } from '../labels.js'
import { formatDate, formatDateTime } from '../format.js'
import StatusBadge from '../components/StatusBadge.jsx'
import StatusChanger from '../components/StatusChanger.jsx'
import HistoryList from '../components/HistoryList.jsx'
import AnalysisPanel from '../components/AnalysisPanel.jsx'
import EvidencePanel from '../components/EvidencePanel.jsx'

export default function StaffComplaintDetail() {
  const { id } = useParams()
  const [c, setC] = useState(null)
  const [categories, setCategories] = useState([])
  const [history, setHistory] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    Promise.all([getComplaint(id), getCategories(), getHistory(id)])
      .then(([cc, cats, h]) => {
        if (!alive) return
        setC(cc)
        setCategories(cats)
        setHistory(h)
      })
      .catch((e) => { if (alive) setError(e.message) })
    return () => { alive = false }
  }, [id])

  function onChanged(updated) {
    setC(updated)
    getHistory(id).then(setHistory).catch((e) => setError(e.message))
  }

  if (error && !c) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-red-700">{error}</p>
        <Link to="/review" className="text-sm text-indigo-700 hover:underline">Back to the review queue</Link>
      </div>
    )
  }
  if (!c) return <p className="text-sm text-slate-600">Loading...</p>

  const cat = (categories.find((x) => x.id === c.category_id) || {}).name || 'Unknown'
  const mode = (PRIVACY_MODES.find((m) => m.value === c.privacy_mode) || {}).label || c.privacy_mode

  return (
    <div className="space-y-6">
      <Link to="/review" className="text-sm text-indigo-700 hover:underline">Back to the review queue</Link>

      <section className="space-y-3 rounded-xl bg-white p-6 shadow">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="flex-1 text-xl font-semibold text-slate-800">{c.title}</h1>
          <StatusBadge status={c.status} />
        </div>
        <dl className="grid gap-2 text-sm text-slate-700 sm:grid-cols-2">
          <div>Category: {cat}</div>
          <div>Privacy mode: {mode}</div>
          {c.pseudonym && <div>Alias: {c.pseudonym}</div>}
          {c.incident_date && <div>Incident date: {formatDate(c.incident_date)}</div>}
          <div>Filed: {formatDateTime(c.created_at)}</div>
          <div>Updated: {formatDateTime(c.updated_at)}</div>
        </dl>
        <p className="whitespace-pre-wrap text-sm text-slate-800">{c.description}</p>
        <p className="text-xs text-slate-500">
          This screen does not show who filed. Identity is role-gated and audited. It is protected, not anonymous.
        </p>
      </section>

      {error && <p className="text-sm text-red-700">{error}</p>}

      <StatusChanger complaintId={c.id} status={c.status} onChanged={onChanged} />

      <AnalysisPanel key={c.id} complaintId={c.id} />

      <EvidencePanel key={'ev-' + c.id} complaintId={c.id} />

      <section className="space-y-3 rounded-xl bg-white p-6 shadow">
        <h2 className="text-lg font-semibold text-slate-800">History</h2>
        <HistoryList items={history} />
      </section>
    </div>
  )
}