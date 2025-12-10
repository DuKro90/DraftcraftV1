/**
 * Global Error Boundary Component
 * Catches React errors and displays fallback UI
 */

import { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo)

    // TODO: Send to Sentry
    // if (window.Sentry) {
    //   window.Sentry.captureException(error, { contexts: { react: errorInfo } })
    // }
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
            <AlertTriangle className="h-16 w-16 text-red-600 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Etwas ist schief gelaufen
            </h1>
            <p className="text-gray-600 mb-6">
              Es tut uns leid, aber es ist ein Fehler aufgetreten. Bitte laden Sie die Seite neu.
            </p>

            {import.meta.env.DEV && this.state.error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-left">
                <p className="text-xs text-red-800 font-mono break-all">
                  {this.state.error.toString()}
                </p>
              </div>
            )}

            <button
              onClick={() => window.location.reload()}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Seite neu laden
            </button>

            <button
              onClick={() => (window.location.href = '/')}
              className="w-full mt-3 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Zur Startseite
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
