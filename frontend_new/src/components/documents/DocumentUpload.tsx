/**
 * Document Upload Component with Drag & Drop
 */

import { useCallback, useState } from 'react'
import { Upload, FileText, X } from 'lucide-react'
import Button from '@/components/ui/Button'
import { formatFileSize } from '@/lib/utils/formatters'

interface DocumentUploadProps {
  onUpload: (file: File) => void
  isLoading?: boolean
}

export default function DocumentUpload({ onUpload, isLoading }: DocumentUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleFileSelect = useCallback((file: File) => {
    // Validate file type
    const validTypes = [
      'application/pdf',
      'image/png',
      'image/jpeg',
      'image/jpg',
      'text/xml',
    ]
    if (!validTypes.includes(file.type)) {
      alert('Ungültiger Dateityp. Bitte PDF, PNG, JPG oder XML hochladen.')
      return
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024 // 10MB
    if (file.size > maxSize) {
      alert('Datei zu groß. Maximale Größe: 10 MB')
      return
    }

    setSelectedFile(file)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      setIsDragging(false)

      const file = e.dataTransfer.files[0]
      if (file) {
        handleFileSelect(file)
      }
    },
    [handleFileSelect]
  )

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback(() => {
    setIsDragging(false)
  }, [])

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) {
        handleFileSelect(file)
      }
    },
    [handleFileSelect]
  )

  const handleUpload = () => {
    if (selectedFile) {
      onUpload(selectedFile)
    }
  }

  const handleClear = () => {
    setSelectedFile(null)
  }

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging
            ? 'border-brand-500 bg-brand-50'
            : 'border-gray-300 hover:border-brand-400'
        }`}
      >
        <Upload className="h-12 w-12 mx-auto text-gray-400 mb-4" />

        {!selectedFile ? (
          <>
            <p className="text-lg font-medium text-gray-700 mb-2">
              Dokument hier ablegen
            </p>
            <p className="text-sm text-gray-500 mb-4">
              oder klicken Sie unten, um eine Datei auszuwählen
            </p>

            <label className="inline-block cursor-pointer">
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.xml"
                onChange={handleFileInput}
                className="hidden"
                disabled={isLoading}
              />
              <span className="inline-flex items-center justify-center rounded-lg font-medium transition-colors focus-visible-ring h-10 px-4 text-base bg-gray-100 text-gray-900 hover:bg-gray-200 active:bg-gray-300">
                Datei auswählen
              </span>
            </label>

            <p className="text-xs text-gray-400 mt-4">
              PDF, PNG, JPG oder XML • Max. 10 MB
            </p>
          </>
        ) : (
          <div className="flex items-center justify-center gap-4 p-4 bg-white rounded-lg border border-gray-200">
            <FileText className="h-8 w-8 text-brand-600 flex-shrink-0" />
            <div className="flex-1 text-left">
              <p className="font-medium text-gray-900">{selectedFile.name}</p>
              <p className="text-sm text-gray-500">{formatFileSize(selectedFile.size)}</p>
            </div>
            <button
              onClick={handleClear}
              className="p-1 hover:bg-gray-100 rounded"
              disabled={isLoading}
            >
              <X className="h-5 w-5 text-gray-500" />
            </button>
          </div>
        )}
      </div>

      {/* Upload Button */}
      {selectedFile && (
        <div className="flex justify-end">
          <Button
            onClick={handleUpload}
            isLoading={isLoading}
            disabled={!selectedFile || isLoading}
          >
            Hochladen und Analysieren
          </Button>
        </div>
      )}
    </div>
  )
}
