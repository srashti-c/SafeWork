import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth.jsx'
import { ROLE_LABELS } from '../labels.js'

// The menu depends on the role.
const MENU = {
  employee: [
    { to: '/complaints', label: 'My complaints', end: true },
    { to: '/complaints/new', label: 'File a complaint' },
  ],
  reviewer: [{ to: '/review', label: 'Review queue' }],
  ic_admin: [
    { to: '/review', label: 'Review queue' },
    { to: '/admin', label: 'IC admin' },
  ],
}

export default function Layout() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const items = MENU[user.role] || []

  function logout() {
    signOut()
    navigate('/login')
  }

  const linkClass = ({ isActive }) =>
    'rounded-md px-3 py-1.5 text-sm ' +
    (isActive ? 'bg-indigo-100 text-indigo-800' : 'text-slate-600 hover:bg-slate-100')

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="mx-auto max-w-5xl flex flex-wrap items-center gap-3 px-4 py-3">
          <span className="font-semibold text-slate-800">SafeWork</span>
          <nav className="flex flex-1 gap-1">
            {items.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} className={linkClass}>
                {item.label}
              </NavLink>
            ))}
          </nav>
          <span className="text-sm text-slate-700">
            {user.full_name}
            <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
              {ROLE_LABELS[user.role] || user.role}
            </span>
          </span>
          <button
            onClick={logout}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100"
          >
            Log out
          </button>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white px-4 py-3 text-center text-xs text-slate-500">
        Identity is role-gated and audited. It is protected, not anonymous. This tool supports
        human review; it does not decide what happened.
      </footer>
    </div>
  )
}