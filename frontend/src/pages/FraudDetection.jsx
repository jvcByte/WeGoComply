import React, { useState } from 'react'
import { ShieldAlert, Play, Info, TrendingUp, AlertCircle } from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import { USER_ROLES } from '../auth/roles'
import { getApiErrorMessage, useApiClient } from '../lib/api'

const SAMPLE_TRANSACTIONS = [
  {
    step: 1, type: 'TRANSFER', amount: 9000000,
    oldbalanceOrg: 10000000, newbalanceOrig: 1000000,
    oldbalanceDest: 0, newbalanceDest: 9000000,
    isFlaggedFraud: 0, transaction_id: 'TXN-F001',
  },
  {
    step: 2, type: 'CASH_OUT', amount: 2500000,
    oldbalanceOrg: 3000000, newbalanceOrig: 500000,
    oldbalanceDest: 0, newbalanceDest: 2500000,
    isFlaggedFraud: 0, transaction_id: 'TXN-F002',
  },
  {
    step: 3, type: 'CASH_IN', amount: 50000,
    oldbalanceOrg: 100000, newbalanceOrig: 150000,
    oldbalanceDest: 0, newbalanceDest: 0,
    isFlaggedFraud: 0, transaction_id: 'TXN-F003',
  },
  {
    step: 4, type: 'PAYMENT', amount: 12000,
    oldbalanceOrg: 500000, newbalanceOrig: 488000,
    oldbalanceDest: 200000, newbalanceDest: 212000,
    isFlaggedFraud: 0, transaction_id: 'TXN-F004',
  },
  {
    step: 5, type: 'TRANSFER', amount: 7800000,
    oldbalanceOrg: 8000000, newbalanceOrig: 200000,
    oldbalanceDest: 0, newbalanceDest: 7800000,
    isFlaggedFraud: 1, transaction_id: 'TXN-F005',
  },
]

const RISK_STYLES = {
  'High Risk': { badge: 'border border-red-800 bg-red-900/50 text-red-300',    row: 'border-red-900/40 bg-red-950/20' },
  'Review':    { badge: 'border border-orange-800 bg-orange-900/50 text-orange-300', row: 'border-orange-900/40 bg-orange-950/20' },
  'Watch':     { badge: 'border border-yellow-800 bg-yellow-900/50 text-yellow-300', row: 'border-yellow-900/40 bg-yellow-950/20' },
  'Low Risk':  { badge: 'border border-green-800 bg-green-900/50 text-green-300',  row: 'border-gray-800 bg-gray-900' },
}

function RiskBar({ score }) {
  const pct   = Math.round(score * 100)
  const color = pct >= 75 ? 'bg-red-500' : pct >= 50 ? 'bg-orange-500' : pct >= 30 ? 'bg-yellow-500' : 'bg-green-500'
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-gray-700">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs tabular-nums text-gray-400">{pct}%</span>
    </div>
  )
}

export default function FraudDetection() {
  const { hasAnyRole } = useAuth()
  const api = useApiClient()

  const [results,      setResults]      = useState(null)
  const [loading,      setLoading]      = useState(false)
  const [error,        setError]        = useState('')
  const [explanation,  setExplanation]  = useState(null)
  const [explainLoading, setExplainLoading] = useState(null)
  const [modelInfo,    setModelInfo]    = useState(null)
  const [showInfo,     setShowInfo]     = useState(false)

  const canAnalyze = hasAnyRole([USER_ROLES.ADMIN, USER_ROLES.COMPLIANCE_OFFICER, USER_ROLES.ANALYST])

  const runAnalysis = async () => {
    setLoading(true); setError(''); setResults(null); setExplanation(null)
    try {
      const { data } = await api.post('/api/fraud/analyze', { transactions: SAMPLE_TRANSACTIONS })
      setResults(data)
    } catch (err) {
      setError(getApiErrorMessage(err, 'Fraud analysis failed.'))
    } finally {
      setLoading(false)
    }
  }

  const fetchExplanation = async (tx) => {
    setExplainLoading(tx.transaction_id); setExplanation(null)
    try {
      const { data } = await api.post('/api/fraud/explain', { transaction: tx })
      setExplanation(data)
    } catch (err) {
      setError(getApiErrorMessage(err, 'Could not fetch explanation.'))
    } finally {
      setExplainLoading(null)
    }
  }

  const fetchModelInfo = async () => {
    try {
      const { data } = await api.get('/api/fraud/model-info')
      setModelInfo(data); setShowInfo(true)
    } catch (err) {
      setError(getApiErrorMessage(err, 'Could not fetch model info.'))
    }
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <ShieldAlert className="text-orange-400" size={22} /> Fraud Detection
          </h1>
          <p className="mt-1 text-sm text-gray-400">
            XGBoost + Isolation Forest hybrid model — real-time fraud risk scoring
          </p>
        </div>
        <button
          onClick={fetchModelInfo}
          className="flex items-center gap-1.5 rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-xs text-gray-300 transition-colors hover:border-gray-600 hover:bg-gray-800"
        >
          <Info size={13} /> Model Info
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-200">{error}</div>
      )}

      {/* Model Info Panel */}
      {showInfo && modelInfo && (
        <div className="rounded-xl border border-blue-900 bg-blue-950/30 p-4 text-sm">
          <div className="mb-2 flex items-center justify-between">
            <span className="font-semibold text-blue-300">Model Details</span>
            <button onClick={() => setShowInfo(false)} className="text-xs text-gray-500 hover:text-gray-300">✕ Close</button>
          </div>
          {modelInfo.model_available ? (
            <div className="grid grid-cols-2 gap-x-8 gap-y-1 text-xs text-gray-300 sm:grid-cols-4">
              <div><span className="text-gray-500">Classifier</span><br />{modelInfo.classifier}</div>
              <div><span className="text-gray-500">ROC-AUC</span><br />{modelInfo.metrics?.roc_auc?.toFixed(4)}</div>
              <div><span className="text-gray-500">F2 Score</span><br />{modelInfo.metrics?.f2_score?.toFixed(4)}</div>
              <div><span className="text-gray-500">Training Rows</span><br />{modelInfo.training_info?.training_rows?.toLocaleString()}</div>
            </div>
          ) : (
            <p className="text-xs text-yellow-300">{modelInfo.message}</p>
          )}
        </div>
      )}

      {/* Transaction Table */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-sm text-gray-400">Sample batch ({SAMPLE_TRANSACTIONS.length} transactions)</span>
          <button
            onClick={runAnalysis}
            disabled={loading || !canAnalyze}
            className="flex items-center gap-2 rounded-lg bg-orange-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-orange-700 disabled:opacity-50"
          >
            <Play size={14} /> {loading ? 'Analyzing...' : 'Run Analysis'}
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-gray-400">
            <thead>
              <tr className="border-b border-gray-800">
                {['ID', 'Type', 'Amount', 'Origin Balance', 'Dest Balance', 'Flagged'].map((h) => (
                  <th key={h} className="py-2 pr-4 text-left font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {SAMPLE_TRANSACTIONS.map((tx) => (
                <tr key={tx.transaction_id} className="border-b border-gray-800/50">
                  <td className="py-2 pr-4 font-mono">{tx.transaction_id}</td>
                  <td className="py-2 pr-4">{tx.type}</td>
                  <td className="py-2 pr-4">{tx.amount.toLocaleString()}</td>
                  <td className="py-2 pr-4">{tx.oldbalanceOrg.toLocaleString()}</td>
                  <td className="py-2 pr-4">{tx.oldbalanceDest.toLocaleString()}</td>
                  <td className="py-2 pr-4">
                    {tx.isFlaggedFraud
                      ? <span className="rounded bg-red-900/50 px-1.5 py-0.5 text-red-300">Yes</span>
                      : <span className="text-gray-600">No</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Results */}
      {results && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              ['High Risk', results.high_risk_count,  'text-red-400'],
              ['Review',    results.review_count,     'text-orange-400'],
              ['Watch',     results.watch_count,      'text-yellow-400'],
              ['Low Risk',  results.low_risk_count,   'text-green-400'],
            ].map(([label, value, color]) => (
              <div key={label} className="rounded-xl border border-gray-800 bg-gray-900 p-4 text-center">
                <div className={`text-3xl font-bold ${color}`}>{value}</div>
                <div className="mt-1 text-xs text-gray-400">{label}</div>
              </div>
            ))}
          </div>

          {results.fraud_predicted_count > 0 && (
            <div className="flex items-center gap-3 rounded-xl border border-red-900 bg-red-950/30 px-4 py-3">
              <AlertCircle size={16} className="shrink-0 text-red-400" />
              <span className="text-sm text-red-200">
                <strong>{results.fraud_predicted_count}</strong> transaction{results.fraud_predicted_count > 1 ? 's' : ''} predicted as fraud by the ML model.
              </span>
            </div>
          )}

          {/* Per-transaction */}
          <div className="space-y-2">
            {results.transactions.map((tx) => {
              const styles = RISK_STYLES[tx.risk_band] || RISK_STYLES['Low Risk']
              return (
                <div key={tx.transaction_id} className={`rounded-xl border p-4 ${styles.row}`}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm text-gray-200">{tx.transaction_id}</span>
                        <span className={`rounded-full px-2 py-0.5 text-xs ${styles.badge}`}>{tx.risk_band}</span>
                        {tx.predicted_is_fraud === 1 && (
                          <span className="rounded-full border border-red-700 bg-red-900/60 px-2 py-0.5 text-xs text-red-300">
                            Fraud Predicted
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-gray-400">
                        {tx.type} · {tx.amount.toLocaleString()} · Origin: {tx.oldbalanceOrg.toLocaleString()} → {tx.newbalanceOrig.toLocaleString()}
                      </div>
                      <div className="flex flex-wrap items-center gap-4 pt-1">
                        {[
                          ['Classifier',    tx.classifier_score],
                          ['Anomaly',       tx.anomaly_score],
                          ['Combined Risk', tx.fraud_risk_score],
                        ].map(([label, score]) => (
                          <div key={label}>
                            <div className="mb-0.5 text-[10px] text-gray-500">{label}</div>
                            <RiskBar score={score} />
                          </div>
                        ))}
                      </div>
                    </div>
                    <button
                      onClick={() => fetchExplanation(tx)}
                      disabled={explainLoading === tx.transaction_id}
                      className="flex items-center gap-1.5 rounded-lg border border-gray-700 bg-gray-800 px-3 py-1.5 text-xs text-gray-300 transition-colors hover:border-gray-600 hover:bg-gray-700 disabled:opacity-50"
                    >
                      <TrendingUp size={12} />
                      {explainLoading === tx.transaction_id ? 'Loading...' : 'Explain'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Explanation */}
      {explanation && (
        <div className="rounded-xl border border-blue-800 bg-gray-900 p-5">
          <div className="mb-3 flex items-center gap-2 font-semibold text-blue-300">
            <TrendingUp size={16} /> Risk Factors — {explanation.transaction_id}
          </div>
          <ul className="space-y-2">
            {explanation.risk_factors.map((factor, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                <span className="mt-0.5 shrink-0 rounded-full bg-blue-900/60 px-1.5 py-0.5 text-[10px] text-blue-300">{i + 1}</span>
                {factor}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
