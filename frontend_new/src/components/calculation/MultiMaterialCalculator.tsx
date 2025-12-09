/**
 * Multi-Material Calculator Component (Phase 4B)
 * Calculate pricing for multiple materials at once
 */

import React, { useState } from 'react'
import { useCalculateMultiMaterial } from '@/lib/hooks/useCalculation'
import { useHolzarten, useOberflaechen, useKomplexitaeten } from '@/lib/hooks/useConfig'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import FormField from '@/components/ui/FormField'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { Plus, Trash2, Calculator } from 'lucide-react'

interface MaterialInput {
  id: string
  holzart_id: string
  oberflaeche_id: string
  komplexitaet_id: string
  base_amount: string
  quantity: string
}

interface CalculationResult {
  total_price: number
  materials: Array<{
    material_index: number
    price: number
    factors_applied: any[]
  }>
}

export const MultiMaterialCalculator: React.FC = () => {
  const [materials, setMaterials] = useState<MaterialInput[]>([
    {
      id: crypto.randomUUID(),
      holzart_id: '',
      oberflaeche_id: '',
      komplexitaet_id: '',
      base_amount: '',
      quantity: '',
    },
  ])

  const [result, setResult] = useState<CalculationResult | null>(null)

  // Fetch configuration data
  const { data: holzarten, isLoading: loadingHolzarten } = useHolzarten()
  const { data: oberflaechen, isLoading: loadingOberflaechen } = useOberflaechen()
  const { data: komplexitaeten, isLoading: loadingKomplexitaeten } = useKomplexitaeten()

  // Calculation mutation
  const { mutate: calculate, isPending, error } = useCalculateMultiMaterial()

  const addMaterial = () => {
    setMaterials([
      ...materials,
      {
        id: crypto.randomUUID(),
        holzart_id: '',
        oberflaeche_id: '',
        komplexitaet_id: '',
        base_amount: '',
        quantity: '',
      },
    ])
  }

  const removeMaterial = (id: string) => {
    if (materials.length > 1) {
      setMaterials(materials.filter((m) => m.id !== id))
    }
  }

  const updateMaterial = (id: string, field: keyof MaterialInput, value: string) => {
    setMaterials(
      materials.map((m) => (m.id === id ? { ...m, [field]: value } : m))
    )
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const materialsData = materials.map((m) => ({
      holzart_id: m.holzart_id,
      oberflaeche_id: m.oberflaeche_id,
      komplexitaet_id: m.komplexitaet_id,
      base_amount: parseFloat(m.base_amount),
      quantity: parseFloat(m.quantity),
    }))

    calculate(
      { materials: materialsData },
      {
        onSuccess: (data) => {
          setResult(data)
        },
      }
    )
  }

  const handleReset = () => {
    setMaterials([
      {
        id: crypto.randomUUID(),
        holzart_id: '',
        oberflaeche_id: '',
        komplexitaet_id: '',
        base_amount: '',
        quantity: '',
      },
    ])
    setResult(null)
  }

  const isFormValid = materials.every(
    (m) =>
      m.holzart_id &&
      m.oberflaeche_id &&
      m.komplexitaet_id &&
      m.base_amount &&
      m.quantity
  )

  if (loadingHolzarten || loadingOberflaechen || loadingKomplexitaeten) {
    return <LoadingSpinner text="Lade Konfigurationsdaten..." />
  }

  return (
    <div className="space-y-6">
      {/* Form */}
      <Card>
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Calculator className="h-6 w-6 text-purple-600" />
            <h2 className="text-2xl font-bold text-gray-900">
              Multi-Material Kalkulation
            </h2>
          </div>
          <Button onClick={addMaterial} size="sm" className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Material hinzufügen
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Materials */}
          <div className="space-y-6">
            {materials.map((material, index) => (
              <div
                key={material.id}
                className="p-6 bg-gray-50 rounded-lg border border-gray-200 space-y-4"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Material {index + 1}
                  </h3>
                  {materials.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeMaterial(material.id)}
                      className="text-red-600 hover:text-red-800 p-2"
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Holzart */}
                  <FormField label="Holzart" required>
                    <select
                      value={material.holzart_id}
                      onChange={(e) =>
                        updateMaterial(material.id, 'holzart_id', e.target.value)
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                      required
                    >
                      <option value="">-- Holzart --</option>
                      {holzarten
                        ?.filter((h) => h.is_enabled)
                        .map((h) => (
                          <option key={h.id} value={h.id}>
                            {h.holzart} (×{h.preis_faktor})
                          </option>
                        ))}
                    </select>
                  </FormField>

                  {/* Oberfläche */}
                  <FormField label="Oberfläche" required>
                    <select
                      value={material.oberflaeche_id}
                      onChange={(e) =>
                        updateMaterial(material.id, 'oberflaeche_id', e.target.value)
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                      required
                    >
                      <option value="">-- Oberfläche --</option>
                      {oberflaechen
                        ?.filter((o) => o.is_enabled)
                        .map((o) => (
                          <option key={o.id} value={o.id}>
                            {o.typ} (×{o.preis_faktor})
                          </option>
                        ))}
                    </select>
                  </FormField>

                  {/* Komplexität */}
                  <FormField label="Komplexität" required>
                    <select
                      value={material.komplexitaet_id}
                      onChange={(e) =>
                        updateMaterial(material.id, 'komplexitaet_id', e.target.value)
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                      required
                    >
                      <option value="">-- Komplexität --</option>
                      {komplexitaeten
                        ?.filter((k) => k.is_enabled)
                        .map((k) => (
                          <option key={k.id} value={k.id}>
                            {k.komplexitaet_typ} (×{k.preis_faktor})
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
                      value={material.base_amount}
                      onChange={(e) =>
                        updateMaterial(material.id, 'base_amount', e.target.value)
                      }
                      placeholder="1000.00"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                      required
                    />
                  </FormField>

                  {/* Quantity */}
                  <FormField label="Menge" required>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={material.quantity}
                      onChange={(e) =>
                        updateMaterial(material.id, 'quantity', e.target.value)
                      }
                      placeholder="5"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                      required
                    />
                  </FormField>
                </div>
              </div>
            ))}
          </div>

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
              {isPending ? 'Berechne...' : 'Gesamtpreis berechnen'}
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
          <h3 className="text-xl font-bold text-gray-900 mb-6">
            Multi-Material Ergebnis
          </h3>

          {/* Total Price */}
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-6 mb-6">
            <div className="text-sm text-purple-700 mb-1">Gesamtpreis</div>
            <div className="text-4xl font-bold text-purple-900">
              {result.total_price.toLocaleString('de-DE', {
                style: 'currency',
                currency: 'EUR',
              })}
            </div>
            <div className="text-sm text-purple-600 mt-2">
              {result.materials.length} Material{result.materials.length !== 1 && 'ien'}
            </div>
          </div>

          {/* Individual Materials */}
          <div className="space-y-3">
            <h4 className="font-semibold text-gray-900">Einzelpreise</h4>
            {result.materials.map((material) => (
              <div
                key={material.material_index}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <span className="text-gray-700 font-medium">
                  Material {material.material_index + 1}
                </span>
                <span className="text-xl font-bold text-gray-900">
                  {material.price.toLocaleString('de-DE', {
                    style: 'currency',
                    currency: 'EUR',
                  })}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
