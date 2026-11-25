import { useState, useEffect } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { complaintApi, userApi } from "@/api"
import { Box, Card, SectionTitle, Button, Select, Input } from "@/components/ui"
import { PRIVACY_MODES } from "@/labels"

export const ComplaintFormPage = () => {
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    category_id: null as number | null,
    privacy_mode: "identified" as string,
    incident_date: new Date().toISOString().split("T")[0],
  })
  const [categories, setCategories] = useState<any[]>([])
  const [loadingCategories, setLoadingCategories] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()

  useEffect(() => {
    loadCategories()
    if (id) loadComplaint()
  }, [id])

  const loadCategories = async () => {
    setLoadingCategories(true)
    try {
      const { data } = await complaintApi.listCategories()
      setCategories(data)
    } catch (err) {
      console.error("Failed to load categories", err)
    } finally {
      setLoadingCategories(false)
    }
  }

  const loadComplaint = async () => {
    setError(null)
    try {
      const { data } = await complaintApi.getComplaint(id!)
      setFormData({
        title: data.title,
        description: data.description,
        category_id: data.category_id,
        privacy_mode: data.privacy_mode,
        incident_date: data.incident_date,
      })
    } catch (err) {
      setError("Failed to load complaint")
      console.error(err)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      if (id) {
        await complaintApi.updateComplaint(id, formData)
      } else {
        await complaintApi.createComplaint(formData)
      }
      navigate("/dashboard")
    } catch (err) {
      setError("Failed to save complaint")
      console.error(err)
    }
  }

  if (loadingCategories) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto my-8" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <nav className="mb-4">
        <button
          onClick={() => navigate("/dashboard")}
          className="px-4 py-2 bg-white text-indigo-600 rounded-lg hover:bg-gray-50 transition-colors"
        >
          ← Back to Dashboard
        </button>
      </nav>

      <SectionTitle title={id ? "Edit Complaint" : "New Complaint"} />

      <Card className="p-8">
        {error && (
          <div className="bg-red-100 text-red-800 rounded-lg p-4 mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
              placeholder="Brief title describing the incident"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
            <textarea
              rows={3}
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
              placeholder="Describe what happened, when, and any witnesses"
            ></textarea>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
            <select
              value={formData.category_id ?? ""}
              onChange={(e) =>
                setFormData({ ...formData, category_id: e.target ? Number(e.target.value) : null })
              }
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
            >
              <option value="" disabled>
                Select a category
              </option>
              {categories?.map((cat: any) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Privacy Mode</label>
            <div className="grid grid-cols-3 gap-3">
              {PRIVACY_MODES.map((mode) => (
                <label
                  key={mode.value}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg border"
                >
                  <input
                    type="radio"
                    name="privacy_mode"
                    value={mode.value}
                    checked={formData.privacy_mode === mode.value}
                    onChange={(e) =>
                      setFormData({ ...formData, privacy_mode: e.target.value })
                    }
                  />
                  <span>
                    {mode.label}
                    {mode.help && (
                      <span className="text-xs text-gray-500 ml-2">
                        {mode.help}
                      </span>
                    )}
                  </span>
                </label>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {PRIVACY_MODES[0].help}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Incident Date</label>
            <input
              type="date"
              value={formData.incident_date}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  incident_date: e.target.value,
                })
              }
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
            />
          </div>

          <Button type="submit" className="w-full">
            {id ? "Update Complaint" : "Submit Complaint"}
          </Button>
        </form>
      </Card>
    </div>
  )
}