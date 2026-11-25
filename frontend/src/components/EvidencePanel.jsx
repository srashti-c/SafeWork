import { useCallback, useEffect, useState } from 'react'
import { listEvidence, uploadEvidence, verifyEvidence } from '../complaintsApi'
import { formatDateTime, formatSize } from '../format.js'

const MAX_BYTES = 10 * 1024 * 1024
const DEFAULT_NOTICE =
  'Integrity check only: it shows whether a file changed after upload. It is not legal admissibility.'

export default function EvidencePanel({ complaintId }) {
  const [items, setItems] = useState(null)
  const [file, setFile] = useState(null)
  const [inputKey, setInputKey] = useState(0)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [results, setResults] = useState({})
  const [notice, setNotice] = useState(DEFAULT_NOTICE)

  const load = useCallback(
    () => listEvidence(complaintId).then(setItems).catch((e) => setError(e.message)),
    [complaintId],
  )
  useEffect(() => { load() }, [load])

  async function onUpload(e) {
    e.preventDefault()
    if (!file) return
    if (file.size > MAX_BYTES) {
      setError('This file is larger than 10 MB.')
      return
    }
    setError('')
    setBusy(true)
    try {
      const out = await uploadEvidence(complaintId, file)
      if (out.notice) setNotice(out.notice)
      setFile(null)
      setInputKey((k) => k + 1) // clears the file box
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function onVerify(evidenceId) {
    setError('')
    try {
      const out = await verifyEvidence(complaintId, evidenceId)
      setResults((r) => ({ ...r, [evidenceId]: out }))
      if (out.notice) setNotice(out.notice)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="rounded-xl bg-white p-6 shadow space-y-4">
      <h2 className="text-lg font-semibold text-slate-800">Evidence</h2>

      <form onSubmit={onUpload} className="space-y-2">
        <input
          key={inputKey}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.txt"
          onChange={(e) => setFile(e.target.files[0] || null)}
          className="block w-full text-sm text-slate-700"
        />
        <p className="text-xs text-slate-500">Allowed: PDF, PNG, JPG, TXT. Largest size: 10 MB.</p>
        <button
          type="submit"
          disabled={!file || busy}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {busy ? 'Uploading...' : 'Upload file'}
        </button>
      </form>

      {error && <p className="text-sm text-red-700">{error}</p>}

      {items === null && !error && <p className="text-sm text-slate-600">Loading...</p>}
      {items && items.length === 0 && <p className="text-sm text-slate-600">No files yet.</p>}

      {items && items.length > 0 && (
        <ul className="divide-y divide-slate-200">
          {items.map((ev) => {
            const r = results[ev.id]
            return (
              <li key={ev.id} className="py-3 space-y-1">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="flex-1 break-all text-sm text-slate-800">{ev.original_filename}</span>
                  <span className="text-xs text-slate-500">
                    {formatSize(ev.file_size)} - {formatDateTime(ev.uploaded_at)}
                  </span>
                  <button
                    onClick={() => onVerify(ev.id)}
                    className="rounded-md border border-slate-300 px-3 py-1 text-sm text-slate-700 hover:bg-slate-100"
                  >
                    Verify
                  </button>
                </div>
                {r && (
                  <p className={'text-sm ' + (r.integrity_ok ? 'text-green-700' : 'text-red-700')}>
                    {r.integrity_ok ? 'Matches: ' : 'Problem: '}
                    {r.message} (checked {formatDateTime(r.verified_at)})
                  </p>
                )}
              </li>
            )
          })}
        </ul>
      )}

      <p className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600">{notice}</p>
    </section>
  )
}