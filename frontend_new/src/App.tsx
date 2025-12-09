import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import Layout from './components/Layout'
import LoadingSpinner from './components/ui/LoadingSpinner'
import { DashboardLayout } from './components/admin/DashboardLayout'
import { DashboardOverview } from './pages/admin/DashboardOverview'
import { PatternManagement } from './pages/admin/PatternManagement'
import { TransparencyDashboard } from './pages/TransparencyDashboard'

// Lazy load pages for better performance
const DocumentWorkflow = lazy(() => import('./pages/DocumentWorkflow'))
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'))
const LoginPage = lazy(() => import('./pages/LoginPage'))

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingSpinner fullScreen />}>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected routes with main Layout */}
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/documents" replace />} />
            <Route path="documents" element={<DocumentWorkflow />} />
            <Route path="workflow" element={<DocumentWorkflow />} />
            <Route path="transparency" element={<TransparencyDashboard />} />
          </Route>

          {/* Admin Dashboard routes with DashboardLayout */}
          <Route path="/admin" element={<DashboardLayout />}>
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardOverview />} />
            <Route path="patterns" element={<PatternManagement />} />
          </Route>

          {/* Legacy admin route (backward compatibility) */}
          <Route path="/admin-old" element={<Layout />}>
            <Route index element={<AdminDashboard />} />
          </Route>

          {/* 404 fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

export default App
