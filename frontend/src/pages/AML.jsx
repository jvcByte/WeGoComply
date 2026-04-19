import React, { useState } from 'react'
import { AlertTriangle, Play, FileText } from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import { USER_ROLES } from '../auth/roles'
import { getApiErrorMessage, useApiClient } from '../lib/api'

const SAMPLE_TRANSACTIONS = [
  {
    transaction_id: 'TXN-001',
    customer_id: 'CUST-4421',
    amount: 7500000,
    currency: 'NGN',
    timestamp: '2026-04-16T02:34:00',
    transaction_type: 'transfer',
    counterparty: 'Unknown Corp Ltd',
    channel: 'mobile',
  },
  {
    transaction_id: 'TXN-002',
    customer_id: 'CUST-1102',
    amount: 45000,
    currency: 'NGN',
    timestamp: '2026-04-16T10:15:00',
    transaction_type: 'deposit',
    counterparty: 'Salary Payment',
    channel: 'web',
  },
  {
    transaction_id: 'TXN-003',
    customer_id: 'CUST-8834',
    amount: 2300000,
    currency: 'NGN',
    timestamp: '2026-04-16T23:58:00',
    transaction_type: 'withdrawal',
    counterparty: 'ATM Lagos',
    channel: 'atm',
  },
  {
    transaction_id: 'TXN-004',
    customer_id: 'CUST-3310',
    amount: 12000,
    currency: 'NGN',
    timestamp: '2026-04-16T14:22:00',
    transaction_type: 'transfer',
    counterparty: 'John Doe',
    channel: 'pos',
  },
  {
    transaction_id: 'TXN-005',
    customer_id: 'CUST-9901',
    amount: 9800000,
    currency: 'NGN',
    timestamp: '2026-04-16T03:11:00',
    transaction_type: 'transfer',
    counterparty: 'Shell Company XYZ',
    channel: 'web',
  },
]

export default function AML() {
  const { authMode, hasAnyRole } = useAuth()
  const api = useApiClient()
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [str, setStr] = useState(null)
  const [strLoading, setStrLoading] = useState(null)
  const [error, setError] = useState('')
  const canGenerateSTR = hasAnyRole([USER_ROLES.ADMIN, USER_ROLES.COMPLIANCE_OFFICER])

  const runMonitor = async () => {
    setLoading(true)
    setError('')

    try {
      const { data } = await api.post('/api/aml/monitor', { transactions: SAMPLE_TRANSACTIONS })
      setResults(data)
    } catch (requestError) {
      if (authMode === 'mock') {
        setResults({
          total_analyzed: 5,
          flagged_count: 3,
          clean_count: 2,
          flagged_transactions: [
            {
              transaction_id: 'TXN-001',
              customer_id: 'CUST-4421',
              amount: 7500000,
              currency: 'NGN',
              timestamp: '2026-04-16T02:34:00',
              transaction_type: 'transfer',
              counterparty: 'Unknown Corp Ltd',
              channel: 'mobile',
              anomaly_score: -0.312,
              rules_triggered: ['LARGE_CASH_TRANSACTION', 'UNUSUAL_HOURS'],
              risk_level: 'HIGH',
              recommended_action: 'GENERATE_STR',
            },
            {
              transaction_id: 'TXN-003',
              customer_id: 'CUST-8834',
              amount: 2300000,
              currency: 'NGN',
              timestamp: '2026-04-16T23:58:00',
              transaction_type: 'withdrawal',
              counterparty: 'ATM Lagos',
              channel: 'atm',
              anomaly_score: -0.198,
              rules_triggered: ['UNUSUAL_HOURS'],
              risk_level: 'MEDIUM',
              recommended_action: 'REVIEW',
            },
            {
              transaction_id: 'TXN-005',
              customer_id: 'CUST-9901',
              amount: 9800000,
              currency: 'NGN',
              timestamp: '2026-04-16T03:11:00',
              transaction_type: 'transfer',
              counterparty: 'Shell Company XYZ',
              channel: 'web',
              anomaly_score: -0.421,
              rules_triggered: ['LARGE_CASH_TRANSACTION', 'UNUSUAL_HOURS', 'HIGH_VALUE_TRANSFER'],
              risk_level: 'HIGH',
              recommended_action: 'GENERATE_STR',
            },
          ],
        })
      } else {
        setError(getApiErrorMessage(requestError, 'AML monitoring failed.'))
      }
    }

    setLoading(false)
  }

  const generateSTR = async (transaction) => {
    setStrLoading(transaction.transaction_id)
    setError('')

    try {
      const { data } = await api.post(`/api/aml/generate-str/${transaction.transaction_id}`, transaction)
      setStr(data)
    } catch (requestError) {
      if (authMode === 'mock') {
        setStr({
          report_reference: `STR-${transaction.transaction_id.slice(-4).toUpperCase()}`,
          reporting_institution: 'WeGoComply Demo Bank',
          subject_name: transaction.customer_id,
          transaction_summary: `Customer conducted a ${transaction.transaction_type} of N${transaction.amount.toLocaleString()} via ${transaction.channel} at an unusual time.`,
          grounds_for_suspicion:
            'Transaction amount exceeds N5M threshold and occurred outside normal banking hours. Counterparty is an unverified entity.',
          recommended_action:
            'Freeze account pending investigation and file STR with NFIU within 24 hours.',
          report_date: '2026-04-16',
        })
      } else {
        setError(getApiErrorMessage(requestError, 'STR generation failed.'))
      }
    }

    setStrLoading(null)
  }

  const riskBadge = (level) =>
    ({
      HIGH: 'border border-red-800 bg-red-900/50 text-red-300',
      MEDIUM: 'border border-yellow-800 bg-yellow-900/50 text-yellow-300',
    }[level] || '')

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <AlertTriangle className="text-red-400" size={22} /> AML Transaction Monitor
        </h1>
        <p className="mt-1 text-sm text-gray-400">
          AI anomaly detection with auto STR generation for NFIU workflows
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-sm text-gray-400">
            Sample transaction batch ({SAMPLE_TRANSACTIONS.length} transactions)
          </span>
          <button
            onClick={runMonitor}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
          >
            <Play size={14} /> {loading ? 'Analyzing...' : 'Run Analysis'}
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-gray-400">
            <thead>
              <tr className="border-b border-gray-800">
                {['ID', 'Customer', 'Amount (N)', 'Type', 'Time', 'Channel'].map((heading) => (
                  <th key={heading} className="py-2 pr-4 text-left font-medium">
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {SAMPLE_TRANSACTIONS.map((transaction) => (
                <tr key={transaction.transaction_id} className="border-b border-gray-800/50">
                  <td className="py-2 pr-4">{transaction.transaction_id}</td>
                  <td className="py-2 pr-4">{transaction.customer_id}</td>
                  <td className="py-2 pr-4">{transaction.amount.toLocaleString()}</td>
                  <td className="py-2 pr-4">{transaction.transaction_type}</td>
                  <td className="py-2 pr-4">{transaction.timestamp.split('T')[1]}</td>
                  <td className="py-2 pr-4">{transaction.channel}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {results && (
        <div className="space-y-4">
          {!canGenerateSTR && (
            <div className="rounded-xl border border-yellow-900 bg-yellow-950/30 px-4 py-3 text-sm text-yellow-200">
              Your role can review flagged activity, but only admins and compliance officers can generate STRs.
            </div>
          )}

          <div className="grid grid-cols-3 gap-4">
            {[
              ['Analyzed', results.total_analyzed, 'text-blue-400'],
              ['Flagged', results.flagged_count, 'text-red-400'],
              ['Clean', results.clean_count, 'text-green-400'],
            ].map(([label, value, color]) => (
              <div key={label} className="rounded-xl border border-gray-800 bg-gray-900 p-4 text-center">
                <div className={`text-3xl font-bold ${color}`}>{value}</div>
                <div className="mt-1 text-xs text-gray-400">{label}</div>
              </div>
            ))}
          </div>

          <div className="space-y-3">
            {results.flagged_transactions.map((transaction) => (
              <div
                key={transaction.transaction_id}
                className="rounded-xl border border-gray-800 bg-gray-900 p-4"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm">{transaction.transaction_id}</span>
                      <span className={`rounded-full px-2 py-0.5 text-xs ${riskBadge(transaction.risk_level)}`}>
                        {transaction.risk_level}
                      </span>
                    </div>
                    <div className="mt-1 text-xs text-gray-400">
                      Customer: {transaction.customer_id} | N{transaction.amount.toLocaleString()} |{' '}
                      {transaction.timestamp}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {transaction.rules_triggered.map((rule) => (
                        <span
                          key={rule}
                          className="rounded bg-gray-800 px-2 py-0.5 text-xs text-gray-300"
                        >
                          {rule}
                        </span>
                      ))}
                    </div>
                  </div>
                  {transaction.recommended_action === 'GENERATE_STR' && canGenerateSTR && (
                    <button
                      onClick={() => generateSTR(transaction)}
                      disabled={strLoading === transaction.transaction_id}
                      className="ml-4 shrink-0 rounded-lg bg-red-700 px-3 py-1.5 text-xs text-white transition-colors hover:bg-red-600"
                    >
                      <span className="inline-flex items-center gap-1">
                        <FileText size={12} />
                        {strLoading === transaction.transaction_id ? 'Generating...' : 'Generate STR'}
                      </span>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {str && (
        <div className="space-y-3 rounded-xl border border-red-800 bg-gray-900 p-5">
          <div className="flex items-center gap-2 font-bold text-red-400">
            <FileText size={18} /> Suspicious Transaction Report (STR)
          </div>
          <div className="grid grid-cols-1 gap-2 text-sm">
            {Object.entries(str).map(([key, value]) => (
              <div key={key} className="rounded-lg bg-gray-800 p-3">
                <div className="text-xs capitalize text-gray-400">{key.replace(/_/g, ' ')}</div>
                <div className="mt-0.5 text-gray-200">{value}</div>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-500">
            Ready for submission to NFIU. Reference: {str.report_reference}
          </p>
        </div>
      )}
    </div>
  )
}
