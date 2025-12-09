/**
 * FormField component with contextual help (inspired by Django Admin tooltips)
 */

import { ReactNode } from 'react'
import { cn } from '@/lib/utils/cn'

interface FormFieldProps {
  label: string
  helpText?: string
  tier?: 'tier1' | 'tier2' | 'tier3' | 'critical' | 'dsgvo'
  icon?: '💡' | '✓' | '⚠'
  error?: string
  required?: boolean
  children: ReactNode
}

export default function FormField({
  label,
  helpText,
  tier = 'tier1',
  icon,
  error,
  required,
  children,
}: FormFieldProps) {
  const tierColors = {
    tier1: 'border-l-tier1',      // Global standards (blue)
    tier2: 'border-l-tier2',      // Company metrics (orange)
    tier3: 'border-l-tier3',      // Dynamic adjustments (purple)
    critical: 'border-l-critical', // Critical fields (red)
    dsgvo: 'border-l-dsgvo',      // DSGVO compliance (green)
  }

  const tierBg = {
    tier1: 'bg-blue-50',
    tier2: 'bg-orange-50',
    tier3: 'bg-purple-50',
    critical: 'bg-red-50',
    dsgvo: 'bg-green-50',
  }

  return (
    <div className="mb-4">
      <label className="block font-semibold text-gray-700 mb-1">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>

      {children}

      {helpText && (
        <div
          className={cn(
            'mt-2 p-3 border-l-4 rounded text-sm text-gray-600 transition-colors hover:bg-opacity-70',
            tierColors[tier],
            tierBg[tier],
            icon && 'pl-10 relative'
          )}
        >
          {icon && (
            <span className="absolute left-3 top-3 text-base">{icon}</span>
          )}
          {helpText}
        </div>
      )}

      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  )
}
