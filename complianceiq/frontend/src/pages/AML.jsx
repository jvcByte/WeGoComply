import React, { useState } from 'react'
import { AlertTriangle, Play, FileText } from 'lucide-react'
import axios from 'axios'

const SAMPLE_TRANSACTIONS = [
  { transaction_id: 'TXN-001', customer_id: 'CUST-4421', amount: 7500000, currency: 'NGN', timestamp: '2026-04-16T02:34:00', transaction_type: 'transfer', counterparty: 'Unknown Corp Ltd', channel: 'mobile' },
  { transaction_id: 'TXN-002', customer_id: 'CUST-1102', amount: 45000, currency: 'NGN', timestamp: '2026-04-16T10:15:00', transaction_type: 'deposit', counterparty: 'Salary Payment', channel: 'web' },
  { transaction_id: 'TXN-003', customer_id: 'CUST-8834', amount: 2300000, currency: 'NGN', timestamp: '2026-04-16T23:58:00', transaction_type: 'withdrawal', counterparty: 'ATM Lagos', channel: 'atm' },
  { transaction_id: 'TXN-004', customer_id: 'CUST-3310', amount: 12000, currency: 'NGN', timestamp: '2026-04-16T14:22:00', transaction_type: 'transfer', counterparty: 'John Doe', channel: 'pos' },
  { transaction_id: 'TXN-005', customer_id: 'CUST-9901', amount: 9800000, currency: 'NGN', timestamp: '2026-04-16T03:11:00', transaction_type: 'transfer', counterparty: 'Shell Company XYZ', channel: 'web' },
]

export default function AML() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [str, setStr] = useState(null)
  const [strLoading, setStrLoading] = useState(null)

  const runMonitor = async () => {
    setLoading(true)
    try {
      const { data } = await axios.post('/api/aml/monitor', { transactions: SAMPLE_TRANSACTIONS })
      setResults(data)
    } catch {
      // Demo fallback
      setResults({
        total_analyzed: 5,
        flagged_count: 3,
        clean_count: 2,
        flagged_transactions: [
          { transaction_id: 'TXN-001', customer_id: 'CUST-4421', amount: 7500000, timestamp: '2026-04-16T02:34:00', anomaly_score: -0.312, rules_triggered: ['LARGE_CASH_TRANSACTION', 'UNUSUAL_HOURS'], risk_level: 'HIGH', recommended_action: 'GENERATE_STR' },
          { transaction_id: 'TXN-003', customer_id: 'CUST-8834', amount: 2300000, timestamp: '2026-04-16T23:58:00', anomaly_score: -0.198, rules_triggered: ['UNUSUAL_HOURS'], risk_level: 'MEDIUM', recommended_action: 'REVIEW' },
          { transaction_id: 'TXN-005', customer_id: 'CUST-9901', amount: 9800000, timestamp: '2026-04-16T03:11:00', anomaly_score: -0.421, rules_triggered: ['LARGE_CASH_TRANSACTION', 'UNUSUAL_HOURS', 'HIGH_VALUE_TRANSFER'], risk_level: 'HIGH', recommended_action: 'GENERATE_STR' },
        ]
      })
    }
    setLoading(false)
  }

  const generateSTR = async (tx) => {
    setStrLoading(tx.transaction_id)
    try {
      const { data } = await axios.post(`/api/aml/generate-str/${tx.transaction_id}`, tx)
      setStr(data)
    } catch {
      setStr({
        report_reference: `STR-${tx.transaction_id.slice(-4).toUpperCase()}`,
        reporting_institution: 'ComplianceIQ Demo Bank',
        subject_name: tx.customer_id,
        transaction_summary: `Customer conducted a ${tx.transaction_type} of ₦${tx.amount.toLocaleString()} via ${tx.channel} at an unusual time.`,
        grounds_for_suspicion: 'Transaction amount exceeds ₦5M threshold and occurred outside normal banking hours (2-4am). Counterparty is an unverified entity.',
        recommended_action: 'Freeze account pending investigation and file STR with NFIU within 24 hours.',
        report_date: '2026-04-16'
      })
    }
    setStrLoading(null)
  }

  const riskBadge = (level) => ({
    HIGH: 'bg-red-900/50 text-red-300 border border-red-800',
    MEDIUM: 'bg-yellow-900/50 text-yellow-300 border border-yellow-800',
  }[level] || '')

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <AlertTriangle className="text-red-400" size={22} /> AML Transaction Monitor
        </h1>
        <p className="text-gray-400 text-sm mt-1">AI anomaly detection + auto STR generation (NFIU-compliant)</p>
      </div>

      <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-gray-400">Sample transaction batch ({SAMPLE_TRANSACTIONS.length} transactions)</span>
          <button
            onClick={runMonitor}
            disabled={loading}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
          >
            <Play size={14} /> {loading ? 'Analyzing...' : 'Run Analysis'}
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-gray-400">
            <thead>
              <tr className="border-b border-gray-800">
                {['ID', 'Customer', 'Amount (₦)', 'Type', 'Time', 'Channel'].map(h => (
                  <th key={h} className="text-left py-2 pr-4 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {SAMPLE_TRANSACTIONS.map(tx => (
                <tr key={tx.transaction_id} className="border-b border-gray-800/50">
                  <td className="py-2 pr-4">{tx.transaction_id}</td>
                  <td className="py-2 pr-4">{tx.customer_id}</td>
                  <td className="py-2 pr-4">{tx.amount.toLocaleString()}</td>
                  <td className="py-2 pr-4">{tx.transaction_type}</td>
                  <td className="py-2 pr-4">{tx.timestamp.split('T')[1]}</td>
                  <td className="py-2 pr-4">{tx.channel}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {results && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            {[
              ['Analyzed', results.total_analyzed, 'text-blue-400'],
              ['Flagged', results.flagged_count, 'text-red-400'],
              ['Clean', results.clean_count, 'text-green-400'],
            ].map(([label, val, color]) => (
              <div key={label} className="bg-gray-900 rounded-xl p-4 border border-gray-800 text-center">
                <div className={`text-3xl font-bold ${color}`}>{val}</div>
                <div className="text-xs text-gray-400 mt-1">{label}</div>
              </div>
            ))}
          </div>

          <div className="space-y-3">
            {results.flagged_transactions.map(tx => (
              <div key={tx.transaction_id} className="bg-gray-900 rounded-xl p-4 border border-gray-800">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm">{tx.transaction_id}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${riskBadge(tx.risk_level)}`}>{tx.risk_level}</span>
                    </div>
                    <div className="text-xs text-gray-400 mt-1">Customer: {tx.customer_id} · ₦{tx.amount.toLocaleString()} · {tx.timestamp}</div>
                    <div className="flex gap-2 mt-2 flex-wrap">
                      {tx.rules_triggered.map(r => (
                        <span key={r} className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded">{r}</span>
                      ))}
                    </div>
                  </div>
                  {tx.recommended_action === 'GENERATE_STR' && (
                    <button
                      onClick={() => generateSTR(tx)}
                      disabled={strLoading === tx.transaction_id}
                      className="flex items-center gap-1 text-xs bg-red-700 hover:bg-red-600 text-white px-3 py-1.5 rounded-lg transition-colors ml-4 shrink-0"
                    >
                      <FileText size={12} />
                      {strLoading === tx.transaction_id ? 'Generating...' : 'Generate STR'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {str && (
        <div className="bg-gray-900 rounded-xl p-5 border border-red-800 space-y-3">
          <div className="flex items-center gap-2 text-red-400 font-bold">
            <FileText size={18} /> Suspicious Transaction Report (STR)
          </div>
          <div className="grid grid-cols-1 gap-2 text-sm">
            {Object.entries(str).map(([key, val]) => (
              <div key={key} className="bg-gray-800 rounded-lg p-3">
                <div className="text-xs text-gray-400 capitalize">{key.replace(/_/g, ' ')}</div>
                <div className="mt-0.5 text-gray-200">{val}</div>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-500">Ready for submission to NFIU. Reference: {str.report_reference}</p>
        </div>
      )}
    </div>
  )
}
