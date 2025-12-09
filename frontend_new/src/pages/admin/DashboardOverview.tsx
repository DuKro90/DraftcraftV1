/**
 * Admin Dashboard Overview Page
 *
 * Displays:
 * - Key metrics (documents, patterns, confidence)
 * - 7-day document trend chart
 * - Pattern severity breakdown
 * - Recent activity feed
 */

import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api/client'
import type { DashboardStats, DashboardActivityResponse } from '@/types/api'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

const SEVERITY_COLORS = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#3b82f6',
}

export const DashboardOverview: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [activity, setActivity] = useState<DashboardActivityResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDashboardData()

    // Refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const [statsData, activityData] = await Promise.all([
        api.getDashboardStats(),
        api.getDashboardActivity(),
      ])
      setStats(statsData)
      setActivity(activityData)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Fehler beim Laden der Dashboard-Daten')
      console.error('Failed to fetch dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
          <p className="mt-4 text-gray-600">Lädt Dashboard...</p>
        </div>
      </div>
    )
  }

  if (error && !stats) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-800 font-bold mb-2">Fehler</h3>
        <p className="text-red-600">{error}</p>
        <button
          onClick={fetchDashboardData}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Erneut versuchen
        </button>
      </div>
    )
  }

  if (!stats) {
    return null
  }

  // Prepare chart data
  const patternSeverityData = Object.entries(stats.pattern_severity_breakdown).map(
    ([severity, count]) => ({
      name: severity,
      value: count,
      color: SEVERITY_COLORS[severity as keyof typeof SEVERITY_COLORS],
    })
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Übersicht</h1>
          <p className="text-sm text-gray-600">
            Letzte Aktualisierung: {new Date(stats.timestamp).toLocaleString('de-DE')}
          </p>
        </div>
        <button
          onClick={fetchDashboardData}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Lädt...' : 'Aktualisieren'}
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Documents */}
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 font-medium">Gesamt Dokumente</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {stats.total_documents.toLocaleString('de-DE')}
              </p>
            </div>
            <div className="bg-blue-100 p-3 rounded-full">
              <svg
                className="w-8 h-8 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
          </div>
          <p className="text-sm text-gray-500 mt-3">
            Heute: +{stats.processed_today}
          </p>
        </div>

        {/* Active Patterns */}
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-yellow-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 font-medium">Aktive Muster</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {stats.active_patterns}
              </p>
            </div>
            <div className="bg-yellow-100 p-3 rounded-full">
              <svg
                className="w-8 h-8 text-yellow-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
          </div>
          <p className="text-sm text-red-600 mt-3 font-medium">
            {stats.critical_patterns} kritisch
          </p>
        </div>

        {/* Average Confidence */}
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 font-medium">Ø Konfidenz</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {(stats.avg_confidence * 100).toFixed(1)}%
              </p>
            </div>
            <div className="bg-green-100 p-3 rounded-full">
              <svg
                className="w-8 h-8 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
          </div>
          <p className="text-sm text-green-600 mt-3">
            Letzte 7 Tage
          </p>
        </div>

        {/* Total Users */}
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-purple-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 font-medium">Aktive Nutzer</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {stats.total_users}
              </p>
            </div>
            <div className="bg-purple-100 p-3 rounded-full">
              <svg
                className="w-8 h-8 text-purple-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                />
              </svg>
            </div>
          </div>
          <p className="text-sm text-gray-500 mt-3">
            Mit Konfiguration
          </p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Document Trend Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">
            Dokumente (7 Tage)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={stats.documents_last_7_days}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#3b82f6"
                strokeWidth={2}
                name="Dokumente"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Pattern Severity Breakdown */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">
            Muster nach Schweregrad
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={patternSeverityData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${entry.value}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {patternSeverityData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Activity */}
      {activity && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-bold text-gray-900">Letzte Aktivitäten</h3>
          </div>
          <div className="divide-y">
            {activity.activities.length === 0 ? (
              <p className="px-6 py-8 text-center text-gray-500">
                Keine aktuellen Aktivitäten
              </p>
            ) : (
              activity.activities.map((item, index) => {
                const getSeverityColor = () => {
                  switch (item.severity) {
                    case 'success':
                      return 'bg-green-100 text-green-800'
                    case 'error':
                    case 'high':
                      return 'bg-red-100 text-red-800'
                    case 'warning':
                    case 'medium':
                      return 'bg-yellow-100 text-yellow-800'
                    default:
                      return 'bg-blue-100 text-blue-800'
                  }
                }

                return (
                  <div key={index} className="px-6 py-4 hover:bg-gray-50">
                    <div className="flex items-start gap-4">
                      <div className={`p-2 rounded-lg ${getSeverityColor()}`}>
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          {item.severity === 'success' ? (
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          ) : (
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                            />
                          )}
                        </svg>
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{item.title}</p>
                        <p className="text-sm text-gray-600 mt-1">
                          {item.description}
                        </p>
                        <p className="text-xs text-gray-500 mt-2">
                          {new Date(item.timestamp).toLocaleString('de-DE')}
                        </p>
                      </div>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}
