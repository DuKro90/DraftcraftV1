/**
 * Main layout component with navigation
 */

import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { FileText, LayoutDashboard, LogOut } from 'lucide-react'
import { api } from '@/lib/api/client'
import Button from './ui/Button'

export default function Layout() {
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = () => {
    api.logout()
    navigate('/login')
  }

  const navItems = [
    { path: '/workflow', label: 'Workflow', icon: FileText },
    { path: '/admin', label: 'Admin', icon: LayoutDashboard },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2">
              <FileText className="h-8 w-8 text-brand-600" />
              <span className="text-xl font-bold text-gray-900">DraftCraft</span>
              <span className="text-sm text-gray-500 hidden sm:inline">
                German Handwerk Analysis
              </span>
            </Link>

            {/* Navigation */}
            <nav className="flex items-center gap-1">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.path

                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-brand-50 text-brand-700 font-medium'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span className="hidden sm:inline">{item.label}</span>
                  </Link>
                )
              })}

              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="ml-4"
              >
                <LogOut className="h-4 w-4 mr-2" />
                <span className="hidden sm:inline">Abmelden</span>
              </Button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            © 2025 DraftCraft. German Handwerk Document Analysis System.
          </p>
        </div>
      </footer>
    </div>
  )
}
