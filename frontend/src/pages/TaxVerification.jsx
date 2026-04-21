import React, { useState } from 'react'
import {
  FileText, Upload, CheckCircle, XCircle, AlertTriangle,
  Search, RefreshCw, ExternalLink, Info
} from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import { getApiErrorMessage, useApiClient } from '../lib/api'

// ---------------------------------------------------------------------------
// Sample data
// ---------------------------------------------------------------------------
const SAMPLE_RECORDS = [
  { customer_id: 'CUST-001', name: 'Adaeze Okonkwo',  tin: '1234567890' },
  { customer_id: 'CUST-002', name: 'Emeka Nwosu',     tin: '0987654321' },
  { customer_id: 'CUST-003', name: 'Fatima Aliyu',    tin: '1122334455' },
  { customer_id: 'CUST-004', name: 'Chukwuemeka Eze', tin: '5566778899' },
  { customer_id: 'CUST-005', name: 'Ngozi Adeyemi',   tin: '9988776655' },
]

const MOCK_BULK_RESULT = (() => {
  const records = SAMPLE_RECORDS.map((r, i) => ({
    customer_id: r.customer_id,
    tin: r.tin,
    status: i === 2 ? 'NOT_FOUND' : i === 4 ? 'NOT_FOUND' : 'MATCHED',
    firs_name: i === 2 || i === 4 ? '' : r.name,
    submitted_name: r.name,
    match_confidence: i === 2 || i === 4 ? 0 : 0.95,
  }))
  const matched = records.filter(r => r.status === 'MATCHED').length
  return {
    total: 5, matched, failed: 5 - matched,
    match_rate: ((matched / 5) * 100).toFixed(1),
    deadline_risk: matched / 5 < 0.8 ? 'HIGH' : 'LOW',
    records,
  }
})()

// ---------------------------------------------------------------------------
// Status badge
// ---------------------------------------------------------------------------
function StatusBadge({ status }) {
  const styles = {
    MATCHED:        'bg-green-900/50 text-green-300 border border-green-800',
    NOT_FOUND:      'bg-red-900/50 text-red-300 border border-red-800',
    NAME_MISMATCH:  'bg-yellow-900/50 text-yellow-300 border border-yellow-800',
  }
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${styles[status] || ''}`}>
      {status}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Single TIN Verify panel
// ---------------------------------------------------------------------------
function SingleVerify({ api, authMode }) {
  const [form, setForm] = useState({ customer_id: '', name: '', tin: '' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleVerify = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const { data } = await api.post('/api/tax/verify-tin', form)
      setResult(data)
    } catch (err) {
      if (authMode === 'mock') {
        const tin = form.tin
        setResult({
          customer_id: form.customer_id,
          tin,
          status: tin.endsWith('55') ? 'NOT_FOUND' : tin.endsWith('99') ? 'NAME_MISMATCH' : 'MATCHED',
          firs_name: tin.endsWith('55') ? '' : tin.endsWith('99') ? `${form.name.split(' ')[0]} Holdings Ltd` : form.name,
          submitted_name: form.name,
          match_confidence: tin.endsWith('55') ? 0 : tin.endsWith('99') ? 0.62 : 0.95,
        })
      } else {
        setError(getApiErrorMessage(err, 'TIN verification failed.'))
      }
    }
    setLoading(false)
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5 space-y-4">
      <div className="flex items-center gap-2">
        <Search size={16} className="text-yellow-400" />
        <span className="font-semibold text-sm text-gray-200">Single TIN Verification</span>
        <span className="ml-auto text-xs text-gray-500">FIRS ATRS API</span>
      </div>

      <form onSubmit={handleVerify} className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <label className="text-xs text-gray-400 block mb-1">Customer ID</label>
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-yellow-500"
            placeholder="CUST-001"
            value={form.customer_id}
            onChange={e => setForm({ ...form, customer_id: e.target.value })}
            required
          />
        </div>
        <div>
          <label className="text-xs text-gray-400 block mb-1">Full Name</label>
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-yellow-500"
            placeholder="Adaeze Okonkwo"
            value={form.name}
            onChange={e => setForm({ ...form, name: e.target.value })}
            required
          />
        </div>
        <div>
          <label className="text-xs text-gray-400 block mb-1">TIN (10 digits)</label>
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-yellow-500"
            placeholder="1234567890"
            value={form.tin}
            onChange={e => setForm({ ...form, tin: e.target.value })}
            pattern="\d{10,15}"
            required
          />
        </div>
        <div className="md:col-span-3">
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
          >
            {loading
              ? <><RefreshCw size={14} className="animate-spin" /> Verifying with FIRS...</>
              : <><Search size={14} /> Verify TIN</>
            }
          </button>
        </div>
      </form>

      {error && (
        <div className="rounded-lg border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-200">
          {error}
        </div>
      )}

      {result && (
        <div className={`rounded-lg p-4 border space-y-3 ${
          result.status === 'MATCHED'
            ? 'border-green-800 bg-green-900/20'
            : result.status === 'NAME_MISMATCH'
            ? 'border-yellow-800 bg-yellow-900/20'
            : 'border-red-800 bg-red-900/20'
        }`}>
          <div className="flex items-center gap-3">
            {result.status === 'MATCHED'
              ? <CheckCircle className="text-green-400" size={20} />
              : result.status === 'NAME_MISMATCH'
              ? <AlertTriangle className="text-yellow-400" size={20} />
              : <XCircle className="text-red-400" size={20} />
            }
            <div>
              <StatusBadge status={result.status} />
              <span className="ml-2 text-sm text-gray-300">
                {result.status === 'MATCHED' && 'TIN verified against FIRS ATRS'}
                {result.status === 'NOT_FOUND' && 'TIN not found in FIRS database'}
                {result.status === 'NAME_MISMATCH' && 'TIN found but name does not match'}
              </span>
            </div>
            <span className="ml-auto text-xs text-gray-500">
              Confidence: {(result.match_confidence * 100).toFixed(0)}%
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            {[
              ['Customer ID', result.customer_id],
              ['TIN', result.tin],
              ['Submitted Name', result.submitted_name],
              ['FIRS Name', result.firs_name || '—'],
            ].map(([label, value]) => (
              <div key={label} className="bg-gray-800/60 rounded-lg p-2">
                <div className="text-gray-500">{label}</div>
                <div className="text-gray-200 font-medium mt-0.5">{value}</div>
              </div>
            ))}
          </div>

          {result.status === 'NOT_FOUND' && (
            <div className="flex items-start gap-2 bg-gray-800/60 rounded-lg p-3 text-xs text-gray-300">
              <Info size={14} className="text-blue-400 shrink-0 mt-0.5" />
              <span>
                Customer must register for a free TIN at{' '}
                <a href="https://jtb.gov.ng" target="_blank" rel="noreferrer"
                  className="text-blue-400 hover:underline inline-flex items-center gap-1">
                  jtb.gov.ng <ExternalLink size={10} />
                </a>
                {' '}— takes 5 minutes with NIN.
              </span>
            </div>
          )}

          {result.status === 'NAME_MISMATCH' && (
            <div className="flex items-start gap-2 bg-gray-800/60 rounded-lg p-3 text-xs text-gray-300">
              <Info size={14} className="text-yellow-400 shrink-0 mt-0.5" />
              <span>
                Name mismatch detected. Customer must update their legal name with FIRS at{' '}
                <a href="https://taxpromax.firs.gov.ng" target="_blank" rel="noreferrer"
                  className="text-yellow-400 hover:underline inline-flex items-center gap-1">
                  taxpromax.firs.gov.ng <ExternalLink size={10} />
                </a>
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Bulk Verify panel
// ---------------------------------------------------------------------------
function BulkVerify({ api, authMode }) {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const runBulkVerify = async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post('/api/tax/bulk-verify', { records: SAMPLE_RECORDS })
      setResults(data)
    } catch (err) {
      if (authMode === 'mock') {
        setResults(MOCK_BULK_RESULT)
      } else {
        setError(getApiErrorMessage(err, 'Bulk TIN verification failed.'))
      }
    }
    setLoading(false)
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Upload size={16} className="text-yellow-400" />
          <span className="font-semibold text-sm text-gray-200">Bulk TIN Verification</span>
          <span className="text-xs text-gray-500 ml-1">— {SAMPLE_RECORDS.length} records</span>
        </div>
        <button
          onClick={runBulkVerify}
          disabled={loading}
          className="flex items-center gap-2 bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
        >
          {loading
            ? <><RefreshCw size={14} className="animate-spin" /> Verifying...</>
            : <><Upload size={14} /> Run Bulk Verification</>
          }
        </button>
      </div>

      {/* Records table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs text-gray-400">
          <thead>
            <tr className="border-b border-gray-800">
              {['Customer ID', 'Name', 'TIN', results ? 'Status' : ''].filter(Boolean).map(h => (
                <th key={h} className="text-left py-2 pr-4 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {SAMPLE_RECORDS.map((r, i) => {
              const res = results?.records[i]
              return (
                <tr key={r.customer_id} className="border-b border-gray-800/50">
                  <td className="py-2 pr-4">{r.customer_id}</td>
                  <td className="py-2 pr-4">{r.name}</td>
                  <td className="py-2 pr-4 font-mono">{r.tin}</td>
                  {results && (
                    <td className="py-2 pr-4">
                      <div className="flex items-center gap-2">
                        {res.status === 'MATCHED'
                          ? <CheckCircle className="text-green-400" size={14} />
                          : <XCircle className="text-red-400" size={14} />
                        }
                        <StatusBadge status={res.status} />
                        <span className="text-gray-500">{(res.match_confidence * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                  )}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {error && (
        <div className="rounded-lg border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-200">
          {error}
        </div>
      )}

      {results && (
        <div className="space-y-3">
          {/* Summary stats */}
          <div className="grid grid-cols-4 gap-3">
            {[
              ['Total', results.total, 'text-blue-400'],
              ['Matched', results.matched, 'text-green-400'],
              ['Failed', results.failed, 'text-red-400'],
              ['Match Rate', `${results.match_rate}%`, parseFloat(results.match_rate) >= 80 ? 'text-green-400' : 'text-red-400'],
            ].map(([label, value, color]) => (
              <div key={label} className="rounded-lg border border-gray-800 bg-gray-800/50 p-3 text-center">
                <div className={`text-xl font-bold ${color}`}>{value}</div>
                <div className="text-xs text-gray-500 mt-0.5">{label}</div>
              </div>
            ))}
          </div>

          {/* Deadline risk */}
          <div className={`rounded-lg border p-3 text-sm font-medium flex items-center gap-2 ${
            results.deadline_risk === 'HIGH'
              ? 'border-red-800 bg-red-900/30 text-red-300'
              : 'border-green-800 bg-green-900/30 text-green-300'
          }`}>
            {results.deadline_risk === 'HIGH'
              ? <AlertTriangle size={16} />
              : <CheckCircle size={16} />
            }
            Deadline Risk: {results.deadline_risk} —{' '}
            {results.deadline_risk === 'HIGH'
              ? 'Immediate action required. Send TIN registration links to failed customers.'
              : 'On track to meet FIRS mandate.'
            }
          </div>

          {/* Failed customers action */}
          {results.failed > 0 && (
            <div className="rounded-lg border border-blue-900 bg-blue-900/20 p-3 text-xs text-blue-300 space-y-1">
              <div className="font-semibold flex items-center gap-1">
                <Info size={13} /> Action Required for {results.failed} failed customer(s)
              </div>
              <div>Send the following message via SMS/email:</div>
              <div className="bg-gray-800 rounded p-2 text-gray-300 font-mono text-xs mt-1">
                "Your account has been flagged for missing Tax ID (TIN). Register free at jtb.gov.ng using your NIN. Takes 5 minutes. Deadline: April 1, 2026."
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// FIRS Connection Status
// ---------------------------------------------------------------------------
function FIRSStatus() {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
          <span className="text-sm font-medium text-gray-200">FIRS ATRS Connection</span>
          <span className="text-xs bg-yellow-900/40 text-yellow-300 border border-yellow-800 px-2 py-0.5 rounded-full">
            Mock Mode
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span>Dev: api-dev.i-fis.com</span>
          <span>Prod: atrs-api.firs.gov.ng</span>
          <a href="https://atrs.firs.gov.ng/getting-started/" target="_blank" rel="noreferrer"
            className="text-blue-400 hover:underline flex items-center gap-1">
            Get credentials <ExternalLink size={10} />
          </a>
        </div>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-3 text-xs">
        {[
          ['Auth', 'OAuth 2.0 Bearer Token', 'text-green-400'],
          ['Signing', 'MD5 SID (client_secret + fields)', 'text-blue-400'],
          ['Switch to Live', 'Set FIRS_MODE=live in .env', 'text-yellow-400'],
        ].map(([label, value, color]) => (
          <div key={label} className="bg-gray-800/60 rounded-lg p-2">
            <div className="text-gray-500">{label}</div>
            <div className={`${color} font-medium mt-0.5`}>{value}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
export default function TaxVerification() {
  const { authMode } = useAuth()
  const api = useApiClient()
  const [tab, setTab] = useState('bulk') // bulk | single

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <FileText className="text-yellow-400" size={22} /> Tax ID (TIN) Verification
        </h1>
        <p className="mt-1 text-sm text-gray-400">
          Verify customer TINs against FIRS ATRS — meet the mandate before sanctions apply
        </p>
      </div>

      {/* FIRS mandate banner */}
      <div className="rounded-xl border border-yellow-800 bg-yellow-900/20 p-4 text-sm text-yellow-300 flex items-start gap-3">
        <AlertTriangle size={18} className="shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold">FIRS Mandate Active:</span> Accounts without verified TINs
          are restricted from transactions above ₦500,000 effective April 1, 2026.
          Unverified customers must register at{' '}
          <a href="https://jtb.gov.ng" target="_blank" rel="noreferrer"
            className="underline hover:text-yellow-200 inline-flex items-center gap-1">
            jtb.gov.ng <ExternalLink size={11} />
          </a>
        </div>
      </div>

      {/* FIRS connection status */}
      <FIRSStatus />

      {/* Tab switcher */}
      <div className="flex gap-2">
        {[
          { id: 'bulk', label: 'Bulk Verification' },
          { id: 'single', label: 'Single Lookup' },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`text-sm px-4 py-2 rounded-lg transition-colors ${
              tab === t.id
                ? 'bg-yellow-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'bulk'
        ? <BulkVerify api={api} authMode={authMode} />
        : <SingleVerify api={api} authMode={authMode} />
      }

      {/* TIN Registration Guide */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-5 space-y-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-gray-200">
          <Info size={16} className="text-blue-400" />
          TIN Registration Guide (for customers without TIN)
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
          {[
            {
              step: '1',
              title: 'Visit JTB Portal',
              desc: 'Go to jtb.gov.ng and click "Register for TIN"',
              color: 'border-blue-800 bg-blue-900/20 text-blue-300',
            },
            {
              step: '2',
              title: 'Provide Details',
              desc: 'Enter full name (must match BVN), NIN, date of birth, phone, and state',
              color: 'border-yellow-800 bg-yellow-900/20 text-yellow-300',
            },
            {
              step: '3',
              title: 'Get TIN Instantly',
              desc: 'TIN is issued immediately. Free of charge. 10-digit number.',
              color: 'border-green-800 bg-green-900/20 text-green-300',
            },
          ].map(item => (
            <div key={item.step} className={`rounded-lg border p-3 ${item.color}`}>
              <div className="font-bold text-lg mb-1">Step {item.step}</div>
              <div className="font-semibold mb-1">{item.title}</div>
              <div className="opacity-80">{item.desc}</div>
            </div>
          ))}
        </div>
        <div className="flex gap-3 text-xs">
          <a href="https://jtb.gov.ng" target="_blank" rel="noreferrer"
            className="flex items-center gap-1 text-blue-400 hover:underline">
            JTB TIN Registration <ExternalLink size={10} />
          </a>
          <a href="https://taxpromax.firs.gov.ng" target="_blank" rel="noreferrer"
            className="flex items-center gap-1 text-blue-400 hover:underline">
            TaxPro Max (Annual Returns) <ExternalLink size={10} />
          </a>
          <a href="https://atrs.firs.gov.ng/getting-started/" target="_blank" rel="noreferrer"
            className="flex items-center gap-1 text-blue-400 hover:underline">
            FIRS ATRS API Access <ExternalLink size={10} />
          </a>
        </div>
      </div>
    </div>
  )
}
