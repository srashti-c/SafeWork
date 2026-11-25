import { useState, useEffect } from "react"
import { useNavigate, useParams, useLocation } from "react-router-dom"
import { complaintApi, userApi } from "@/api"
import { Box, Card, SectionTitle, StatusBadge, KPICard } from "@/components/ui"

export const ComplaintsListPage = () => {
  const [complaints, setComplaints] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const { status, privacyMode } = useParams()
  const navigate = useNavigate()
  const location = useLocation()

  const useCurrentUser = () => {
    const { data } = userApi.getCurrentUser()
    return data
  }

  const initFilter = async () => {
    setLoading(true)
    try {
      let comps: any[] = []
      if (status || privacyMode) {
        const { data } = await complaintApi.listComplaints({
          status,
          privacy_mode: privacyMode,
        })
        comps = data
      } else {
        const { data } = await complaintApi.listComplaints()
        comps = data
      }
      setComplaints(comps)
    } catch (err) {
      console.error("Failed to load complaints", err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto my-8" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="mb-6">
        <div className="flex gap-4">
          <button
            onClick={() => navigate("/dashboard")}
            className="px-4 py-2 bg-white text-indigo-600 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Back to Dashboard
          </button>
          {currentUser?.role === "ic_admin" && (
            <button
              onClick={() => navigate("/categories")}
              className="px-4 py-2 bg-white text-indigo-600 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Manage Categories
            </button>
          )}
        </div>
      </nav>

      <SectionTitle title="Complaints List" />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {complaints.map((complaint) => (
          <Card
            key={complaint.id}
            title={complaint.title}
            description={complaint.description}
            status={complaint.status}
            privacyMode={complaint.privacy_mode}
          />
        ))}
      </div>
    </div>
  )
}