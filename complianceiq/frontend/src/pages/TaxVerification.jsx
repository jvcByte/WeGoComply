import React, { useState } from 'react'
import { FileText, Upload, CheckCircle, XCircle } from 'lucide-react'
import axios from 'axios'

const SAMPLE_RECORDS = [
  { customer_id: 'CUST-001', name: 'Adaeze Okonkwo', tin: '1234567890' },
  { customer_id: 'CUST-002', name: 'Emeka Nwosu', tin: '0987654321' },
  { customer_id: 'CUST-003', name: 'Fatima Aliyu', tin: '1122334455' },
  { customer_id: 'CUST-004', name: 'Chukwuemeka Eze', tin: '5566778899' },
  { customer_id: 'CUST-005', name: 'Ngozi Adeyemi', tin: '9988776655' },
]

export default function TaxVerification() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)

  const runBulkVerify = async () => {
    setLoading(true)
    try {
      const { data } = await axios.post('/api/tax/bulk-verify', { records: SAMPLE_RECORDS })
      setResults(data)
    } catch {
      // Demo fallback
      const records = SAMPLE_RECORDS.map((r, i) => ({
        customer_id: r.customer_id,
        tin: r.tin,
        status: i === 2 ? 'NOT_FOUND' : 'MATCHED',
        firs_name: i === 2 ? '' : r.name,
        submitted_name: r.name,
        match_confidence: i === 2 ? 0 : 0.95
      }))
      const matched = records.filter(r => r.status === 'MATCHED').length
      setResults({
        total: 5, matched, failed: 5 - matched,
        match_rate: (matched / 5 * 100).toFixed(1),
        deadline_risk: matched / 5 < 0.8 ? 'HIGH' : 'LOW',
        records
      })
    }
    setLoading(false)
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <FileText className="text-yellow-400" size={22} /> Tax ID (TIN) Verification
        </h1>
        <p className="text-gray-400 text-sm mt-1">Bulk TIN matching against FIRS — meet the mandate before sanctions apply</p>
      </div>

      <div className="bg-yellow-900/20 border border-yellow-800 rounded-xl p-4 text-sm text-yellow-300">
        ⚠ FIRS Mandate: Accounts without verified TINs will be restricted above ₦500,000 effective April 1, 2026.
      </div>

      <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-gray-400">Sample customer records ({SAMPLE_RECORDS.length})</span>
          <button
            onClick={runBulkVerify}
            disabled={loading}
            className="flex items-center gap-2 bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
          >
            <Upload size={14} /> {loading ? 'Verifying...' : 'Run Bulk Verification'}
          </button>
        </div>
        <table className="w-full text-xs text-gray-400">
          <thead>
            <tr className="border-b border-gray-800">
              {['Customer ID', 'Name', 'TIN'].map(h => (
                <th key={h} className="text-left py-2 pr-4 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {SAMPLE_RECORDS.map(r => (
              <tr key={r.customer_id} className="border-b border-gray-800/50">
                <td className="py-2 pr-4">{r.customer_id}</td>
                <td className="py-2 pr-4">{r.name}</td>
                <td className="py-2 pr-4 font-mono">{r.tin}</td>
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
              ['Match Rate', `${results.match_rate}%`, results.match_rate >= 80 ? 'text-green-400' : 'text-red-400'],
            ].map(([label, val, color]) => (
              <div key={label} className="bg-gray-900 rounded-xl p-4 border border-gray-800 text-center">
                <div className={`text-2xl font-bold ${color}`}>{val}</div>
                <div className="text-xs text-gray-400 mt-1">{label}</div>
              </div>
            ))}
          </div>

          <div className={`rounded-xl p-3 text-sm font-medium ${results.deadline_risk === 'HIGH' ? 'bg-red-900/30 text-red-300 border border-red-800' : 'bg-green-900/30 text-green-300 border border-green-800'}`}>
            Deadline Risk: {results.deadline_risk} — {results.deadline_risk === 'HIGH' ? 'Immediate action required to avoid account restrictions.' : 'On track to meet FIRS mandate.'}
          </div>

          <div className="space-y-2">
            {results.records.map(r => (
              <div key={r.customer_id} className="flex items-center gap-3 bg-gray-900 rounded-lg p-3 border border-gray-800 text-sm">
                {r.status === 'MATCHED'
                  ? <CheckCircle className="text-green-400 shrink-0" size={16} />
                  : <XCircle className="text-red-400 shrink-0" size={16} />
                }
                <span className="text-gray-300 w-24">{r.customer_id}</span>
                <span className="text-gray-400 flex-1">{r.submitted_name}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${r.status === 'MATCHED' ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'}`}>
                  {r.status}
                </span>
                <span className="text-xs text-gray-500">{(r.match_confidence * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
