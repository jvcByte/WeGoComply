import React, { useState } from 'react'
import {
  AlertTriangle, Play, FileText, Eye,
  Copy, CheckCircle, Clock, TrendingDown
} from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import { USER_ROLES } from '../auth/roles'
import { getApiErrorMessage, useApiClient } from '../lib/api'

const SAMPLE_TRANSACTIONS = [
  { transaction_id: 'TXN-001', customer_id: 'CUST-4421', amount: 7500000, currency: 'NGN', timestamp: '2026-04-16T02:34:00', transaction_type: 'transfer', counterparty: 'Unknown Corp Ltd', channel: 'mobile' },
  { transaction_id: 'TXN-002', customer_id: 'CUST-1102', amount: 45000, currency: 'NGN', timestamp: '2026-04-16T10:15:00', transaction_type: 'deposit', counterparty: 'Salary Payment', channel: 'web' },
  { transaction_id: 'TXN-003', customer_id: 'CUST-8834', amount: 2300000, currency: 'NGN', timestamp: '2026-04-16T23:58:00', transaction_type: 'withdrawal', counterparty: 'ATM Lagos', channel: 'atm' },
  { transaction_id: 'TXN-004', customer_id: 'CUST-3310', amount: 12000, currency: 'NGN', timestamp: '2026-04-16T14:22:00', transaction_type: 'transfer', counterparty: 'John Doe', channel: 'pos' },
  { transaction_id: 'TXN-005', customer_id: 'CUST-9901', amount: 9800000, currency: 'NGN', timestamp: '2026-04-16T03:11:00', transaction_type: 'transfer', counterparty: 'Shell Company XYZ', channel: 'web' },
]

const MOCK_RESULTS = {
  total_analyzed: 5, flagged_count: 3, clean_count: 2,
  flagged_transactions: [
    { transaction_id: 'TXN-001', customer_id: 'CUST-4421', amount: 7500000, currency: 'NGN', timestamp: '2026-04-16T02:34:00', transaction_type: 'transfer', counterparty: 'Unknown Corp Ltd', channel: 'mobile', anomaly_score: -0.312, rules_triggered: ['LARGE_CASH_TRANSACTION', 'UNUSUAL_HOURS'], risk_level: 'HIGH', recommended_action: 'GENERATE_STR' },
    { transaction_id: 'TXN-003', customer_id: 'CUST-8834', amount: 2300000, currency: 'NGN', timestamp: '2026-04-16T23:58:00', transaction_type: 'withdrawal', counterparty: 'ATM Lagos', channel: 'atm', anomaly_score: -0.198, rules_triggered: ['UNUSUAL_HOURS'], risk_level: 'MEDIUM', recommended_action: 'REVIEW' },
    { transaction_id: 'TXN-005', customer_id: 'CUST-9901', amount: 9800000, currency: 'NGN', timestamp: '2026-04-16T03:11:00', transaction_type: 'transfer', counterparty: 'Shell Company XYZ', channel: 'web', anomaly_score: -0.421, rules_triggered: ['LARGE_CASH_TRANSACTION', 'UNUSUAL_HOURS', 'HIGH_VALUE_TRANSFER'], risk_level: 'HIGH', recommended_action: 'GENERATE_STR' },
  ],
}

const riskStyle = {
  HIGH:   'border border-red-800 bg-red-900/50 text-red-300',
  MEDIUM: 'border border-yellow-800 bg-yellow-900/50 text-yellow-300',
}

const ruleDesc = {
  LARGE_CASH_TRANSACTION: 'Amount ≥ ₦5M (CBN threshold)',
  UNUSUAL_HOURS:          'Transaction outside 05:00–23:00',
  HIGH_VALUE_TRANSFER:    'Transfer > ₦1M to counterparty',
}

function AnomalyBar({ score }) {
  // score is negative for anomalies, range roughly -0.5 to +0.5
  const pct = Math.min(Math.max((-score) * 200, 0), 100)
  const color = pct > 60 ? 'bg-red-500' : pct > 30 ? 'bg-yellow-500' : 'bg-green-500'
  return (
    <div className="flex items-center gap-2 text-xs">
      <div className="flex-1 bg-gray-700 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-gray-400 w-12 text-right">{score.toFixed(3)}</span>
    </div>
  )
}

export default function AML() {
  const { authMode, hasAnyRole } = useAuth()
  const api = useApiClient()
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [str, setStr] = useState(null)
  const [strLoading, setStrLoading] = useState(null)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const [reviewedIds, setReviewedIds] = useState(new Set())
  const canGenerateSTR = hasAnyRole([USER_ROLES.ADMIN, USER_ROLES.COMPLIANCE_OFFICER])

  const runMonitor = async () => {
    setLoading(true)
    setError('')
    setStr(null)
    try {
      const { data } = await api.post('/api/aml/monitor', { transactions: SAMPLE_TRANSACTIONS })
      setResults(data)
    } catch (err) {
      if (authMode === 'mock') {
        setResults(MOCK_RESULTS)
      } else {
        setError(getApiErrorMessage(err, 'AML monitoring failed.'))
      }
    }
    setLoading(false)
  }

  const generateSTR = async (tx) => {
    setStrLoading(tx.transaction_id)
    setError('')
    try {
      const { data } = await api.post(`/api/aml/generate-str/${tx.transaction_id}`, tx)
      setStr(data)
    } catch (err) {
      if (authMode === 'mock') {
        setStr({
          report_reference: `STR-${tx.transaction_id.slice(-4).toUpperCase()}`,
          reporting_institution: 'WeGoComply Demo Bank',
          subject_name: tx.customer_id,
          transaction_summary: `Customer conducted a ${tx.transaction_type} of ₦${tx.amount.toLocaleString()} via ${tx.channel} at ${tx.timestamp.split('T')[1]}.`,
          grounds_for_suspicion: `Transaction amount exceeds ₦5M CBN threshold and occurred outside normal banking hours. Counterparty "${tx.counterparty}" is unverified.`,
          recommended_action: 'Freeze account pending investigation and file STR with NFIU within 24 hours per CBN AML/CFT Regulations.',
          report_date: '2026-04-16',
        })
      } else {
        setError(getApiErrorMessage(err, 'STR generation failed.'))
      }
    }
    setStrLoading(null)
  }

  const markReviewed = (id) => setReviewedIds(prev => new Set([...prev, id]))

  const copySTR = () => {
    if (!str) return
    navigator.clipboard.writeText(JSON.stringify(str, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <AlertTriangle className="text-red-400" size={22} /> AML Transaction Monitor
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Isolation Forest ML + CBN Rules Engine · Auto STR generation for NFIU
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {/* Transaction batch */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <span className="text-sm font-medium text-gray-200">Transaction Batch</span>
            <span className="text-xs text-gray-500 ml-2">({SAMPLE_TRANSACTIONS.length} transactions)</span>
          </div>
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
                {['ID', 'Customer', 'Amount (₦)', 'Type', 'Counterparty', 'Time', 'Channel'].map(h => (
                  <th key={h} className="text-left py-2 pr-3 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {SAMPLE_TRANSACTIONS.map(tx => (
                <tr key={tx.transaction_id} className="border-b border-gray-800/50">
                  <td className="py-2 pr-3 font-mono">{tx.transaction_id}</td>
                  <td className="py-2 pr-3">{tx.customer_id}</td>
                  <td className="py-2 pr-3">{tx.amount.toLocaleString()}</td>
                  <td className="py-2 pr-3">{tx.transaction_type}</td>
                  <td className="py-2 pr-3 max-w-[120px] truncate">{tx.counterparty}</td>
                  <td className="py-2 pr-3">{tx.timestamp.split('T')[1]}</td>
                  <td className="py-2 pr-3">{tx.channel}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Results */}
      {results && (
        <div className="space-y-4">
          {!canGenerateSTR && (
            <div className="rounded-xl border border-yellow-900 bg-yellow-950/30 px-4 py-3 text-sm text-yellow-200">
              Your role can review flagged activity, but only admins and compliance officers can generate STRs.
            </div>
          )}

          {/* Summary stats */}
          <div className="grid grid-cols-3 gap-4">
            {[
              ['Analyzed', results.total_analyzed, 'text-blue-400', TrendingDown],
              ['Flagged', results.flagged_count, 'text-red-400', AlertTriangle],
              ['Clean', results.clean_count, 'text-green-400', CheckCircle],
            ].map(([label, value, color, Icon]) => (
              <div key={label} className="rounded-xl border border-gray-800 bg-gray-900 p-4 text-center">
                <Icon size={18} className={`${color} mx-auto mb-2`} />
                <div className={`text-3xl font-bold ${color}`}>{value}</div>
                <div className="text-xs text-gray-400 mt-1">{label}</div>
              </div>
            ))}
          </div>

          {/* Flagged transactions */}
          <div className="space-y-3">
            {results.flagged_transactions.map(tx => (
              <div key={tx.transaction_id} className={`rounded-xl border bg-gray-900 p-4 space-y-3 ${
                tx.risk_level === 'HIGH' ? 'border-red-900' : 'border-yellow-900'
              }`}>
                {/* Header row */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-sm font-medium">{tx.transaction_id}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${riskStyle[tx.risk_level]}`}>
                        {tx.risk_level}
                      </span>
                      {reviewedIds.has(tx.transaction_id) && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-400">
                          Reviewed
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {tx.customer_id} · ₦{tx.amount.toLocaleString()} · {tx.transaction_type} · {tx.channel}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      Counterparty: <span className="text-gray-300">{tx.counterparty}</span>
                      {' · '}{tx.timestamp.replace('T', ' ')}
                    </div>
                  </div>

                  <div className="flex gap-2 shrink-0">
                    {tx.recommended_action === 'REVIEW' && !reviewedIds.has(tx.transaction_id) && (
                      <button
                        onClick={() => markReviewed(tx.transaction_id)}
                        className="flex items-center gap-1 text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 px-3 py-1.5 rounded-lg transition-colors"
                      >
                        <Eye size={12} /> Mark Reviewed
                      </button>
                    )}
                    {tx.recommended_action === 'GENERATE_STR' && canGenerateSTR && (
                      <button
                        onClick={() => generateSTR(tx)}
                        disabled={strLoading === tx.transaction_id}
                        className="flex items-center gap-1 text-xs bg-red-700 hover:bg-red-600 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg transition-colors"
                      >
                        <FileText size={12} />
                        {strLoading === tx.transaction_id ? 'Generating...' : 'Generate STR'}
                      </button>
                    )}
                  </div>
                </div>

                {/* Anomaly score bar */}
                <div>
                  <div className="text-xs text-gray-500 mb-1">Anomaly Score (ML)</div>
                  <AnomalyBar score={tx.anomaly_score} />
                </div>

                {/* Rules triggered */}
                <div className="flex flex-wrap gap-2">
                  {tx.rules_triggered.map(rule => (
                    <div key={rule} className="group relative">
                      <span className="text-xs bg-gray-800 text-gray-300 px-2 py-1 rounded cursor-help">
                        {rule}
                      </span>
                      <div className="absolute bottom-full left-0 mb-1 hidden group-hover:block bg-gray-700 text-xs text-gray-200 px-2 py-1 rounded whitespace-nowrap z-10">
                        {ruleDesc[rule] || rule}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* STR Report */}
      {str && (
        <div className="rounded-xl border border-red-800 bg-gray-900 p-5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 font-bold text-red-400">
              <FileText size={18} /> Suspicious Transaction Report (STR)
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">NFIU-compliant format</span>
              <button
                onClick={copySTR}
                className="flex items-center gap-1 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-2 py-1 rounded transition-colors"
              >
                {copied ? <><CheckCircle size={11} className="text-green-400" /> Copied</> : <><Copy size={11} /> Copy</>}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-2 text-sm">
            {[
              ['Report Reference', str.report_reference],
              ['Reporting Institution', str.reporting_institution],
              ['Subject Name', str.subject_name],
              ['Transaction Summary', str.transaction_summary],
              ['Grounds for Suspicion', str.grounds_for_suspicion],
              ['Recommended Action', str.recommended_action],
              ['Report Date', str.report_date],
            ].map(([label, value]) => (
              <div key={label} className="bg-gray-800 rounded-lg p-3">
                <div className="text-xs text-gray-400">{label}</div>
                <div className="text-gray-200 mt-0.5">{value}</div>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Clock size={12} />
            Ready for submission to NFIU within 24 hours · Ref: {str.report_reference}
          </div>
        </div>
      )}
    </div>
  )
}
