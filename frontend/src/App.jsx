import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth.jsx'
import Layout from './components/Layout.jsx'
import Protected from './components/Protected.jsx'
import ComingSoon from './components/ComingSoon.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import MyComplaints from './pages/MyComplaints.jsx'
import NewComplaint from './pages/NewComplaint.jsx'
import ComplaintDetail from './pages/ComplaintDetail.jsx'
import ReviewQueue from './pages/ReviewQueue.jsx'
import StaffComplaintDetail from './pages/StaffComplaintDetail.jsx'

// "/" sends each role to its own first screen.
function Home() {
  const { user } = useAuth()
  return <Navigate to={user.role === 'employee' ? '/complaints' : '/review'} replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route element={<Protected><Layout /></Protected>}>
            <Route index element={<Home />} />
            <Route path="complaints" element={<MyComplaints />} />
            <Route path="complaints/new" element={<NewComplaint />} />
            <Route path="complaints/:id" element={<ComplaintDetail />} />
            <Route
              path="review"
              element={<Protected roles={['reviewer', 'ic_admin']}><ReviewQueue /></Protected>}
            />
            <Route
              path="admin"
              element={<Protected roles={['ic_admin']}><ComingSoon name="IC admin" /></Protected>}
            />
            <Route path="review/:id" element={<Protected roles={['reviewer', 'ic_admin']}><StaffComplaintDetail /></Protected>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}