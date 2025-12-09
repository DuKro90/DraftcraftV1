/**
 * Benchmark Comparison Component
 *
 * Compares current calculation with user's historical project benchmarks.
 * Displays:
 * - Price comparison (current vs. average)
 * - Deviation percentage with visual indicators
 * - Factors causing the difference
 * - Sample size (number of projects in benchmark)
 */

import React from 'react'
import { useCalculationComparison } from '@/lib/hooks/useTransparency'

interface BenchmarkComparisonProps {
  extractionResultId: string
  className?: string
}

export const BenchmarkComparison: React.FC<BenchmarkComparisonProps> = ({
  extractionResultId,
  className = '',
}) => {
  const { data: comparison, isLoading, error } = useCalculationComparison(extractionResultId)

  if (isLoading) {
    return (
      <div className={`animate-pulse space-y-4 ${className}`}>
        <div className="h-6 bg-gray-200 rounded w-1/2"></div>
        <div className="h-24 bg-gray-200 rounded"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`bg-yellow-50 border border-yellow-200 rounded-lg p-4 ${className}`}>
        <p className="text-yellow-700 text-sm">
          <strong>Benchmark nicht verfügbar:</strong> {error.message}
        </p>
        <p className="text-yellow-600 text-xs mt-2">
          Führen Sie ähnliche Projekte durch, um Vergleichsdaten zu erstellen.
        </p>
      </div>
    )
  }

  if (!comparison) {
    return null
  }

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Vergleich mit Ihren Projekten
      </h3>

      {/* Price Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <PriceCard
          label="Aktueller Preis"
          amount={comparison.current_price_eur}
          color="blue"
        />
        <PriceCard
          label="Ihr Durchschnitt"
          amount={comparison.benchmark_avg_eur}
          color="gray"
        />
        <DeviationCard
          difference={comparison.difference_eur}
          differencePercent={comparison.difference_percent}
          isAboveAverage={comparison.is_above_average}
        />
      </div>

      {/* Explanation */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <p className="text-sm text-blue-900">{comparison.explanation}</p>
        <p className="text-xs text-blue-700 mt-2">
          Basierend auf {comparison.sample_size}{' '}
          {comparison.sample_size === 1 ? 'Projekt' : 'Projekten'}
        </p>
      </div>

      {/* Factors Causing Difference */}
      {comparison.factors_causing_difference.length > 0 && (
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-3">
            Faktoren für die Abweichung
          </h4>
          <div className="space-y-2">
            {comparison.factors_causing_difference.map((factor, index) => (
              <FactorDifferenceCard key={index} factor={factor} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ========================================
// Sub-Components
// ========================================

const PriceCard: React.FC<{
  label: string
  amount: number
  color: 'blue' | 'gray'
}> = ({ label, amount, color }) => {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 text-blue-900',
    gray: 'bg-gray-50 border-gray-200 text-gray-900',
  }

  return (
    <div className={`border rounded-lg p-4 ${colorClasses[color]}`}>
      <p className="text-xs text-gray-600 mb-1">{label}</p>
      <p className="text-2xl font-bold">
        {amount.toLocaleString('de-DE', { style: 'currency', currency: 'EUR' })}
      </p>
    </div>
  )
}

const DeviationCard: React.FC<{
  difference: number
  differencePercent: number
  isAboveAverage: boolean
}> = ({ difference, differencePercent, isAboveAverage }) => {
  const absDifference = Math.abs(difference)
  const absPercent = Math.abs(differencePercent)

  const colorClass = isAboveAverage
    ? 'bg-orange-50 border-orange-200'
    : 'bg-green-50 border-green-200'

  const textColorClass = isAboveAverage ? 'text-orange-900' : 'text-green-900'

  const icon = isAboveAverage ? '↑' : '↓'

  return (
    <div className={`border rounded-lg p-4 ${colorClass}`}>
      <p className="text-xs text-gray-600 mb-1">Abweichung</p>
      <p className={`text-2xl font-bold ${textColorClass}`}>
        {icon} {absPercent.toFixed(1)}%
      </p>
      <p className={`text-sm ${textColorClass}`}>
        {absDifference.toLocaleString('de-DE', { style: 'currency', currency: 'EUR' })}
      </p>
    </div>
  )
}

const FactorDifferenceCard: React.FC<{
  factor: {
    factor: string
    value: string
    impact: string
  }
}> = ({ factor }) => {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-900">{factor.factor}</p>
          <p className="text-xs text-gray-600 mt-1">{factor.value}</p>
        </div>
        <div className="ml-4">
          <span className="px-2 py-1 text-xs font-medium bg-orange-100 text-orange-800 rounded">
            {factor.impact}
          </span>
        </div>
      </div>
    </div>
  )
}
