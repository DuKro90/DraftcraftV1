/**
 * Holzarten Configuration Management Page
 * CRUD interface for wood types (TIER 1)
 */

import React, { useState } from 'react'
import {
  useHolzarten,
  useCreateHolzart,
  useUpdateHolzart,
  useDeleteHolzart,
} from '@/lib/hooks/useConfig'
import type { HolzartKennzahl } from '@/types/api'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { Plus, Edit2, Trash2, Save, X } from 'lucide-react'

export const HolzartenManagement: React.FC = () => {
  const { data: holzarten, isLoading } = useHolzarten()
  const createMutation = useCreateHolzart()
  const updateMutation = useUpdateHolzart()
  const deleteMutation = useDeleteHolzart()

  const [editingId, setEditingId] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [formData, setFormData] = useState<Partial<HolzartKennzahl>>({
    holzart: '',
    kategorie: 'hartholz',
    preis_faktor: 1.0,
    verfuegbarkeit: 'verfuegbar',
    is_enabled: true,
  })

  const handleCreate = () => {
    createMutation.mutate(formData, {
      onSuccess: () => {
        setIsCreating(false)
        setFormData({
          holzart: '',
          kategorie: 'hartholz',
          preis_faktor: 1.0,
          verfuegbarkeit: 'verfuegbar',
          is_enabled: true,
        })
      },
    })
  }

  const handleUpdate = (id: string) => {
    updateMutation.mutate(
      { id, data: formData },
      {
        onSuccess: () => {
          setEditingId(null)
          setFormData({})
        },
      }
    )
  }

  const handleDelete = (id: string) => {
    if (confirm('Holzart wirklich löschen?')) {
      deleteMutation.mutate(id)
    }
  }

  const startEdit = (holzart: HolzartKennzahl) => {
    setEditingId(holzart.id)
    setFormData(holzart)
  }

  const cancelEdit = () => {
    setEditingId(null)
    setIsCreating(false)
    setFormData({
      holzart: '',
      kategorie: 'hartholz',
      preis_faktor: 1.0,
      verfuegbarkeit: 'verfuegbar',
      is_enabled: true,
    })
  }

  if (isLoading) {
    return <LoadingSpinner text="Lade Holzarten..." />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Holzarten-Verwaltung</h1>
          <p className="text-sm text-gray-600 mt-1">
            TIER 1 Konfiguration - Globale Holzart-Standards
          </p>
        </div>
        {!isCreating && (
          <Button
            onClick={() => setIsCreating(true)}
            className="flex items-center gap-2"
          >
            <Plus className="h-5 w-5" />
            Neue Holzart
          </Button>
        )}
      </div>

      {/* Create Form */}
      {isCreating && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Neue Holzart erstellen
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Holzart *
              </label>
              <input
                type="text"
                value={formData.holzart || ''}
                onChange={(e) => setFormData({ ...formData, holzart: e.target.value })}
                placeholder="z.B. Eiche"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Kategorie *
              </label>
              <select
                value={formData.kategorie || 'hartholz'}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    kategorie: e.target.value as 'hartholz' | 'weichholz',
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="hartholz">Hartholz</option>
                <option value="weichholz">Weichholz</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Preisfaktor *
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={formData.preis_faktor || 1.0}
                onChange={(e) =>
                  setFormData({ ...formData, preis_faktor: parseFloat(e.target.value) })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Verfügbarkeit *
              </label>
              <select
                value={formData.verfuegbarkeit || 'verfuegbar'}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    verfuegbarkeit: e.target.value as
                      | 'verfuegbar'
                      | 'begrenzt'
                      | 'auf_anfrage',
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="verfuegbar">Verfügbar</option>
                <option value="begrenzt">Begrenzt</option>
                <option value="auf_anfrage">Auf Anfrage</option>
              </select>
            </div>

            <div className="flex items-center">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_enabled ?? true}
                  onChange={(e) =>
                    setFormData({ ...formData, is_enabled: e.target.checked })
                  }
                  className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Aktiviert</span>
              </label>
            </div>
          </div>

          {createMutation.error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <p className="text-red-800 text-sm">{createMutation.error.message}</p>
            </div>
          )}

          <div className="flex gap-3">
            <Button
              onClick={handleCreate}
              disabled={!formData.holzart || createMutation.isPending}
              className="flex items-center gap-2"
            >
              <Save className="h-4 w-4" />
              {createMutation.isPending ? 'Speichert...' : 'Erstellen'}
            </Button>
            <Button onClick={cancelEdit} variant="secondary" className="flex items-center gap-2">
              <X className="h-4 w-4" />
              Abbrechen
            </Button>
          </div>
        </Card>
      )}

      {/* Holzarten Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b">
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                  Holzart
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                  Kategorie
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                  Preisfaktor
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                  Verfügbarkeit
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase">
                  Aktionen
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {holzarten?.map((holzart) => {
                const isEditing = editingId === holzart.id

                return (
                  <tr key={holzart.id} className="hover:bg-gray-50">
                    {isEditing ? (
                      <>
                        <td className="px-6 py-4">
                          <input
                            type="text"
                            value={formData.holzart || ''}
                            onChange={(e) =>
                              setFormData({ ...formData, holzart: e.target.value })
                            }
                            className="w-full px-3 py-1 border border-gray-300 rounded"
                          />
                        </td>
                        <td className="px-6 py-4">
                          <select
                            value={formData.kategorie || 'hartholz'}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                kategorie: e.target.value as 'hartholz' | 'weichholz',
                              })
                            }
                            className="w-full px-3 py-1 border border-gray-300 rounded"
                          >
                            <option value="hartholz">Hartholz</option>
                            <option value="weichholz">Weichholz</option>
                          </select>
                        </td>
                        <td className="px-6 py-4">
                          <input
                            type="number"
                            step="0.01"
                            value={formData.preis_faktor || 1.0}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                preis_faktor: parseFloat(e.target.value),
                              })
                            }
                            className="w-full px-3 py-1 border border-gray-300 rounded"
                          />
                        </td>
                        <td className="px-6 py-4">
                          <select
                            value={formData.verfuegbarkeit || 'verfuegbar'}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                verfuegbarkeit: e.target.value as any,
                              })
                            }
                            className="w-full px-3 py-1 border border-gray-300 rounded"
                          >
                            <option value="verfuegbar">Verfügbar</option>
                            <option value="begrenzt">Begrenzt</option>
                            <option value="auf_anfrage">Auf Anfrage</option>
                          </select>
                        </td>
                        <td className="px-6 py-4">
                          <input
                            type="checkbox"
                            checked={formData.is_enabled ?? true}
                            onChange={(e) =>
                              setFormData({ ...formData, is_enabled: e.target.checked })
                            }
                            className="w-4 h-4 text-blue-600 rounded"
                          />
                        </td>
                        <td className="px-6 py-4 text-right space-x-2">
                          <button
                            onClick={() => handleUpdate(holzart.id)}
                            disabled={updateMutation.isPending}
                            className="text-green-600 hover:text-green-800 p-1"
                          >
                            <Save className="h-5 w-5" />
                          </button>
                          <button
                            onClick={cancelEdit}
                            className="text-gray-600 hover:text-gray-800 p-1"
                          >
                            <X className="h-5 w-5" />
                          </button>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="px-6 py-4 font-medium text-gray-900">
                          {holzart.holzart}
                        </td>
                        <td className="px-6 py-4 text-gray-700">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {holzart.kategorie}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-gray-700">
                          ×{holzart.preis_faktor.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 text-gray-700">
                          {holzart.verfuegbarkeit}
                        </td>
                        <td className="px-6 py-4">
                          {holzart.is_enabled ? (
                            <span className="text-green-600 text-sm">Aktiv</span>
                          ) : (
                            <span className="text-gray-400 text-sm">Inaktiv</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right space-x-2">
                          <button
                            onClick={() => startEdit(holzart)}
                            className="text-blue-600 hover:text-blue-800 p-1"
                          >
                            <Edit2 className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => handleDelete(holzart.id)}
                            disabled={deleteMutation.isPending}
                            className="text-red-600 hover:text-red-800 p-1"
                          >
                            <Trash2 className="h-5 w-5" />
                          </button>
                        </td>
                      </>
                    )}
                  </tr>
                )
              })}
            </tbody>
          </table>

          {holzarten?.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500">Keine Holzarten konfiguriert</p>
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}
