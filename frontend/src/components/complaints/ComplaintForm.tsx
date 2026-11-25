import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { complaintApi } from "@/api"
import { Box, Card, SectionTitle } from "@/components/ui"

interface ComplaintFormProps {
  initial?: {
    category_id: number
    privacy_mode: "identified" | "confidential" | "pseudonymous"
    title: string
    description: string
    incident_date?: string
  }
}

export const ComplaintForm = ({ initial }: ComplaintFormProps = {}) => {
  const [form, setForm] = useState({
    category_id: initial?.category_id || 1,
    privacy_mode: initial?.privacy_mode || "identified",
    title: initial?.title || "",
    description: initial?.description || "",
    incident_date: initial?.incident_date || "",
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const response = await complaintApi.createComplaint(form)
      navigate(`/complaints/${response.data.id}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create complaint")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm p-8 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">New Complaint</h2>

      {error && (
        <div className="mb-4 p-3 rounded bg-red-100 text-red-800 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Category */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Category
            <span className="text-red-500">*</span>
          </label>
          <select
            value={form.category_id}
            onChange={(e) =>
              setForm((f) => ({ ...f, category_id: Number(e.target.value) }))
            }
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
          >
            <option value="" disabled>Select a category</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </select>
        </div>

        {/* Privacy Mode */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Privacy Mode
            <span className="text-red-500">*</span>
          </label>
          <div className="grid grid-cols-3 gap-3">
            <label
              key="identified"
              className="flex items-center gap-2 px-3 py-2 rounded border bg-indigo-50 hover:bg-indigo-100"
            >
              <input
                type="radio"
                name="privacy_mode"
                value="identified"
                checked={form.privacy_mode === "identified"}
                onChange={(e) => setForm((f) => ({ ...f, privacy_mode: "identified" }))}
                className="rounded border-indigo-600"
              />
              Identified
            </label>
            <label
              key="confidential"
              className="flex items-center gap-2 px-3 py-2 rounded bg-gray-100 hover:bg-gray-200"
            >
              <input
                type="radio"
                name="privacy_mode"
                value="confidential"
                checked={form.privacy_mode === "confidential"}
                onChange={(e) =>
                  setForm((f) => ({ ...f, privacy_mode: "confidential" }))}
                className="rounded border-gray-600"
              />
              Confidential
            </label>
            <label
              key="pseudonymous"
              className="flex items-center gap-2 px-3 py-2 rounded bg-purple-50 hover:bg-purple-100"
            >
              <input
                type="radio"
                name="privacy_mode"
                value="pseudonymous"
                checked={form.privacy_mode === "pseudonymous"}
                onChange={(e) =>
                  setForm((f) => ({ ...f, privacy_mode: "pseudonymous" }))}
                className="rounded border-purple-600"
              />
              Pseudonymous
            </label>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            {form.privacy_mode}: See design rules - identity stored separately
          </p>
        </div>

        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Title
            <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={form.title}
            onChange={(e) =>
              setForm((f) => ({ ...f, title: e.target.value }))
            }
            required
            maxLength={200}
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
            placeholder="Brief title describing the incident"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description
            <span className="text-red-500">*</span>
          </label>
          <textarea
            value={form.description}
            onChange={(e) =>
              setForm((f) => ({ ...f, description: e.target.value }))
            }
            required
            maxLength={5000}
            rows={4}
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors resize-none"
            placeholder="Describe what happened, when, where, and any witnesses"
          />
        </div>

        {/* Incident Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Incident Date
          </label>
          <input
            type="date"
            value={form.incident_date}
            onChange={(e) =>
              setForm((f) => ({ ...f, incident_date: e.target.value }))
            }
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 px-4 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 hover:transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed">
          {loading ? "Submitting..." : "Submit Complaint"}
        </button>
      </form>
    </div>
  )
}