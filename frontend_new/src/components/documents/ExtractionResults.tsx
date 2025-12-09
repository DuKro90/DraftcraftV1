/**
 * Extraction Results Display Component
 * Shows OCR confidence, entity count, and extracted data
 */

import { CheckCircle, AlertCircle, Clock } from 'lucide-react'
import type { ExtractionSummary } from '@/types/api'
import { formatPercentage, formatRelativeTime } from '@/lib/utils/formatters'

interface ExtractionResultsProps {
  data: ExtractionSummary
}

export default function ExtractionResults({ data }: ExtractionResultsProps) {
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.92) return 'text-green-600 bg-green-50'
    if (confidence >= 0.80) return 'text-blue-600 bg-blue-50'
    if (confidence >= 0.70) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.92) return 'Ausgezeichnet'
    if (confidence >= 0.80) return 'Gut'
    if (confidence >= 0.70) return 'Akzeptabel'
    return 'Benötigt Überprüfung'
  }

  const getRoutingTierBadge = (tier?: string) => {
    if (!tier) return null

    const styles = {
      AUTO_ACCEPT: 'bg-green-100 text-green-800',
      AGENT_VERIFY: 'bg-blue-100 text-blue-800',
      AGENT_EXTRACT: 'bg-yellow-100 text-yellow-800',
      HUMAN_REVIEW: 'bg-red-100 text-red-800',
    }

    const labels = {
      AUTO_ACCEPT: 'Auto-Akzeptiert',
      AGENT_VERIFY: 'Agent-Verifizierung',
      AGENT_EXTRACT: 'Agent-Extraktion',
      HUMAN_REVIEW: 'Manuelle Prüfung',
    }

    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${styles[tier as keyof typeof styles]}`}>
        {labels[tier as keyof typeof labels]}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Status Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* OCR Confidence */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="h-5 w-5 text-gray-500" />
            <h3 className="font-semibold text-gray-700">OCR Vertrauen</h3>
          </div>
          <div className="flex items-baseline gap-2">
            <p className={`text-3xl font-bold ${getConfidenceColor(data.ocr_confidence)}`}>
              {formatPercentage(data.ocr_confidence, 1)}
            </p>
            <p className="text-sm text-gray-500">{getConfidenceLabel(data.ocr_confidence)}</p>
          </div>
          {data.routing_tier && (
            <div className="mt-2">{getRoutingTierBadge(data.routing_tier)}</div>
          )}
        </div>

        {/* Entity Count */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="h-5 w-5 text-gray-500" />
            <h3 className="font-semibold text-gray-700">Entitäten</h3>
          </div>
          <p className="text-3xl font-bold text-gray-900">{data.entity_count}</p>
          <p className="text-sm text-gray-500">{data.materials_found} Materialien</p>
        </div>

        {/* Processing Time */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="h-5 w-5 text-gray-500" />
            <h3 className="font-semibold text-gray-700">Verarbeitung</h3>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {(data.processing_time_ms / 1000).toFixed(1)}s
          </p>
          <p className="text-sm text-gray-500">{formatRelativeTime(data.extracted_at)}</p>
        </div>
      </div>

      {/* Confidence Progress Bar */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-gray-700">Vertrauensgrad</h3>
          <span className="text-sm text-gray-500">
            {formatPercentage(data.ocr_confidence, 1)}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all ${
              data.ocr_confidence >= 0.92
                ? 'bg-green-500'
                : data.ocr_confidence >= 0.80
                ? 'bg-blue-500'
                : data.ocr_confidence >= 0.70
                ? 'bg-yellow-500'
                : 'bg-red-500'
            }`}
            style={{ width: `${data.ocr_confidence * 100}%` }}
          />
        </div>
      </div>

      {/* Entity Types Breakdown */}
      {Object.keys(data.entity_types).length > 0 && (
        <div>
          <h3 className="font-semibold text-gray-700 mb-3">Erkannte Datentypen</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {Object.entries(data.entity_types).map(([type, count]) => (
              <div
                key={type}
                className="flex items-center justify-between p-2 bg-white rounded border border-gray-200"
              >
                <span className="text-sm text-gray-600">{type}</span>
                <span className="text-sm font-semibold text-brand-600">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Extracted Entities Preview */}
      {data.entities && data.entities.length > 0 && (
        <div>
          <h3 className="font-semibold text-gray-700 mb-3">
            Extrahierte Daten (Top {Math.min(5, data.entities.length)})
          </h3>
          <div className="space-y-2">
            {data.entities.slice(0, 5).map((entity, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-3 bg-white rounded border border-gray-200"
              >
                <span className="px-2 py-1 bg-tier1 text-white text-xs rounded font-medium">
                  {entity.entity_type}
                </span>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{entity.value}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Vertrauen: {formatPercentage(entity.confidence, 1)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
