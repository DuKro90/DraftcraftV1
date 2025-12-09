/**
 * Price Calculator Component (Phase 4B)
 * Single material price calculation with TIER breakdown
 */

import React, { useState } from 'react'
import { useCalculatePrice } from '@/lib/hooks/useCalculation'
import { useHolzarten, useOberflaechen, useKomplexitaeten } from '@/lib/hooks/useConfig'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import FormField from '@/components/ui/FormField'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { Calculator, Info } from 'lucide-react'

interface CalculationResult {
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

export const PriceCalculator: React.FC = () => {
  const [formData, setFormData] = useState({
    holzart_id: '',
    oberflaeche_id: '',
    komplexitaet_id: '',
    base_amount: '',
    quantity: '',
  })

  const [result, setResult] = useState<CalculationResult | null>(null)

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
  }

  const isFormValid =
    formData.holzart_id &&
    formData.oberflaeche_id &&
    formData.komplexitaet_id &&
    formData.base_amount &&
    formData.quantity

  if (loadingHolzarten || loadingOberflaechen || loadingKomplexitaeten) {
    return <LoadingSpinner text="Lade Konfigurationsdaten..." />
  }

  return (
    <div className="space-y-6">
      {/* Form */}
      <Card>
        <div className="flex items-center gap-3 mb-6">
          <Calculator className="h-6 w-6 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900">Preiskalkulation</h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Holzart */}
          <FormField label="Holzart" required>
            <select
              value={formData.holzart_id}
              onChange={(e) => setFormData({ ...formData, holzart_id: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="">-- Holzart auswählen --</option>
              {holzarten?.map((h) => (
                <option key={h.id} value={h.id} disabled={!h.is_enabled}>
                  {h.holzart} ({h.kategorie}) - Faktor: {h.preis_faktor}
                  {!h.is_enabled && ' (deaktiviert)'}
                </option>
              ))}
            </select>
          </FormField>

          {/* Oberflächenbearbeitung */}
          <FormField label="Oberflächenbearbeitung" required>
            <select
              value={formData.oberflaeche_id}
              onChange={(e) => setFormData({ ...formData, oberflaeche_id: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="">-- Oberfläche auswählen --</option>
              {oberflaechen?.map((o) => (
                <option key={o.id} value={o.id} disabled={!o.is_enabled}>
                  {o.typ} - Faktor: {o.preis_faktor}, +{o.zusatzkosten_pro_qm}€/m²
                  {!o.is_enabled && ' (deaktiviert)'}
                </option>
              ))}
            </select>
          </FormField>

          {/* Komplexität */}
          <FormField label="Komplexität" required>
            <select
              value={formData.komplexitaet_id}
              onChange={(e) =>
                setFormData({ ...formData, komplexitaet_id: e.target.value })
              }
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="">-- Komplexität auswählen --</option>
              {komplexitaeten?.map((k) => (
                <option key={k.id} value={k.id} disabled={!k.is_enabled}>
                  {k.komplexitaet_typ} - Zeit: {k.zeit_faktor}x, Preis: {k.preis_faktor}x
                  {!k.is_enabled && ' (deaktiviert)'}
                </option>
              ))}
            </select>
          </FormField>

          {/* Base Amount */}
          <FormField label="Basisbetrag (€)" required>
            <input
              type="number"
              step="0.01"
              min="0"
              value={formData.base_amount}
              onChange={(e) => setFormData({ ...formData, base_amount: e.target.value })}
              placeholder="z.B. 1000.00"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </FormField>

          {/* Quantity */}
          <FormField label="Menge" required>
            <input
              type="number"
              step="0.01"
              min="0"
              value={formData.quantity}
              onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
              placeholder="z.B. 5"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </FormField>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800 text-sm">
                <strong>Fehler:</strong> {error.message}
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <Button type="submit" disabled={!isFormValid || isPending} className="flex-1">
              {isPending ? 'Berechne...' : 'Preis berechnen'}
            </Button>
            <Button type="button" onClick={handleReset} variant="secondary">
              Zurücksetzen
            </Button>
          </div>
        </form>
      </Card>

      {/* Results */}
      {result && (
        <Card>
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
                    <div className="font-semibold text-gray-900">
                      {factor.value.toFixed(2)}x
                    </div>
                    <div className="text-sm text-gray-600">
                      Auswirkung: {factor.impact.toFixed(1)}%
                    </div>
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
        </Card>
      )}
    </div>
  )
}
