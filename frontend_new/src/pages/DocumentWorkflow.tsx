/**
 * Main Document Workflow Page
 * Implements step-by-step workflow: Upload → Process → Review → Proposal
 */

import { useState } from 'react'
import { Upload, FileText, CheckCircle, Send } from 'lucide-react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import {
  useUploadDocument,
  useProcessDocument,
  useAutoExtractionSummary,
} from '@/lib/hooks/useDocuments'
import { useGenerateProposal } from '@/lib/hooks/useProposals'
import DocumentUpload from '@/components/documents/DocumentUpload'
import ExtractionResults from '@/components/documents/ExtractionResults'
import ProposalForm from '@/components/proposals/ProposalForm'
import ProposalSuccess from '@/components/proposals/ProposalSuccess'

type WorkflowStep = 'upload' | 'process' | 'review' | 'proposal' | 'success'

export default function DocumentWorkflow() {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('upload')
  const [documentId, setDocumentId] = useState<string | null>(null)
  const [proposalId, setProposalId] = useState<string | null>(null)

  const uploadMutation = useUploadDocument()
  const processMutation = useProcessDocument()
  const {
    data: extractionData,
    isLoading: isLoadingExtraction,
  } = useAutoExtractionSummary(documentId)
  const proposalMutation = useGenerateProposal()

  // Step 1: Upload Document
  const handleFileUpload = async (file: File) => {
    try {
      const document = await uploadMutation.mutateAsync(file)
      setDocumentId(document.id)
      setCurrentStep('process')

      // Automatically start processing
      await processMutation.mutateAsync(document.id)
      setCurrentStep('review')
    } catch (error) {
      console.error('Upload/Process error:', error)
    }
  }

  // Step 4: Generate Proposal
  const handleGenerateProposal = async (data: {
    customer_name: string
    customer_email: string
    customer_address?: string
  }) => {
    if (!documentId) return

    try {
      const proposal = await proposalMutation.mutateAsync({
        document_id: documentId,
        ...data,
        valid_days: 30,
      })
      setProposalId(proposal.id)
      setCurrentStep('success')
    } catch (error) {
      console.error('Proposal generation error:', error)
    }
  }

  // Step Indicator Component
  const steps = [
    { id: 'upload', label: 'Hochladen', icon: Upload },
    { id: 'process', label: 'Verarbeitung', icon: FileText },
    { id: 'review', label: 'Prüfen', icon: CheckCircle },
    { id: 'proposal', label: 'Angebot', icon: Send },
  ]

  const currentStepIndex = steps.findIndex((s) => s.id === currentStep)

  return (
    <div className="max-w-5xl mx-auto">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Angebots-Workflow</h1>
        <p className="text-gray-600">
          Lade ein Dokument hoch und erstelle automatisch ein Angebot
        </p>
      </div>

      {/* Step Indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => {
            const Icon = step.icon
            const isCompleted = index < currentStepIndex
            const isCurrent = index === currentStepIndex

            return (
              <div key={step.id} className="flex items-center flex-1">
                {/* Step Circle */}
                <div className="flex flex-col items-center">
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                      isCompleted
                        ? 'bg-green-500 text-white'
                        : isCurrent
                        ? 'bg-brand-500 text-white ring-4 ring-brand-100'
                        : 'bg-gray-200 text-gray-400'
                    }`}
                  >
                    <Icon className="h-6 w-6" />
                  </div>
                  <p
                    className={`mt-2 text-sm font-medium ${
                      isCurrent ? 'text-brand-700' : 'text-gray-500'
                    }`}
                  >
                    {step.label}
                  </p>
                </div>

                {/* Connector Line */}
                {index < steps.length - 1 && (
                  <div
                    className={`flex-1 h-1 mx-4 transition-colors ${
                      isCompleted ? 'bg-green-500' : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Step Content */}
      <div className="space-y-6">
        {/* Step 1: Upload */}
        {currentStep === 'upload' && (
          <Card>
            <h2 className="text-xl font-semibold mb-4">1. Dokument hochladen</h2>
            <DocumentUpload
              onUpload={handleFileUpload}
              isLoading={uploadMutation.isPending || processMutation.isPending}
            />
            {uploadMutation.error && (
              <p className="mt-2 text-sm text-red-600">
                Fehler: {uploadMutation.error.message}
              </p>
            )}
          </Card>
        )}

        {/* Step 2: Processing */}
        {currentStep === 'process' && (
          <Card>
            <h2 className="text-xl font-semibold mb-4">2. Dokument wird verarbeitet...</h2>
            <LoadingSpinner size="lg" text="OCR + NER Extraktion läuft" />
          </Card>
        )}

        {/* Step 3: Review Extraction Results */}
        {currentStep === 'review' && (
          <Card>
            <h2 className="text-xl font-semibold mb-4">3. Ergebnisse prüfen</h2>
            {isLoadingExtraction ? (
              <LoadingSpinner text="Extraktionsergebnisse werden geladen..." />
            ) : extractionData ? (
              <>
                <ExtractionResults data={extractionData} />
                <div className="mt-6 flex justify-end">
                  <Button onClick={() => setCurrentStep('proposal')}>
                    Weiter zum Angebot
                  </Button>
                </div>
              </>
            ) : (
              <p className="text-gray-600">Keine Extraktionsdaten verfügbar</p>
            )}
          </Card>
        )}

        {/* Step 4: Generate Proposal */}
        {currentStep === 'proposal' && (
          <Card>
            <h2 className="text-xl font-semibold mb-4">4. Angebot erstellen</h2>
            <ProposalForm
              documentId={documentId!}
              extractionData={extractionData}
              onSubmit={handleGenerateProposal}
              isLoading={proposalMutation.isPending}
            />
            {proposalMutation.error && (
              <p className="mt-2 text-sm text-red-600">
                Fehler: {proposalMutation.error.message}
              </p>
            )}
          </Card>
        )}

        {/* Success: Proposal Generated */}
        {currentStep === 'success' && proposalId && (
          <Card>
            <ProposalSuccess
              proposalId={proposalId}
              onNewDocument={() => {
                setCurrentStep('upload')
                setDocumentId(null)
                setProposalId(null)
              }}
            />
          </Card>
        )}
      </div>
    </div>
  )
}
