import axios from "axios"

const api = axios.create({
  baseURL: "http://localhost:8000",
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const authApi = {
  register: (email: string, password: string, fullName: string) =>
    api.post("/auth/register", { email, password, fullName }),
  login: (email: string, password: string) => api.post("/auth/login", { email, password }),
}

export const complaintApi = {
  listCategories: () => api.get("/companies/categories"),
  createComplaint: (data: {
    category_id: number
    privacy_mode: "identified" | "confidential" | "pseudonymous"
    title: string
    description: string
    incident_date?: string
  }) => api.post("/complaints", data),
  listComplaints: () => api.get("/complaints"),
  getComplaint: (id: string) => api.get(`/complaints/${id}`),
  updateStatus: (id: string, newStatus: string, note?: string) =>
    api.patch(`/complaints/${id}/status`, { new_status: newStatus, note }),
  getHistory: (id: string) => api.get(`/complaints/${id}/history`),
  revealIdentity: (id: string, reason: string) =>
    api.get(`/complaints/${id}/identity`, { params: { reason } }),
}

export const userApi = {
  getCurrentUser: () => api.get("/users/me"),
}

export default api