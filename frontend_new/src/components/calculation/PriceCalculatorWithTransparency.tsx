/**
 * Price Calculator Component with Transparency Integration (Phase 4A + 4B)
 *
 * Enhanced version with:
 * - Calculation explanation viewer
 * - Benchmark comparison
 * - Feedback submission
 * - Progressive disclosure (expandable sections)
 */

import React, { useState } from 'react'
import { useCalculatePrice } from '@/lib/hooks/useCalculation'
import { useHolzarten, useOberflaechen, useKomplexitaeten } from '@/lib/hooks/useConfig'
import { CalculationExplanationViewer } from '@/components/transparency/CalculationExplanationViewer'
import { BenchmarkComparison } from '@/components/transparency/BenchmarkComparison'
import { CalculationFeedback } from '@/components/transparency/CalculationFeedback'
import { Calculator, Info, TrendingUp, MessageSquare, ChevronDown, ChevronUp } from 'lucide-react'

interface CalculationResult {
  calculation_id: string // For transparency linking
  extraction_result_id: string // For benchmark comparison
  final_price: number
  base_price: number
  factors_applied: Array<{
    name: string
    value: number
    impact: number
  }>
  tier_breakdown: {
    tier1_contribution: number
    tier2_contribution: number
    tier3_contribution: number
  }
}

export const PriceCalculatorWithTransparency: React.FC = () => {
  const [formData, setFormData] = useState({
    holzart_id: '',
    oberflaeche_id: '',
    komplexitaet_id: '',
    base_amount: '',
    quantity: '',
  })

  const [result, setResult] = useState<CalculationResult | null>(null)
  const [expandedSections, setExpandedSections] = useState({
    explanation: false,
    benchmark: false,
    feedback: false,
  })

  // Fetch configuration data
  const { data: holzarten, isLoading: loadingHolzarten } = useHolzarten()
  const { data: oberflaechen, isLoading: loadingOberflaechen } = useOberflaechen()
  const { data: komplexitaeten, isLoading: loadingKomplexitaeten } = useKomplexitaeten()

  // Calculation mutation
  const { mutate: calculate, isPending, error } = useCalculatePrice()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    calculate(
      {
        holzart_id: formData.holzart_id,
        oberflaeche_id: formData.oberflaeche_id,
        komplexitaet_id: formData.komplexitaet_id,
        base_amount: parseFloat(formData.base_amount),
        quantity: parseFloat(formData.quantity),
      },
      {
        onSuccess: (data) => {
          setResult(data)
          // Auto-expand explanation section on first calculation
          if (!expandedSections.explanation) {
            setExpandedSections((prev) => ({ ...prev, explanation: true }))
          }
        },
      }
    )
  }

  const handleReset = () => {
    setFormData({
      holzart_id: '',
      oberflaeche_id: '',
      komplexitaet_id: '',
      base_amount: '',
      quantity: '',
    })
    setResult(null)
    setExpandedSections({
      explanation: false,
      benchmark: false,
      feedback: false,
    })
  }

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }))
  }

  const isFormValid =
    formData.holzart_id &&
    formData.oberflaeche_id &&
    formData.komplexitaet_id &&
    formData.base_amount &&
    formData.quantity

  const isLoading = loadingHolzarten || loadingOberflaechen || loadingKomplexitaeten

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Lade Konfigurationsdaten...</p>
        </div>
      </div>
    )
  }

  // Filter enabled options
  const enabledHolzarten = holzarten?.filter((h) => h.is_enabled) || []
  const enabledOberflaechen = oberflaechen?.filter((o) => o.is_enabled) || []
  const enabledKomplexitaeten = komplexitaeten?.filter((k) => k.is_enabled) || []

  return (
    <div className="space-y-6 max-w-6xl mx-auto p-6">
      {/* Form Card */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center gap-3 mb-6">
          <Calculator className="h-6 w-6 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900">Preiskalkulation mit Transparenz</h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Holzart */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Holzart *</label>
            <select
              value={formData.holzart_id}
              onChange={(e) => setFormData({ ...formData, holzart_id: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Holzart wählen...</option>
              {enabledHolzarten.map((holzart) => (
                <option key={holzart.id} value={holzart.id}>
                  {holzart.holzart} ({holzart.kategorie}) - Faktor: {holzart.preis_faktor}x
                </option>
              ))}
            </select>
          </div>

          {/* Oberflächenbearbeitung */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Oberflächenbearbeitung *
            </label>
            <select
              value={formData.oberflaeche_id}
              onChange={(e) => setFormData({ ...formData, oberflaeche_id: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Oberfläche wählen...</option>
              {enabledOberflaechen.map((oberflaeche) => (
                <option key={oberflaeche.id} value={oberflaeche.id}>
                  {oberflaeche.typ} - Faktor: {oberflaeche.preis_faktor}x
                </option>
              ))}
            </select>
          </div>

          {/* Komplexität */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Komplexität *</label>
            <select
              value={formData.komplexitaet_id}
              onChange={(e) => setFormData({ ...formData, komplexitaet_id: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Komplexität wählen...</option>
              {enabledKomplexitaeten.map((komplexitaet) => (
                <option key={komplexitaet.id} value={komplexitaet.id}>
                  {komplexitaet.komplexitaet_typ} - Faktor: {komplexitaet.preis_faktor}x
                </option>
              ))}
            </select>
          </div>

          {/* Base Amount & Quantity */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Grundbetrag (€) *</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={formData.base_amount}
                onChange={(e) => setFormData({ ...formData, base_amount: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="z.B. 1000.00"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Menge *</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={formData.quantity}
                onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="z.B. 5"
                required
              />
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-700 text-sm">{error.message}</p>
            </div>
          )}

          {/* Buttons */}
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={!isFormValid || isPending}
              className={`flex-1 py-3 rounded-lg font-medium transition-colors ${
                isFormValid && !isPending
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {isPending ? 'Berechnet...' : 'Preis berechnen'}
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition-colors"
            >
              Zurücksetzen
            </button>
          </div>
        </form>
      </div>

      {/* Results Section */}
      {result && (
        <>
          {/* Main Result Card */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Berechnungsergebnis</h3>

            {/* Final Price */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
              <div className="text-sm text-green-700 mb-1">Endpreis</div>
              <div className="text-4xl font-bold text-green-900">
                {result.final_price.toLocaleString('de-DE', {
                  style: 'currency',
                  currency: 'EUR',
                })}
              </div>
              <div className="text-sm text-green-600 mt-2">
                Basispreis: {result.base_price.toLocaleString('de-DE', { style: 'currency', currency: 'EUR' })}
              </div>
            </div>

            {/* Factors Applied */}
            <div className="mb-6">
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Info className="h-5 w-5 text-blue-600" />
                Angewandte Faktoren
              </h4>
              <div className="space-y-2">
                {result.factors_applied.map((factor, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <span className="text-gray-700">{factor.name}</span>
                    <div className="text-right">
                      <div className="font-semibold text-gray-900">{factor.value.toFixed(2)}x</div>
                      <div className="text-sm text-gray-600">Auswirkung: {factor.impact.toFixed(1)}%</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* TIER Breakdown */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">TIER-Aufschlüsselung</h4>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="text-xs text-blue-700 mb-1">TIER 1 (Global)</div>
                  <div className="text-xl font-bold text-blue-900">
                    {result.tier_breakdown.tier1_contribution.toLocaleString('de-DE', {
                      style: 'currency',
                      currency: 'EUR',
                    })}
                  </div>
                </div>

                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <div className="text-xs text-purple-700 mb-1">TIER 2 (Betrieb)</div>
                  <div className="text-xl font-bold text-purple-900">
                    {result.tier_breakdown.tier2_contribution.toLocaleString('de-DE', {
                      style: 'currency',
                      currency: 'EUR',
                    })}
                  </div>
                </div>

                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                  <div className="text-xs text-orange-700 mb-1">TIER 3 (Dynamisch)</div>
                  <div className="text-xl font-bold text-orange-900">
                    {result.tier_breakdown.tier3_contribution.toLocaleString('de-DE', {
                      style: 'currency',
                      currency: 'EUR',
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Transparency Sections (Expandable) */}

          {/* 1. Calculation Explanation */}
          <ExpandableSection
            title="Detaillierte Erklärung"
            icon={<Info className="h-5 w-5" />}
            isExpanded={expandedSections.explanation}
            onToggle={() => toggleSection('explanation')}
          >
            {result.calculation_id && (
              <CalculationExplanationViewer calculationId={result.calculation_id} />
            )}
          </ExpandableSection>

          {/* 2. Benchmark Comparison */}
          <ExpandableSection
            title="Vergleich mit Ihren Projekten"
            icon={<TrendingUp className="h-5 w-5" />}
            isExpanded={expandedSections.benchmark}
            onToggle={() => toggleSection('benchmark')}
          >
            {result.extraction_result_id && (
              <BenchmarkComparison extractionResultId={result.extraction_result_id} />
            )}
          </ExpandableSection>

          {/* 3. Feedback */}
          <ExpandableSection
            title="Feedback zur Kalkulation"
            icon={<MessageSquare className="h-5 w-5" />}
            isExpanded={expandedSections.feedback}
            onToggle={() => toggleSection('feedback')}
          >
            <CalculationFeedback
              extractionResultId={result.extraction_result_id}
              calculationId={result.calculation_id}
              currentPrice={result.final_price}
              onFeedbackSubmitted={() => {
                // Optionally collapse section after submission
                setExpandedSections((prev) => ({ ...prev, feedback: false }))
              }}
            />
          </ExpandableSection>
        </>
      )}
    </div>
  )
}

// ========================================
// Expandable Section Component
// ========================================

const ExpandableSection: React.FC<{
  title: string
  icon: React.ReactNode
  isExpanded: boolean
  onToggle: () => void
  children: React.ReactNode
}> = ({ title, icon, isExpanded, onToggle, children }) => {
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full px-6 py-4 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="text-blue-600">{icon}</div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        <div className="text-gray-500">
          {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
        </div>
      </button>

      {isExpanded && <div className="p-6">{children}</div>}
    </div>
  )
}
