/**
 * Proposal Generation Form Component
 * With smart defaults from extraction data
 */

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMemo } from 'react'
import type { ExtractionSummary } from '@/types/api'
import FormField from '@/components/ui/FormField'
import Input from '@/components/ui/Input'
import Button from '@/components/ui/Button'

const proposalSchema = z.object({
  customer_name: z.string().min(2, 'Kundenname ist erforderlich'),
  customer_email: z.string().email('Ungültige E-Mail-Adresse'),
  customer_address: z.string().optional(),
})

type ProposalFormData = z.infer<typeof proposalSchema>

interface ProposalFormProps {
  documentId: string
  extractionData?: ExtractionSummary | null
  onSubmit: (data: ProposalFormData) => void
  isLoading?: boolean
}

export default function ProposalForm({
  documentId: _documentId,
  extractionData,
  onSubmit,
  isLoading,
}: ProposalFormProps) {
  // Smart defaults from extraction data
  const defaultValues = useMemo(() => {
    if (!extractionData?.entities) {
      return { customer_name: '', customer_email: '', customer_address: '' }
    }

    const entities = extractionData.entities
    return {
      customer_name:
        entities.find((e) => e.entity_type === 'CUSTOMER_NAME')?.value || '',
      customer_email: entities.find((e) => e.entity_type === 'EMAIL')?.value || '',
      customer_address: entities.find((e) => e.entity_type === 'ADDRESS')?.value || '',
    }
  }, [extractionData])

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProposalFormData>({
    resolver: zodResolver(proposalSchema),
    defaultValues,
  })

  const hasAutoFilled = defaultValues.customer_name || defaultValues.customer_email

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {hasAutoFilled && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-800">
          ✓ Kundendaten wurden automatisch aus dem Dokument extrahiert
        </div>
      )}

      <FormField
        label="Kundenname"
        helpText="Name des Kunden oder der Firma"
        tier="tier2"
        required
        error={errors.customer_name?.message}
      >
        <Input
          {...register('customer_name')}
          placeholder="z.B. Schreinerei Müller GmbH"
          error={errors.customer_name?.message}
        />
      </FormField>

      <FormField
        label="E-Mail-Adresse"
        helpText="E-Mail für Angebotszustellung"
        tier="tier2"
        required
        error={errors.customer_email?.message}
      >
        <Input
          {...register('customer_email')}
          type="email"
          placeholder="kontakt@beispiel.de"
          error={errors.customer_email?.message}
        />
      </FormField>

      <FormField
        label="Adresse (Optional)"
        helpText="Vollständige Kundenadresse"
        tier="tier2"
      >
        <textarea
          {...register('customer_address')}
          rows={3}
          placeholder="Musterstraße 123&#10;12345 Musterstadt&#10;Deutschland"
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
        />
      </FormField>

      <FormField
        label="Gültigkeitsdauer"
        helpText="Angebot ist 30 Tage ab Erstellung gültig"
        tier="tier3"
        icon="💡"
      >
        <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-700">30 Tage (Standard)</p>
        </div>
      </FormField>

      <div className="flex justify-end gap-3 pt-4 border-t">
        <Button type="button" variant="secondary" disabled={isLoading}>
          Abbrechen
        </Button>
        <Button type="submit" isLoading={isLoading}>
          Angebot generieren
        </Button>
      </div>
    </form>
  )
}
