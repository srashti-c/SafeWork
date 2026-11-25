import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { complaintApi, userApi } from "@/api"
import { Box, Card, SectionTitle, Button } from "@/components/ui"

export const CategoriesManagementPage = () => {
  const [categories, setCategories] = useState<any[]>([])
  const [newCategory, setNewCategory] = useState("")
  const navigate = useNavigate()

  useEffect(() => {
    loadCategories()
  }, [])

  const loadCategories = async () => {
    try {
      const { data } = await complaintApi.listCategories()
      setCategories(data)
    } catch (err) {
      console.error("Failed to load categories", err)
    }
  }

  const handleAddCategory = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await complaintApi.addCategory(newCategory)
      setNewCategory("")
      loadCategories()
    } catch (err) {
      console.error("Failed to add category", err)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto">
        <SectionTitle title="Manage Complaint Categories" />

        <Card className="p-6 mb-8">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Category</h3>
          <form onSubmit={handleAddCategory} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Category Name</label>
              <input
                type="text"
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                placeholder="e.g., harassment, safety, ethics"
              />
            </div>
            <button
              type="submit"
              className="w-full py-3 px-4 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 hover:transition-colors duration-200">
              Add Category
            </button>
          </form>
        </Card>

        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Existing Categories</h3>
          <div className="space-y-3">
            {categories.map((cat) => (
              <div
                key={cat.id}
                className="flex items-center justify-between px-4 py-3 border border-gray-200 rounded-lg"
              >
                <span className="text-gray-600">{cat.name}</span>
                <button
                  className="text-sm text-indigo-600 hover:text-indigo-800"
                >
                  Edit
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}