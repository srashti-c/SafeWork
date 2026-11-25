import { useState, useEffect } from "react"
import { useParams } from "react-router-dom"
import { complaintApi, userApi } from "@/api"
import { Box, Card, SectionTitle } from "@/components/ui"

export const StatusHistoryPage = () => {
  const { id } = useParams<{ id: string }>()
  const [history, setHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    setLoading(true)
    try {
      const { data } = await complaintApi.getComplaint(id!)
      // Build status history from complaint timeline/events
      const timeline = data.timeline || []
      setHistory(timeline)
    } catch (err) {
      console.error("Failed to load status history", err)
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
    <div className="min-h-screen bg-gray-50 p-6">
      <nav className="mb-4">
        <button
          onClick={() => window.history.back()}
          className="px-4 py-2 bg-white text-indigo-600 rounded-lg hover:bg-gray-50 transition-colors"
        >
          ← Back
        </button>
      </nav>

      <SectionTitle title="Status History" />

      {history.length === 0 && (
        <p className="text-gray-500">
          No status history available for this complaint.
        </p>
      )}

      <Card className="p-6">
        <div className="space-y-3">
          {history.map((entry) => (
            <div
              key={entry.id}
              className="flex items-start gap-3 px-3 py-2 rounded border-b"
            >
              <div className="w-2 h-2 rounded-full bg-indigo-500 mt-1" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">
                  {entry.status || "Updated"}
                </p>
                <p className="text-xs text-gray-500">
                  {entry.timestamp ? new Date(entry.timestamp).toLocaleDateString() : ""}
                </p>
                {entry.comment && (
                  <p className="text-xs text-gray-500 mt-1">
                    "{entry.comment}"
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}