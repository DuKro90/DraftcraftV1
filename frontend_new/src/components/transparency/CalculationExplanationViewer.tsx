/**
 * Calculation Explanation Viewer Component
 *
 * Displays AI-generated explanations for pricing calculations with:
 * - Progressive disclosure (Level 1-4 detail depth)
 * - Visual confidence indicators (Ampelsystem: high/medium/low)
 * - TIER breakdown visualization
 * - Individual calculation factors with impact percentages
 * - Data source transparency
 */

import React, { useState } from 'react'
import { useCalculationExplanation, useConfidenceBadgeColor, useDataSourceBadge, useDeviationFormatter } from '@/lib/hooks/useTransparency'
import type { CalculationExplanation, CalculationFactor } from '@/types/api'

interface CalculationExplanationViewerProps {
  calculationId: string
  className?: string
}

export const CalculationExplanationViewer: React.FC<CalculationExplanationViewerProps> = ({
  calculationId,
  className = '',
}) => {
  const { data: explanation, isLoading, error } = useCalculationExplanation(calculationId)
  const [detailLevel, setDetailLevel] = useState<1 | 2 | 3 | 4>(2) // Progressive disclosure level

  if (isLoading) {
    return (
      <div className={`animate-pulse space-y-4 ${className}`}>
        <div className="h-8 bg-gray-200 rounded w-3/4"></div>
        <div className="h-4 bg-gray-200 rounded w-full"></div>
        <div className="h-4 bg-gray-200 rounded w-5/6"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
        <p className="text-red-700 text-sm">
          <strong>Fehler beim Laden der Erklärung:</strong> {error.message}
        </p>
      </div>
    )
  }

  if (!explanation) {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-lg p-4 ${className}`}>
        <p className="text-gray-600 text-sm">Keine Erklärung verfügbar.</p>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg shadow-md ${className}`}>
      {/* Header: Confidence & Price */}
      <CalculationHeader explanation={explanation} />

      {/* Detail Level Selector */}
      <DetailLevelSelector currentLevel={detailLevel} onLevelChange={setDetailLevel} />

      {/* Level 1: Summary - Top 3-5 factors only */}
      {detailLevel >= 1 && <TopFactorsSummary factors={explanation.faktoren} />}

      {/* Level 2: All factors */}
      {detailLevel >= 2 && <AllFactorsBreakdown factors={explanation.faktoren} />}

      {/* Level 3: TIER breakdown */}
      {detailLevel >= 3 && <TierBreakdownVisualization tierBreakdown={explanation.tier_breakdown} totalPrice={explanation.total_price_eur} />}

      {/* Level 4: Benchmark comparison */}
      {detailLevel >= 4 && <BenchmarkComparison explanation={explanation} />}
    </div>
  )
}

// ========================================
// Sub-Components
// ========================================

const CalculationHeader: React.FC<{ explanation: CalculationExplanation }> = ({ explanation }) => {
  const confidenceBadgeColor = useConfidenceBadgeColor(explanation.confidence_level)
  const confidenceText = {
    high: 'Hohe Sicherheit',
    medium: 'Mittlere Sicherheit',
    low: 'Niedrige Sicherheit',
  }

  return (
    <div className="p-6 border-b border-gray-200">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-2xl font-bold text-gray-900">
            {explanation.total_price_eur.toLocaleString('de-DE', {
              style: 'currency',
              currency: 'EUR',
            })}
          </h3>
          <p className="text-sm text-gray-500 mt-1">Berechneter Gesamtpreis</p>
        </div>
        <div className={`px-3 py-1 rounded-full text-sm font-medium border ${confidenceBadgeColor}`}>
          {confidenceText[explanation.confidence_level]} ({Math.round(explanation.confidence_score * 100)}%)
        </div>
      </div>
    </div>
  )
}

const DetailLevelSelector: React.FC<{
  currentLevel: 1 | 2 | 3 | 4
  onLevelChange: (level: 1 | 2 | 3 | 4) => void
}> = ({ currentLevel, onLevelChange }) => {
  const levels = [
    { level: 1, label: 'Zusammenfassung' },
    { level: 2, label: 'Alle Faktoren' },
    { level: 3, label: 'TIER-Details' },
    { level: 4, label: 'Benchmark-Vergleich' },
  ] as const

  return (
    <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
      <label className="block text-sm font-medium text-gray-700 mb-2">Detailgrad:</label>
      <div className="flex space-x-2">
        {levels.map(({ level, label }) => (
          <button
            key={level}
            onClick={() => onLevelChange(level)}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              currentLevel >= level
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  )
}

const TopFactorsSummary: React.FC<{ factors: CalculationFactor[] }> = ({ factors }) => {
  // Show top 5 factors by impact
  const topFactors = [...factors]
    .sort((a, b) => b.impact_percent - a.impact_percent)
    .slice(0, 5)

  return (
    <div className="p-6 border-b border-gray-200">
      <h4 className="text-lg font-semibold text-gray-900 mb-4">Wichtigste Faktoren</h4>
      <div className="space-y-3">
        {topFactors.map((factor) => (
          <FactorCard key={factor.id} factor={factor} showDetails={false} />
        ))}
      </div>
    </div>
  )
}

const AllFactorsBreakdown: React.FC<{ factors: CalculationFactor[] }> = ({ factors }) => {
  // Group factors by category
  const groupedFactors = factors.reduce((acc, factor) => {
    const category = factor.factor_category || 'Sonstiges'
    if (!acc[category]) {
      acc[category] = []
    }
    acc[category].push(factor)
    return acc
  }, {} as Record<string, CalculationFactor[]>)

  return (
    <div className="p-6 border-b border-gray-200">
      <h4 className="text-lg font-semibold text-gray-900 mb-4">Detaillierte Faktorenanalyse</h4>
      <div className="space-y-6">
        {Object.entries(groupedFactors).map(([category, categoryFactors]) => (
          <div key={category}>
            <h5 className="text-md font-medium text-gray-700 mb-3 capitalize">{category}</h5>
            <div className="space-y-2">
              {categoryFactors
                .sort((a, b) => b.impact_percent - a.impact_percent)
                .map((factor) => (
                  <FactorCard key={factor.id} factor={factor} showDetails={true} />
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

const FactorCard: React.FC<{ factor: CalculationFactor; showDetails: boolean }> = ({
  factor,
  showDetails,
}) => {
  const dataSourceBadge = useDataSourceBadge(factor.data_source)

  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <h5 className="font-medium text-gray-900">{factor.factor_name}</h5>
            <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded">
              {dataSourceBadge}
            </span>
          </div>
          {showDetails && (
            <p className="text-sm text-gray-600 mt-1">{factor.explanation_text}</p>
          )}
        </div>
        <div className="text-right ml-4">
          <p className="text-lg font-semibold text-gray-900">
            {factor.amount_eur.toLocaleString('de-DE', { style: 'currency', currency: 'EUR' })}
          </p>
          <p className="text-sm text-gray-500">{factor.impact_percent.toFixed(1)}%</p>
        </div>
      </div>

      {/* Impact percentage bar */}
      <div className="mt-3">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{ width: `${Math.min(factor.impact_percent, 100)}%` }}
          ></div>
        </div>
      </div>
    </div>
  )
}

const TierBreakdownVisualization: React.FC<{
  tierBreakdown: {
    tier1_contribution: number
    tier2_contribution: number
    tier3_contribution: number
    user_history_contribution: number
  }
  totalPrice: number
}> = ({ tierBreakdown, totalPrice }) => {
  const tiers = [
    {
      name: 'TIER 1 - Globaler Standard',
      amount: tierBreakdown.tier1_contribution,
      color: 'bg-green-500',
      description: 'Holzarten, Oberflächen, Komplexität',
    },
    {
      name: 'TIER 2 - Firmenwerte',
      amount: tierBreakdown.tier2_contribution,
      color: 'bg-blue-500',
      description: 'Stundensätze, Gemeinkosten, Gewinnmarge',
    },
    {
      name: 'TIER 3 - Dynamische Anpassung',
      amount: tierBreakdown.tier3_contribution,
      color: 'bg-purple-500',
      description: 'Saisonale Faktoren, Kundenrabatte',
    },
    {
      name: 'Ihre Erfahrung',
      amount: tierBreakdown.user_history_contribution,
      color: 'bg-orange-500',
      description: 'Basierend auf Ihren bisherigen Projekten',
    },
  ]

  return (
    <div className="p-6 border-b border-gray-200">
      <h4 className="text-lg font-semibold text-gray-900 mb-4">TIER-Zusammensetzung</h4>
      <div className="space-y-4">
        {tiers.map((tier) => {
          const percentage = totalPrice > 0 ? (tier.amount / totalPrice) * 100 : 0
          return (
            <div key={tier.name}>
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="text-sm font-medium text-gray-900">{tier.name}</p>
                  <p className="text-xs text-gray-500">{tier.description}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-gray-900">
                    {tier.amount.toLocaleString('de-DE', { style: 'currency', currency: 'EUR' })}
                  </p>
                  <p className="text-xs text-gray-500">{percentage.toFixed(1)}%</p>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`${tier.color} h-3 rounded-full transition-all`}
                  style={{ width: `${Math.min(percentage, 100)}%` }}
                ></div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

const BenchmarkComparison: React.FC<{ explanation: CalculationExplanation }> = ({ explanation }) => {
  const deviationText = useDeviationFormatter(explanation.deviation_from_average_percent)

  if (!explanation.user_average_for_type) {
    return (
      <div className="p-6">
        <h4 className="text-lg font-semibold text-gray-900 mb-2">Benchmark-Vergleich</h4>
        <p className="text-sm text-gray-600">
          Noch keine Vergleichsdaten verfügbar. Führen Sie ähnliche Projekte durch, um Benchmarks zu
          erstellen.
        </p>
      </div>
    )
  }

  return (
    <div className="p-6">
      <h4 className="text-lg font-semibold text-gray-900 mb-4">Vergleich mit Ihren Projekten</h4>
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div>
            <p className="text-xs text-gray-600 mb-1">Aktueller Preis</p>
            <p className="text-lg font-semibold text-gray-900">
              {explanation.total_price_eur.toLocaleString('de-DE', {
                style: 'currency',
                currency: 'EUR',
              })}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">Ihr Durchschnitt</p>
            <p className="text-lg font-semibold text-gray-900">
              {explanation.user_average_for_type.toLocaleString('de-DE', {
                style: 'currency',
                currency: 'EUR',
              })}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">Abweichung</p>
            <p className="text-lg font-semibold text-gray-900">{deviationText}</p>
          </div>
        </div>
        <p className="text-sm text-gray-700">
          Basierend auf {explanation.similar_projects_count}{' '}
          {explanation.similar_projects_count === 1 ? 'ähnlichem Projekt' : 'ähnlichen Projekten'}
        </p>
      </div>
    </div>
  )
}
