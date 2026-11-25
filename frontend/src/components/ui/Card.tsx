import React from "react"

interface CardProps {
  title: string
  description: string
  status?: string
  privacyMode?: string
  children?: React.ReactNode
}

export const Card = ({ title, description, status, privacyMode, children }: CardProps) => {
  const statusColor = status?.toLowerCase()
  const colors: Record<string, string> = {
    submitted: "bg-indoise-100 text-indigo-800",
    under_review: "bg-yellow-100 text-amber-800",
    escalated_to_ic: "bg-orange-100 text-orange-800",
    closed: "bg-green-100 text-green-800",
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border p-6 hover:shadow-md transition-shadow duration-200">
      <div className="flex flex-col gap-4">
        <h3 className="text-lg font-medium text-gray-900">{title}</h3>
        <p className="text-sm text-gray-500 line-clamp-3">{description}</p>
        {status && (
          <span className={`px-2 py-1 rounded text-xs font-medium ${colors[status] || "bg-gray-200 text-gray-600"}`}>
            {status?.replace(/_/g, " ")}
          </span>
        )}
        {privacyMode && (
          <span className="text-xs px-2 py-1 rounded bg-purple-100 text-purple-800">
            {privacyMode}
          </span>
        )}
      </div>
      {children && <div className="mt-4">{children}</div>}
    </div>
  )
}