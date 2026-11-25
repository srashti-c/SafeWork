import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createComplaint, getCategories } from '../complaintsApi'
import { PRIVACY_MODES, PRIVACY_NOTE } from '../labels.js'

export default function NewComplaint() {
  const navigate = useNavigate()
  const [categories, setCategories] = useState([])
  const [mode, setMode] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [incidentDate, setIncidentDate] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    getCategories().then(setCategories).catch((e) => setError(e.message))
  }, [])

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const created = await createComplaint({
        category_id: Number(categoryId),
        privacy_mode: mode,
        title: title.trim(),
        description: description.trim(),
        incident_date: incidentDate || null,
      })
      navigate('/complaints/' + created.id) // evidence can be added on the next page
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  const today = new Date().toISOString().slice(0, 10)

  return (
    <form onSubmit={onSubmit} className="space-y-6 rounded-xl bg-white p-6 shadow">
      <h1 className="text-xl font-semibold text-slate-800">File a complaint</h1>

      <fieldset className="space-y-2">
        <legend className="text-sm font-medium text-slate-700">How should your identity be handled?</legend>
        {PRIVACY_MODES.map((m) => (
          <label
            key={m.value}
            className={'block cursor-pointer rounded-lg border p-3 text-sm ' + (mode === m.value ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300')}
          >
            <input
              type="radio"
              name="privacy_mode"
              value={m.value}
              required
              checked={mode === m.value}
              onChange={() => setMode(m.value)}
              className="mr-2"
            />
            <span className="font-medium text-slate-800">{m.label}</span>
            <span className="mt-1 block text-slate-600">{m.help}</span>
          </label>
        ))}
        <p className="text-xs text-slate-500">{PRIVACY_NOTE}</p>
      </fieldset>

      <label className="block text-sm text-slate-700">
        Category
        <select
          required
          value={categoryId}
          onChange={(e) => setCategoryId(e.target.value)}
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
        >
          <option value="">Choose a category</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </label>

      <label className="block text-sm text-slate-700">
        Title (5 to 200 characters)
        <input
          type="text"
          required
          minLength={5}
          maxLength={200}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
        />
      </label>

      <label className="block text-sm text-slate-700">
        What happened? (10 to 5000 characters)
        <textarea
          required
          minLength={10}
          maxLength={5000}
          rows={8}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
        />
      </label>

      <label className="block text-sm text-slate-700">
        Date of the incident (optional)
        <input
          type="date"
          max={today}
          value={incidentDate}
          onChange={(e) => setIncidentDate(e.target.value)}
          className="mt-1 rounded-lg border border-slate-300 px-3 py-2"
        />
      </label>

      {error && <p className="text-sm text-red-700">{error}</p>}
      <p className="text-xs text-slate-500">You can add evidence files after the complaint is filed.</p>

      <button
        type="submit"
        disabled={busy}
        className="rounded-lg bg-indigo-600 px-5 py-2 text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        {busy ? 'Filing...' : 'File complaint'}
      </button>
    </form>
  )
}