/**
 * Transparency Dashboard Page
 *
 * Central hub for viewing:
 * - User project benchmarks
 * - Recent calculation explanations
 * - Transparency analytics
 *
 * Implements "Wie kalkuliere ICH normalerweise?" concept from German Handwerk analysis.
 */

import React, { useState } from 'react'
import { useUserBenchmarks, useCalculationExplanations } from '@/lib/hooks/useTransparency'
import type { UserProjectBenchmark } from '@/types/api'

export const TransparencyDashboard: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Transparenz & Analyse</h1>
          <p className="text-gray-600 mt-2">
            Verstehen Sie Ihre Kalkulationen und vergleichen Sie mit Ihren bisherigen Projekten
          </p>
        </div>

        {/* Benchmarks Section */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Ihre Projekt-Benchmarks
          </h2>
          <BenchmarksOverview />
        </div>

        {/* Recent Explanations Section */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Letzte Kalkulationserklärungen
          </h2>
          <RecentExplanations />
        </div>

        {/* Analytics Section */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Transparenz-Statistiken
          </h2>
          <TransparencyAnalytics />
        </div>
      </div>
    </div>
  )
}

// ========================================
// Sub-Components
// ========================================

const BenchmarksOverview: React.FC = () => {
  const { data: benchmarks, isLoading, error } = useUserBenchmarks()
  const [sortBy, setSortBy] = useState<'projekttyp' | 'anzahl_projekte' | 'durchschnittspreis_eur'>(
    'anzahl_projekte'
  )

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-24 bg-gray-200 rounded-lg"></div>
        <div className="h-24 bg-gray-200 rounded-lg"></div>
        <div className="h-24 bg-gray-200 rounded-lg"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700 text-sm">
          <strong>Fehler:</strong> {error.message}
        </p>
      </div>
    )
  }

  if (!benchmarks || benchmarks.length === 0) {
    return (
      <div className="bg-gray-100 border border-gray-200 rounded-lg p-8 text-center">
        <div className="text-6xl mb-4">📊</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Noch keine Benchmarks verfügbar
        </h3>
        <p className="text-sm text-gray-600">
          Führen Sie Projekte durch und lassen Sie diese analysieren, um Ihre persönlichen
          Benchmarks zu erstellen.
        </p>
      </div>
    )
  }

  // Sort benchmarks
  const sortedBenchmarks = [...benchmarks].sort((a, b) => {
    if (sortBy === 'projekttyp') {
      return a.projekttyp.localeCompare(b.projekttyp)
    } else if (sortBy === 'anzahl_projekte') {
      return b.anzahl_projekte - a.anzahl_projekte
    } else {
      return b.durchschnittspreis_eur - a.durchschnittspreis_eur
    }
  })

  return (
    <div>
      {/* Sort Selector */}
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-gray-600">
          {benchmarks.length} {benchmarks.length === 1 ? 'Projekttyp' : 'Projekttypen'}
        </p>
        <div className="flex items-center space-x-2">
          <label className="text-sm text-gray-700">Sortieren nach:</label>
          <select
            value={sortBy}
            onChange={(e) =>
              setSortBy(
                e.target.value as 'projekttyp' | 'anzahl_projekte' | 'durchschnittspreis_eur'
              )
            }
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="anzahl_projekte">Anzahl Projekte</option>
            <option value="durchschnittspreis_eur">Durchschnittspreis</option>
            <option value="projekttyp">Projekttyp (A-Z)</option>
          </select>
        </div>
      </div>

      {/* Benchmark Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sortedBenchmarks.map((benchmark) => (
          <BenchmarkCard key={benchmark.id} benchmark={benchmark} />
        ))}
      </div>
    </div>
  )
}

const BenchmarkCard: React.FC<{ benchmark: UserProjectBenchmark }> = ({ benchmark }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{benchmark.projekttyp}</h3>
        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
          {benchmark.anzahl_projekte} {benchmark.anzahl_projekte === 1 ? 'Projekt' : 'Projekte'}
        </span>
      </div>

      <div className="space-y-3">
        <div>
          <p className="text-xs text-gray-500 mb-1">Durchschnittspreis</p>
          <p className="text-2xl font-bold text-gray-900">
            {benchmark.durchschnittspreis_eur.toLocaleString('de-DE', {
              style: 'currency',
              currency: 'EUR',
            })}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-500 mb-1">Minimum</p>
            <p className="text-sm font-medium text-gray-700">
              {benchmark.min_preis_eur.toLocaleString('de-DE', {
                style: 'currency',
                currency: 'EUR',
              })}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Maximum</p>
            <p className="text-sm font-medium text-gray-700">
              {benchmark.max_preis_eur.toLocaleString('de-DE', {
                style: 'currency',
                currency: 'EUR',
              })}
            </p>
          </div>
        </div>

        <div>
          <p className="text-xs text-gray-500 mb-1">Letztes Projekt</p>
          <p className="text-sm text-gray-700">
            {new Date(benchmark.letztes_projekt_datum).toLocaleDateString('de-DE', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        </div>
      </div>
    </div>
  )
}

const RecentExplanations: React.FC = () => {
  const { data: explanations, isLoading, error } = useCalculationExplanations({ limit: 5 })

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-3">
        <div className="h-20 bg-gray-200 rounded-lg"></div>
        <div className="h-20 bg-gray-200 rounded-lg"></div>
        <div className="h-20 bg-gray-200 rounded-lg"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700 text-sm">
          <strong>Fehler:</strong> {error.message}
        </p>
      </div>
    )
  }

  if (!explanations || explanations.length === 0) {
    return (
      <div className="bg-gray-100 border border-gray-200 rounded-lg p-8 text-center">
        <div className="text-6xl mb-4">📝</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Noch keine Erklärungen verfügbar
        </h3>
        <p className="text-sm text-gray-600">
          Erstellen Sie Kalkulationen, um detaillierte Erklärungen zu erhalten.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="divide-y divide-gray-200">
        {explanations.map((explanation) => (
          <ExplanationRow key={explanation.id} explanation={explanation} />
        ))}
      </div>
    </div>
  )
}

const ExplanationRow: React.FC<{ explanation: any }> = ({ explanation }) => {
  const confidenceBadgeColor = {
    high: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-red-100 text-red-800',
  }

  const confidenceText = {
    high: 'Hoch',
    medium: 'Mittel',
    low: 'Niedrig',
  }

  return (
    <div className="p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-3">
            <span
              className={`px-2 py-1 text-xs font-medium rounded ${
                confidenceBadgeColor[explanation.confidence_level]
              }`}
            >
              {confidenceText[explanation.confidence_level]}
            </span>
            <p className="text-lg font-semibold text-gray-900">
              {explanation.total_price_eur.toLocaleString('de-DE', {
                style: 'currency',
                currency: 'EUR',
              })}
            </p>
            <p className="text-sm text-gray-500">
              {new Date(explanation.created_at).toLocaleDateString('de-DE')}
            </p>
          </div>
          <p className="text-sm text-gray-600 mt-1">
            {explanation.faktoren.length} Faktoren,{' '}
            {explanation.similar_projects_count > 0
              ? `${explanation.similar_projects_count} ähnliche Projekte`
              : 'keine Vergleichsdaten'}
          </p>
        </div>
        <button className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors">
          Details →
        </button>
      </div>
    </div>
  )
}

const TransparencyAnalytics: React.FC = () => {
  const { data: benchmarks } = useUserBenchmarks()
  const { data: explanations } = useCalculationExplanations()

  // Calculate analytics
  const totalProjects = benchmarks?.reduce((sum, b) => sum + b.anzahl_projekte, 0) || 0
  const totalExplanations = explanations?.length || 0
  const highConfidenceCount =
    explanations?.filter((e) => e.confidence_level === 'high').length || 0
  const avgConfidence =
    explanations && explanations.length > 0
      ? explanations.reduce((sum, e) => sum + e.confidence_score, 0) / explanations.length
      : 0

  const stats = [
    {
      label: 'Gesamte Projekte',
      value: totalProjects,
      icon: '📊',
      color: 'bg-blue-50 text-blue-900',
    },
    {
      label: 'Projekttypen',
      value: benchmarks?.length || 0,
      icon: '📁',
      color: 'bg-green-50 text-green-900',
    },
    {
      label: 'Erklärungen',
      value: totalExplanations,
      icon: '📝',
      color: 'bg-purple-50 text-purple-900',
    },
    {
      label: 'Hohe Konfidenz',
      value: `${highConfidenceCount}/${totalExplanations}`,
      icon: '✅',
      color: 'bg-orange-50 text-orange-900',
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, index) => (
        <div key={index} className={`rounded-lg p-6 ${stat.color}`}>
          <div className="text-3xl mb-2">{stat.icon}</div>
          <p className="text-3xl font-bold mb-1">{stat.value}</p>
          <p className="text-sm opacity-80">{stat.label}</p>
        </div>
      ))}
    </div>
  )
}
