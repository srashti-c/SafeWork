import { useState } from 'react'
import { Link } from 'react-router-dom'
import { calculateRisk, suggestCategory } from '../analysisApi.js'

const FREQUENCY = [
  { value: 'unknown', label: 'Not known' },
  { value: 'once', label: 'Happened once' },
  { value: 'a_few', label: 'A few times' },
  { value: 'repeated', label: 'Repeated / ongoing' },
]
const POWER = [
  { value: 'unknown', label: 'Not known' },
  { value: 'none', label: 'No power difference' },
  { value: 'senior', label: 'Someone more senior' },
  { value: 'direct_manager', label: 'Direct manager' },
]
const LEVEL_STYLE = {
  LOW: 'border-green-300 bg-green-50 text-green-800',
  MEDIUM: 'border-amber-300 bg-amber-50 text-amber-800',
  HIGH: 'border-orange-300 bg-orange-50 text-orange-800',
  CRITICAL: 'border-red-300 bg-red-50 text-red-800',
}

function Notice({ text }) {
  if (!text) return null
  return <p className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">{text}</p>
}

function Choice({ label, value, onChange, options }) {
  return (
    <label className="block text-sm text-slate-700">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 block w-full rounded-lg border border-slate-300 bg-white p-2 text-sm"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </label>
  )
}

export default function AnalysisPanel({ complaintId }) {
  const [sug, setSug] = useState(null)
  const [sugError, setSugError] = useState('')
  const [sugBusy, setSugBusy] = useState(false)
  const [frequency, setFrequency] = useState('unknown')
  const [power, setPower] = useState('unknown')
  const [rep, setRep] = useState(null)
  const [repError, setRepError] = useState('')
  const [repBusy, setRepBusy] = useState(false)

  async function onSuggest() {
    setSugError('')
    setSugBusy(true)
    try {
      setSug(await suggestCategory(complaintId))
    } catch (err) {
      setSugError(err.message)
    } finally {
      setSugBusy(false)
    }
  }

  async function onRisk(e) {
    e.preventDefault()
    setRepError('')
    setRepBusy(true)
    try {
      setRep(await calculateRisk(complaintId, frequency, power))
    } catch (err) {
      setRepError(err.message)
    } finally {
      setRepBusy(false)
    }
  }

  const risk = rep ? rep.risk : null
  const notices = rep
    ? [...new Set([
        risk && risk.notice,
        rep.notice,
        rep.pattern && rep.pattern.notice,
        rep.retaliation && rep.retaliation.notice,
      ].filter(Boolean))]
    : []

  return (
    <section className="space-y-6 rounded-xl bg-white p-6 shadow">
      <div>
        <h2 className="text-lg font-semibold text-slate-800">Decision support</h2>
        <p className="text-sm text-slate-600">
          For human review only. Nothing here decides what happened or who is at fault, and nothing here changes the complaint.
        </p>
      </div>

      <div className="space-y-3">
        <h3 className="font-medium text-slate-800">1. Suggested categories (language model)</h3>
        <button
          onClick={onSuggest}
          disabled={sugBusy}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {sugBusy ? 'Working... (the first call can be slow)' : 'Suggest categories'}
        </button>
        {sugError && <p className="text-sm text-red-700">{sugError}</p>}
        {sug && (
          <div className="space-y-3">
            {sug.suggestions.length === 0 && <p className="text-sm text-slate-600">{sug.message || 'No suggestions.'}</p>}
            <ol className="space-y-2">
              {sug.suggestions.map((s) => (
                <li key={s.rank} className="space-y-1">
                  <div className="flex items-center justify-between text-sm text-slate-800">
                    <span>Suggestion {s.rank}: <span className="font-medium">{s.category}</span></span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100">
                    <div className="h-2 rounded-full bg-indigo-400" style={{ width: Math.round(Math.max(0, Math.min(1, s.score)) * 100) + '%' }} />
                  </div>
                </li>
              ))}
            </ol>
            <p className="text-xs text-slate-600">
              The bar shows the model's relative score, not certainty. On our small synthetic test the first suggestion was wrong
              about 1 time in 4, so always read the complaint yourself.
            </p>
            <Notice text={sug.notice} />
          </div>
        )}
      </div>

      <div className="space-y-3 border-t border-slate-200 pt-6">
        <h3 className="font-medium text-slate-800">2. Priority for triage (explained)</h3>
        <form onSubmit={onRisk} className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <Choice label="How often did it happen?" value={frequency} onChange={setFrequency} options={FREQUENCY} />
            <Choice label="Power difference with the person complained about" value={power} onChange={setPower} options={POWER} />
          </div>
          <p className="text-xs text-slate-600">
            You enter these two answers. "Not known" gives 0 points, so missing information lowers the priority.
          </p>
          <button
            type="submit"
            disabled={repBusy}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {repBusy ? 'Working... (the first call can be slow)' : 'Calculate priority'}
          </button>
        </form>
        {repError && <p className="text-sm text-red-700">{repError}</p>}

        {risk && (
          <div className="space-y-4">
            <div className={'rounded-xl border p-4 ' + (LEVEL_STYLE[String(risk.level).toUpperCase()] || 'border-slate-300 bg-slate-50 text-slate-800')}>
              <p className="text-xs uppercase tracking-wide">Priority level</p>
              <p className="text-2xl font-semibold">{risk.level}</p>
              <p className="text-xs">Points: {risk.score} of {risk.max_score}. This is a priority, not a probability.</p>
            </div>

            <ul className="divide-y divide-slate-200">
              {risk.reasons.map((x) => (
                <li key={x.factor} className="space-y-1 py-2">
                  <div className="flex items-center justify-between text-sm text-slate-800">
                    <span className="font-medium capitalize">{String(x.factor).replace(/_/g, ' ')}</span>
                    <span>{x.points} / {x.max_points}</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-slate-100">
                    <div
                      className="h-1.5 rounded-full bg-slate-500"
                      style={{ width: (x.max_points > 0 ? Math.min(100, (x.points / x.max_points) * 100) : 0) + '%' }}
                    />
                  </div>
                  <p className="text-sm text-slate-700">{x.reason}</p>
                </li>
              ))}
            </ul>

            {rep.pattern && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-slate-800">Similar earlier or later wording</h4>
                <p className="text-sm text-slate-700">{rep.pattern.message}</p>
                {rep.pattern.matches.length > 0 && (
                  <ul className="space-y-1 text-sm text-slate-700">
                    {rep.pattern.matches.map((m) => (
                      <li key={m.case_id}>
                        <Link to={'/review/' + m.case_id} className="text-indigo-700 hover:underline">Case {String(m.case_id).slice(0, 8)}</Link>
                        {' '}- {m.category}, filed {m.filed_on}, similarity {m.similarity}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {rep.retaliation && (
              <div className="space-y-1">
                <h4 className="text-sm font-medium text-slate-800">Retaliation timing check</h4>
                <p className="text-sm text-slate-700">{rep.retaliation.message}</p>
              </div>
            )}

            {notices.map((n) => <Notice key={n} text={n} />)}
          </div>
        )}
      </div>
    </section>
  )
}