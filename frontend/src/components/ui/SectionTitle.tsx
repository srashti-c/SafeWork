import React from "react"

export const SectionTitle = ({ title }: { title: string }) => {
  return (
    <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-start">
      <svg className="w-5 h-5 text-indigo-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path className="stroke-2" strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7l7 9z" />
      </svg>
      {title}
    </h2>
  )
}