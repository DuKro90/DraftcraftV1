/**
 * Admin Dashboard Page
 * Placeholder for Phase 4B.4 implementation
 */

import { BarChart3, Activity, AlertCircle } from 'lucide-react'
import Card from '@/components/ui/Card'

export default function AdminDashboard() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
        <p className="text-gray-600">
          Übersicht über Systemaktivitäten und Betriebskennzahlen
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <div className="flex items-center gap-3">
            <div className="p-3 bg-brand-100 rounded-lg">
              <BarChart3 className="h-6 w-6 text-brand-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Dokumente heute</p>
              <p className="text-2xl font-bold text-gray-900">12</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <Activity className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Erfolgsquote</p>
              <p className="text-2xl font-bold text-gray-900">94,2%</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <AlertCircle className="h-6 w-6 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Offene Muster</p>
              <p className="text-2xl font-bold text-gray-900">3</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Placeholder for future features */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">Kommende Features</h2>
        <ul className="space-y-2 text-gray-600">
          <li>• Pattern Review Interface - Fehlerhafte Extraktionen analysieren</li>
          <li>• Fix Approval Workflow - Vorgeschlagene Fixes genehmigen</li>
          <li>• Deployment Management - System-Updates verwalten</li>
          <li>• Analytics Charts - Betriebskennzahlen visualisieren</li>
          <li>• Betriebskennzahlen Editor - TIER 1/2/3 Faktoren anpassen</li>
        </ul>
      </Card>
    </div>
  )
}
