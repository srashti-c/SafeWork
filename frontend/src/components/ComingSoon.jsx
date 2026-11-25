export default function ComingSoon({ name }) {
  return (
    <div className="rounded-xl bg-white p-6 shadow">
      <h1 className="text-xl font-semibold text-slate-800">{name}</h1>
      <p className="mt-2 text-sm text-slate-600">This screen is built in a later step.</p>
    </div>
  )
}