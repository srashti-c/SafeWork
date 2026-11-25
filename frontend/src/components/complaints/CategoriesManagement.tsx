import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { complaintApi } from "@/api"
import { Box, Card, SectionTitle, Button } from "@/components/ui"

export const CategoriesManagement = () => {
  const [categories, setCategories] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    loadCategories()
  }, [])

  const loadCategories = async () => {
    setLoading(true)
    try {
      const response = await complaintApi.listCategories()
      setCategories(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load categories")
    } finally {
      setLoading(false)
    }
  }

  const handleCreateCategory = async (name: string, description: string) => {
    setLoading(true)
    setError(null)
    try {
      // Note: Backend doesn't have a create category endpoint yet
      // This would need to be added to the API
      await loadCategories()
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create category")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm p-8 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Category Management</h2>

      {error && (
        <div className="mb-4 p-3 rounded bg-red-100 text-red-800 text-sm">
          {error}
        </div>
      )}

      <SectionTitle title="Available Categories" />

      <div className="space-y-4">
        {categories.map((cat) => (
          <Card
            key={cat.id}
            title={cat.name}
            description={cat.description || "No description"}
          />
        ))}

        {/* Add New Category Form */}
        <div className="pt-6 border-t border-gray-200">
          <h3 className="text-semibold text-gray-900 mb-4">Add New Category</h3>
          <form className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category Name
                <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                maxLength={100}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                placeholder="e.g., Verbal harassment"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                rows={3}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors resize-none"
                placeholder="Optional description"
              />
            </div>
            <button
              type="submit"
              className="w-full py-3 px-4 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 hover:transition-colors duration-200"
            >
              Add Category
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}