/**
 * Calculation Feedback Component
 *
 * Allows users to provide feedback on calculation accuracy for ML improvement.
 * Implements German Handwerk feedback flow:
 * - Feedback type selection (zu_hoch, zu_niedrig, genau_richtig, etc.)
 * - Expected price input (optional)
 * - Comments field for detailed feedback
 * - Factor rating (optional, for advanced users)
 */

import React, { useState } from 'react'
import { useSubmitCalculationFeedback } from '@/lib/hooks/useTransparency'
import type { FeedbackType, CalculationFeedback as FeedbackData } from '@/types/api'

interface CalculationFeedbackProps {
  extractionResultId: string
  calculationId?: string
  currentPrice: number
  onFeedbackSubmitted?: () => void
  className?: string
}

export const CalculationFeedback: React.FC<CalculationFeedbackProps> = ({
  extractionResultId,
  calculationId,
  currentPrice,
  onFeedbackSubmitted,
  className = '',
}) => {
  const [feedbackType, setFeedbackType] = useState<FeedbackType | ''>('')
  const [erwarteterPreis, setErwarteterPreis] = useState<string>('')
  const [kommentare, setKommentare] = useState<string>('')
  const [showSuccess, setShowSuccess] = useState(false)

  const { mutate: submitFeedback, isPending, error } = useSubmitCalculationFeedback()

  const feedbackOptions: Array<{ value: FeedbackType; label: string; icon: string }> = [
    { value: 'zu_hoch', label: 'Preis zu hoch', icon: '⬆️' },
    { value: 'zu_niedrig', label: 'Preis zu niedrig', icon: '⬇️' },
    { value: 'genau_richtig', label: 'Preis genau richtig', icon: '✅' },
    { value: 'faktor_fehlt', label: 'Wichtiger Faktor fehlt', icon: '❓' },
    { value: 'faktor_falsch', label: 'Faktor falsch angewendet', icon: '⚠️' },
    { value: 'sonstiges', label: 'Sonstiges Feedback', icon: '💬' },
  ]

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!feedbackType) {
      return
    }

    const feedbackData: FeedbackData = {
      extraction_result_id: extractionResultId,
      calculation_id: calculationId,
      feedback_type: feedbackType,
      erwarteter_preis_eur: erwarteterPreis ? parseFloat(erwarteterPreis) : undefined,
      kommentare: kommentare || undefined,
    }

    submitFeedback(feedbackData, {
      onSuccess: () => {
        setShowSuccess(true)
        // Reset form
        setFeedbackType('')
        setErwarteterPreis('')
        setKommentare('')

        // Hide success message after 3 seconds
        setTimeout(() => setShowSuccess(false), 3000)

        // Notify parent
        onFeedbackSubmitted?.()
      },
    })
  }

  const isFormValid = feedbackType !== ''

  return (
    <div className={`bg-white rounded-lg shadow-md ${className}`}>
      <div className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Feedback zur Kalkulation
        </h3>
        <p className="text-sm text-gray-600 mb-6">
          Helfen Sie uns, die Kalkulationsgenauigkeit zu verbessern. Ihr Feedback wird für
          maschinelles Lernen verwendet.
        </p>

        {/* Success Message */}
        {showSuccess && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-green-800 text-sm font-medium">
              ✓ Feedback erfolgreich gespeichert. Vielen Dank!
            </p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800 text-sm font-medium">
              Fehler beim Speichern: {error.message}
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Feedback Type Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Wie bewerten Sie diese Kalkulation? *
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {feedbackOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setFeedbackType(option.value)}
                  className={`p-4 text-left rounded-lg border-2 transition-all ${
                    feedbackType === option.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  }`}
                >
                  <div className="text-2xl mb-1">{option.icon}</div>
                  <div className="text-sm font-medium text-gray-900">{option.label}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Expected Price (optional, shown if price is wrong) */}
          {(feedbackType === 'zu_hoch' || feedbackType === 'zu_niedrig') && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Erwarteter Preis (optional)
              </label>
              <div className="relative">
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={erwarteterPreis}
                  onChange={(e) => setErwarteterPreis(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="z.B. 3500.00"
                />
                <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                  <span className="text-gray-500">€</span>
                </div>
              </div>
              {currentPrice > 0 && erwarteterPreis && (
                <p className="text-xs text-gray-500 mt-2">
                  Differenz: {(parseFloat(erwarteterPreis) - currentPrice).toFixed(2)} € (
                  {(((parseFloat(erwarteterPreis) - currentPrice) / currentPrice) * 100).toFixed(1)}
                  %)
                </p>
              )}
            </div>
          )}

          {/* Comments */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Zusätzliche Kommentare (optional)
            </label>
            <textarea
              value={kommentare}
              onChange={(e) => setKommentare(e.target.value)}
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder="z.B. 'Materialkosten scheinen zu hoch', 'Zeitaufwand wurde unterschätzt', etc."
            />
            <p className="text-xs text-gray-500 mt-1">{kommentare.length} / 500 Zeichen</p>
          </div>

          {/* Submit Button */}
          <div className="flex items-center justify-between">
            <p className="text-xs text-gray-500">* Pflichtfeld</p>
            <button
              type="submit"
              disabled={!isFormValid || isPending}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                isFormValid && !isPending
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {isPending ? 'Wird gespeichert...' : 'Feedback absenden'}
            </button>
          </div>
        </form>
      </div>

      {/* Privacy Notice */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 rounded-b-lg">
        <p className="text-xs text-gray-600">
          🔒 Ihr Feedback wird anonymisiert gespeichert und ausschließlich zur Verbesserung der
          Kalkulationsalgorithmen verwendet. Weitere Informationen finden Sie in unserer{' '}
          <a href="/datenschutz" className="text-blue-600 hover:underline">
            Datenschutzerklärung
          </a>
          .
        </p>
      </div>
    </div>
  )
}
