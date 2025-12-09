/**
 * Proposal Success Component
 * Shown after successful proposal generation
 */

import { CheckCircle, Download, Mail, FileText } from 'lucide-react'
import { useState } from 'react'
import { useProposal, useDownloadProposalPdf, useSendProposal } from '@/lib/hooks/useProposals'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { formatGermanCurrency, formatGermanDate } from '@/lib/utils/formatters'

interface ProposalSuccessProps {
  proposalId: string
  onNewDocument: () => void
}

export default function ProposalSuccess({ proposalId, onNewDocument }: ProposalSuccessProps) {
  const [showEmailForm, setShowEmailForm] = useState(false)
  const [emailAddress, setEmailAddress] = useState('')

  const { data: proposal, isLoading } = useProposal(proposalId)
  const downloadMutation = useDownloadProposalPdf()
  const sendMutation = useSendProposal()

  const handleDownload = () => {
    downloadMutation.mutate({
      proposalId,
      filename: `Angebot-${proposal?.proposal_number}.pdf`,
    })
  }

  const handleSendEmail = async () => {
    if (!emailAddress) return

    try {
      await sendMutation.mutateAsync({ proposalId, email: emailAddress })
      setShowEmailForm(false)
      setEmailAddress('')
      alert('Angebot erfolgreich per E-Mail versendet!')
    } catch (error) {
      alert('Fehler beim Versenden: ' + (error as Error).message)
    }
  }

  if (isLoading) {
    return <LoadingSpinner text="Angebotsdaten werden geladen..." />
  }

  if (!proposal) {
    return <p className="text-red-600">Angebot konnte nicht geladen werden</p>
  }

  return (
    <div className="space-y-6">
      {/* Success Header */}
      <div className="text-center py-6">
        <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Angebot erfolgreich erstellt!
        </h2>
        <p className="text-gray-600">
          Angebotsnummer: <span className="font-semibold">{proposal.proposal_number}</span>
        </p>
      </div>

      {/* Proposal Summary */}
      <Card>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500">Kunde</p>
            <p className="font-semibold text-gray-900">{proposal.customer_name}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">E-Mail</p>
            <p className="font-semibold text-gray-900">{proposal.customer_email}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Gesamtbetrag</p>
            <p className="text-2xl font-bold text-brand-600">
              {formatGermanCurrency(proposal.total)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Gültig bis</p>
            <p className="font-semibold text-gray-900">
              {formatGermanDate(proposal.valid_until)}
            </p>
          </div>
        </div>

        {/* Price Breakdown */}
        {proposal.lines && proposal.lines.length > 0 && (
          <div className="mt-6 pt-6 border-t">
            <h3 className="font-semibold text-gray-700 mb-3">Positionen</h3>
            <div className="space-y-2">
              {proposal.lines.slice(0, 3).map((line) => (
                <div key={line.id} className="flex justify-between text-sm">
                  <span className="text-gray-600">{line.description}</span>
                  <span className="font-medium text-gray-900">
                    {formatGermanCurrency(line.total_price)}
                  </span>
                </div>
              ))}
              {proposal.lines.length > 3 && (
                <p className="text-sm text-gray-500 italic">
                  ... und {proposal.lines.length - 3} weitere Positionen
                </p>
              )}
            </div>

            <div className="mt-4 pt-4 border-t space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Zwischensumme</span>
                <span className="font-medium">{formatGermanCurrency(proposal.subtotal)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">
                  MwSt. ({(proposal.vat_rate * 100).toFixed(0)}%)
                </span>
                <span className="font-medium">{formatGermanCurrency(proposal.vat_amount)}</span>
              </div>
              <div className="flex justify-between text-lg font-bold pt-2 border-t">
                <span>Gesamtbetrag</span>
                <span className="text-brand-600">{formatGermanCurrency(proposal.total)}</span>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Button
          variant="primary"
          onClick={handleDownload}
          isLoading={downloadMutation.isPending}
          className="flex-1"
        >
          <Download className="h-4 w-4 mr-2" />
          PDF herunterladen
        </Button>

        <Button
          variant="secondary"
          onClick={() => setShowEmailForm(!showEmailForm)}
          className="flex-1"
        >
          <Mail className="h-4 w-4 mr-2" />
          Per E-Mail versenden
        </Button>
      </div>

      {/* Email Form */}
      {showEmailForm && (
        <Card padding="sm">
          <div className="flex gap-2">
            <Input
              type="email"
              placeholder="E-Mail-Adresse eingeben"
              value={emailAddress}
              onChange={(e) => setEmailAddress(e.target.value)}
              className="flex-1"
            />
            <Button
              onClick={handleSendEmail}
              isLoading={sendMutation.isPending}
              disabled={!emailAddress}
            >
              Senden
            </Button>
          </div>
        </Card>
      )}

      {/* New Document Button */}
      <div className="text-center pt-6 border-t">
        <Button variant="outline" onClick={onNewDocument}>
          <FileText className="h-4 w-4 mr-2" />
          Neues Dokument hochladen
        </Button>
      </div>
    </div>
  )
}
