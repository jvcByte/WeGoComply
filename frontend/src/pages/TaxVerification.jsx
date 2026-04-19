import React, { useState } from 'react'
import { FileText, Upload, CheckCircle, XCircle } from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import { getApiErrorMessage, useApiClient } from '../lib/api'

const SAMPLE_RECORDS = [
  { customer_id: 'CUST-001', name: 'Adaeze Okonkwo', tin: '1234567890' },
  { customer_id: 'CUST-002', name: 'Emeka Nwosu', tin: '0987654321' },
  { customer_id: 'CUST-003', name: 'Fatima Aliyu', tin: '1122334455' },
  { customer_id: 'CUST-004', name: 'Chukwuemeka Eze', tin: '5566778899' },
  { customer_id: 'CUST-005', name: 'Ngozi Adeyemi', tin: '9988776655' },
]

export default function TaxVerification() {
  const { authMode } = useAuth()
  const api = useApiClient()
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const runBulkVerify = async () => {
    setLoading(true)
    setError('')

    try {
      const { data } = await api.post('/api/tax/bulk-verify', { records: SAMPLE_RECORDS })
      setResults(data)
    } catch (requestError) {
      if (authMode === 'mock') {
        const records = SAMPLE_RECORDS.map((record, index) => ({
          customer_id: record.customer_id,
          tin: record.tin,
          status: index === 2 ? 'NOT_FOUND' : 'MATCHED',
          firs_name: index === 2 ? '' : record.name,
          submitted_name: record.name,
          match_confidence: index === 2 ? 0 : 0.95,
        }))
        const matched = records.filter((record) => record.status === 'MATCHED').length

        setResults({
          total: 5,
          matched,
          failed: 5 - matched,
          match_rate: (matched / 5 * 100).toFixed(1),
          deadline_risk: matched / 5 < 0.8 ? 'HIGH' : 'LOW',
          records,
        })
      } else {
        setError(getApiErrorMessage(requestError, 'TIN verification failed.'))
      }
    }

    setLoading(false)
  }

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <FileText className="text-yellow-400" size={22} /> Tax ID (TIN) Verification
        </h1>
        <p className="mt-1 text-sm text-gray-400">
          Bulk TIN matching against FIRS to meet the mandate before sanctions apply
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      <div className="rounded-xl border border-yellow-800 bg-yellow-900/20 p-4 text-sm text-yellow-300">
        FIRS Mandate: Accounts without verified TINs will be restricted above N500,000 effective April 1, 2026.
      </div>

      <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-sm text-gray-400">
            Sample customer records ({SAMPLE_RECORDS.length})
          </span>
          <button
            onClick={runBulkVerify}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-yellow-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-yellow-700 disabled:opacity-50"
          >
            <Upload size={14} /> {loading ? 'Verifying...' : 'Run Bulk Verification'}
          </button>
        </div>
        <table className="w-full text-xs text-gray-400">
          <thead>
            <tr className="border-b border-gray-800">
              {['Customer ID', 'Name', 'TIN'].map((heading) => (
                <th key={heading} className="py-2 pr-4 text-left font-medium">
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {SAMPLE_RECORDS.map((record) => (
              <tr key={record.customer_id} className="border-b border-gray-800/50">
                <td className="py-2 pr-4">{record.customer_id}</td>
                <td className="py-2 pr-4">{record.name}</td>
                <td className="py-2 pr-4 font-mono">{record.tin}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {results && (
        <div className="space-y-4">
          <div className="grid grid-cols-4 gap-4">
            {[
              ['Total', results.total, 'text-blue-400'],
              ['Matched', results.matched, 'text-green-400'],
              ['Failed', results.failed, 'text-red-400'],
              [
                'Match Rate',
                `${results.match_rate}%`,
                results.match_rate >= 80 ? 'text-green-400' : 'text-red-400',
              ],
            ].map(([label, value, color]) => (
              <div key={label} className="rounded-xl border border-gray-800 bg-gray-900 p-4 text-center">
                <div className={`text-2xl font-bold ${color}`}>{value}</div>
                <div className="mt-1 text-xs text-gray-400">{label}</div>
              </div>
            ))}
          </div>

          <div
            className={`rounded-xl border p-3 text-sm font-medium ${
              results.deadline_risk === 'HIGH'
                ? 'border-red-800 bg-red-900/30 text-red-300'
                : 'border-green-800 bg-green-900/30 text-green-300'
            }`}
          >
            Deadline Risk: {results.deadline_risk} -{' '}
            {results.deadline_risk === 'HIGH'
              ? 'Immediate action required to avoid account restrictions.'
              : 'On track to meet FIRS mandate.'}
          </div>

          <div className="space-y-2">
            {results.records.map((record) => (
              <div
                key={record.customer_id}
                className="flex items-center gap-3 rounded-lg border border-gray-800 bg-gray-900 p-3 text-sm"
              >
                {record.status === 'MATCHED' ? (
                  <CheckCircle className="shrink-0 text-green-400" size={16} />
                ) : (
                  <XCircle className="shrink-0 text-red-400" size={16} />
                )}
                <span className="w-24 text-gray-300">{record.customer_id}</span>
                <span className="flex-1 text-gray-400">{record.submitted_name}</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${
                    record.status === 'MATCHED'
                      ? 'bg-green-900/50 text-green-300'
                      : 'bg-red-900/50 text-red-300'
                  }`}
                >
                  {record.status}
                </span>
                <span className="text-xs text-gray-500">
                  {(record.match_confidence * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
