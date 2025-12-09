/**
 * Pattern Management Page
 *
 * Features:
 * - List all extraction failure patterns
 * - Filter by severity and status
 * - Approve/reject pattern fixes
 * - View pattern details
 */

import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api/client'
import type { ExtractionFailurePattern, SeverityLevel } from '@/types/api'

const SEVERITY_COLORS: Record<SeverityLevel, string> = {
  CRITICAL: 'bg-red-100 text-red-800 border-red-200',
  HIGH: 'bg-orange-100 text-orange-800 border-orange-200',
  MEDIUM: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  LOW: 'bg-blue-100 text-blue-800 border-blue-200',
}

export const PatternManagement: React.FC = () => {
  const [patterns, setPatterns] = useState<ExtractionFailurePattern[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all')
  const [showActiveOnly, setShowActiveOnly] = useState(true)
  const [expandedPattern, setExpandedPattern] = useState<string | null>(null)

  useEffect(() => {
    fetchPatterns()
  }, [selectedSeverity, showActiveOnly])

  const fetchPatterns = async () => {
    try {
      setLoading(true)
      const params: any = {}

      if (selectedSeverity !== 'all') {
        params.severity = selectedSeverity
      }

      if (showActiveOnly) {
        params.is_active = true
      }

      const data = await api.getFailurePatterns(params)
      setPatterns(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Fehler beim Laden der Muster')
      console.error('Failed to fetch patterns:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (patternId: string) => {
    if (!confirm('Möchten Sie dieses Muster-Fix wirklich genehmigen?')) {
      return
    }

    try {
      await api.approvePatternFix(patternId, { approved: true })
      await fetchPatterns() // Refresh list
      alert('Muster-Fix wurde genehmigt')
    } catch (err: any) {
      alert(`Fehler: ${err.message}`)
    }
  }

  const handleReject = async (patternId: string) => {
    const notes = prompt('Grund für Ablehnung (optional):')

    try {
      await api.approvePatternFix(patternId, {
        approved: false,
        deployment_notes: notes || undefined,
      })
      await fetchPatterns() // Refresh list
      alert('Muster-Fix wurde abgelehnt')
    } catch (err: any) {
      alert(`Fehler: ${err.message}`)
    }
  }

  if (loading && patterns.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
          <p className="mt-4 text-gray-600">Lädt Muster...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Muster-Verwaltung</h1>
          <p className="text-sm text-gray-600 mt-1">
            {patterns.length} Muster gefunden
          </p>
        </div>
        <button
          onClick={fetchPatterns}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Lädt...' : 'Aktualisieren'}
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-wrap gap-4">
          {/* Severity Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Schweregrad
            </label>
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">Alle</option>
              <option value="CRITICAL">Kritisch</option>
              <option value="HIGH">Hoch</option>
              <option value="MEDIUM">Mittel</option>
              <option value="LOW">Niedrig</option>
            </select>
          </div>

          {/* Active Only Toggle */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <button
              onClick={() => setShowActiveOnly(!showActiveOnly)}
              className={`px-4 py-2 rounded-lg border ${
                showActiveOnly
                  ? 'bg-blue-50 border-blue-300 text-blue-700'
                  : 'bg-gray-50 border-gray-300 text-gray-700'
              }`}
            >
              {showActiveOnly ? 'Nur aktive' : 'Alle anzeigen'}
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {/* Patterns List */}
      <div className="space-y-4">
        {patterns.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <svg
              className="w-16 h-16 text-gray-400 mx-auto mb-4"
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
            <p className="text-gray-600">Keine Muster gefunden</p>
            <p className="text-sm text-gray-500 mt-2">
              Ändern Sie die Filter, um mehr Ergebnisse zu sehen
            </p>
          </div>
        ) : (
          patterns.map((pattern) => {
            const isExpanded = expandedPattern === pattern.id
            const severityClass = SEVERITY_COLORS[pattern.severity]

            return (
              <div key={pattern.id} className="bg-white rounded-lg shadow">
                {/* Pattern Header */}
                <div
                  className="p-6 cursor-pointer hover:bg-gray-50"
                  onClick={() =>
                    setExpandedPattern(isExpanded ? null : pattern.id)
                  }
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-bold border ${severityClass}`}
                        >
                          {pattern.severity}
                        </span>
                        <span className="text-sm text-gray-600">
                          {pattern.occurrence_count} Vorkommen
                        </span>
                      </div>
                      <h3 className="text-lg font-bold text-gray-900">
                        {pattern.pattern_type}
                      </h3>
                      <p className="text-gray-600 mt-1">
                        {pattern.description}
                      </p>
                    </div>
                    <svg
                      className={`w-6 h-6 text-gray-400 transition-transform ${
                        isExpanded ? 'transform rotate-180' : ''
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="px-6 pb-6 border-t">
                    <div className="grid grid-cols-2 gap-6 mt-4">
                      {/* Pattern Details */}
                      <div>
                        <h4 className="font-bold text-gray-900 mb-3">
                          Details
                        </h4>
                        <dl className="space-y-2">
                          <div>
                            <dt className="text-sm text-gray-600">
                              Erstes Auftreten
                            </dt>
                            <dd className="text-sm font-medium">
                              {new Date(pattern.first_seen).toLocaleDateString(
                                'de-DE'
                              )}
                            </dd>
                          </div>
                          <div>
                            <dt className="text-sm text-gray-600">
                              Letztes Auftreten
                            </dt>
                            <dd className="text-sm font-medium">
                              {new Date(pattern.last_seen).toLocaleDateString(
                                'de-DE'
                              )}
                            </dd>
                          </div>
                          <div>
                            <dt className="text-sm text-gray-600">Status</dt>
                            <dd className="text-sm font-medium">
                              {pattern.is_resolved ? (
                                <span className="text-green-600">Gelöst</span>
                              ) : (
                                <span className="text-orange-600">Aktiv</span>
                              )}
                            </dd>
                          </div>
                        </dl>
                      </div>

                      {/* Suggested Fix */}
                      <div>
                        <h4 className="font-bold text-gray-900 mb-3">
                          Vorgeschlagene Lösung
                        </h4>
                        <p className="text-sm text-gray-700 bg-gray-50 p-4 rounded-lg">
                          {pattern.suggested_fix || 'Keine Lösung vorgeschlagen'}
                        </p>
                      </div>
                    </div>

                    {/* Example Documents */}
                    {pattern.example_documents &&
                      pattern.example_documents.length > 0 && (
                        <div className="mt-4">
                          <h4 className="font-bold text-gray-900 mb-2">
                            Beispiel-Dokumente
                          </h4>
                          <ul className="text-sm text-gray-600 space-y-1">
                            {pattern.example_documents.map((docId, idx) => (
                              <li key={idx}>• {docId}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                    {/* Action Buttons */}
                    {!pattern.is_resolved && (
                      <div className="mt-6 flex gap-3">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleApprove(pattern.id)
                          }}
                          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                        >
                          Fix genehmigen
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleReject(pattern.id)
                          }}
                          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                        >
                          Ablehnen
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
