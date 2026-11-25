import { useEffect, useState } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { complaintApi, userApi } from "@/api"
import { Box, Card, SectionTitle, StatusBadge, KPICard } from "@/components/ui"

export const DashboardPage = () => {
  const [complaints, setComplaints] = useState<any[]>([])
  const [categories, setCategories] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [currentUser, setCurrentUser] = useState<any>(null)
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    initApp()
  }, [])

  const initApp = async () => {
    setLoading(true)
    try {
      const [user, cats, comps] = await Promise.all([
        userApi.getCurrentUser(),
        complaintApi.listCategories(),
        complaintApi.listComplaints(),
      ])
      setCurrentUser(user.data)
      setCategories(cats.data)
      setComplaints(comps.data)
    } catch (err) {
      console.error("Failed to init app", err)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem("token")
    navigate("/login")
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
      {/* Header */}
      <header className="border-b border-gray-200 bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path className="stroke-2" strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7l7 9z" />
              </svg>
            </div>
            <h1 className="text-xl font-bold text-gray-900">SafeWork</h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-gray-600 text-sm">
              {currentUser?.email || "Guest"}
            </span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-100 text-red-800 rounded-lg text-sm hover:bg-red-200 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {currentUser?.role === "ic_admin" && (
            <KPICard
              title="Total Complaints"
              value={complaints.length}
              trend="+12%"
              trendDirection="up"
              bg="bg-indigo-100 text-indigo-800"
            />
          )}
          <KPICard
            title="Active Cases"
            value={complaints.filter(c => c.status !== "closed").length}
            trend="+5%"
            trendDirection="up"
            bg="bg-green-100 text-green-800"
          />
          {currentUser?.role === "employee" && (
            <KPICard
              title="My Complaints"
              value={complaints.filter(c => c.email === currentUser?.email).length}
              trend="0%"
              trendDirection="side"
              bg="bg-purple-100 text-purple-800"
            />
          )}
        </div>

        {/* Recent Complaints */}
        <SectionTitle title="Recent Complaints" />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {complaints.slice(0, 6).map((complaint) => (
            <Card
              key={complaint.id}
              title={complaint.title}
              description={complaint.description.substring(0, 100) + "..."}
              status={complaint.status}
              privacyMode={complaint.privacy_mode}
            />
          ))}
        </div>
      </main>
    </div>
  )
}