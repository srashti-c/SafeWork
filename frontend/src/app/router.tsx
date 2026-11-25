import { createBrowserRouter, RouterProvider } from "react-router-dom"
import { LoginPage } from "@/pages/auth/Login"
import { DashboardPage } from "@/pages/dashboard/Dashboard"
import { ComplaintFormPage } from "@/pages/complaints/Form"
import { ComplaintsListPage } from "@/pages/complaints/List"
import { CategoriesManagementPage } from "@/pages/categories/Management"
import { StatusHistoryPage } from "@/pages/complaints/History"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <DashboardPage />,
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/dashboard",
    element: <DashboardPage />,
    errorElement: "/login",
  },
  {
    path: "/complaints/new",
    element: <ComplaintFormPage />,
    errorElement: "/login",
  },
  {
    path: "/complaints",
    element: <ComplaintsListPage />,
    errorElement: "/login",
  },
  {
    path: "/categories",
    element: <CategoriesManagementPage />,
    errorElement: "/login",
  },
  {
    path: "/complaints/:id",
    element: (
      <div>
        <ComplaintFormPage />
        <StatusHistoryPage />
      </div>
    ),
    errorElement: "/login",
  },
])

export const App = () => <RouterProvider router={router} />