import React, { useState, useEffect } from 'react'
import { Bell, ExternalLink, RefreshCw, FileText, Send, ChevronDown, ChevronUp } from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import { getApiErrorMessage, useApiClient } from '../lib/api'

const MOCK_UPDATES = [
  { id: 'CBN-2026-AML-001', source: 'CBN', title: 'Baseline Standards for Automated AML Solutions', date: '2026-03-15', url: '#', summary: 'All financial institutions must implement real-time AML transaction monitoring by June 30, 2026.', action_required: 'Deploy automated AML monitoring system and configure real-time STR filing within 24 hours of detection.', deadline: '2026-06-30', affected_operations: ['AML', 'Transaction Monitoring', 'STR Filing'], urgency: 'HIGH' },
  { id: 'FIRS-2026-TIN-002', source: 'FIRS', title: 'Mandatory TIN Verification for Financial Accounts', date: '2026-01-10', url: '#', summary: 'Accounts without verified TINs will be restricted from transactions above ₦500,000 from April 1, 2026.', action_required: 'Complete bulk TIN verification for all existing customers and enforce TIN collection for new onboarding.', deadline: '2026-04-01', affected_operations: ['KYC', 'Account Management', 'Tax Compliance'], urgency: 'HIGH' },
  { id: 'FCCPC-2026-DL-003', source: 'FCCPC', title: 'Digital Lender Registration Deadline', date: '2026-01-05', url: '#', summary: 'All digital money lenders must complete FCCPC registration by April 30, 2026 or face delisting.', action_required: 'Submit registration documents to FCCPC and ensure consumer protection compliance.', deadline: '2026-04-30', affected_operations: ['Digital Lending', 'Consumer Protection'], urgency: 'MEDIUM' },
  { id: 'CBN-2026-OB-004', source: 'CBN', title: 'Open Banking API Framework Go-Live', date: '2026-02-01', url: '#', summary: 'Open Banking is now live in Nigeria. Only CBN-licensed entities may access standardized bank APIs.', action_required: 'Ensure your institution is CBN-licensed before integrating Open Banking APIs.', deadline: null, affected_operations: ['API Integration', 'Data Sharing', 'Licensing'], urgency: 'MEDIUM' },
]

const urgencyStyle = {
  HIGH:   'border-red-800 bg-red-900/40 text-red-300',
  MEDIUM: 'border-yellow-800 bg-yellow-900/40 text-yellow-300',
  LOW:    'border-green-800 bg-green-900/40 text-green-300',
}

const sourceStyle = {
  CBN:   'bg-blue-900/50 text-blue-300',
  FIRS:  'bg-purple-900/50 text-purple-300',
  FCCPC: 'bg-orange-900/50 text-orange-300',
  SEC:   'bg-teal-900/50 text-teal-300',
  NITDA: 'bg-pink-900/50 text-pink-300',
}

function UpdateCard({ update }) {
  const [expanded, setExpanded] = useState(false)
  const daysLeft = update.deadline
    ? Math.ceil((new Date(update.deadline) - new Date()) / 86400000)
    : null

  return (
    <div className={`rounded-xl border bg-gray-900 p-5 space-y-3 ${urgencyStyle[update.urgency]}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`text-xs font-bold px-2 py-0.5 rounded ${sourceStyle[update.source] || 'bg-gray-700 text-gray-300'}`}>
              {update.source}
            </span>
            <span className="text-sm font-semibold text-gray-100">{update.title}</span>
          </div>
          <p className="text-sm text-gray-300 mt-2">{update.summary}</p>

          <div className="mt-3 bg-gray-800/60 rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-1">Action Required</div>
            <p className="text-sm text-gray-200">{update.action_required}</p>
          </div>

          <div className="flex items-center gap-4 mt-3 flex-wrap">
            {update.deadline && (
              <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                daysLeft !== null && daysLeft < 0
                  ? 'bg-red-900/50 text-red-300'
                  : daysLeft !== null && daysLeft < 30
                  ? 'bg-yellow-900/50 text-yellow-300'
                  : 'bg-gray-800 text-gray-400'
              }`}>
                {daysLeft !== null && daysLeft < 0
                  ? `Deadline passed ${Math.abs(daysLeft)} days ago`
                  : daysLeft !== null
                  ? `${daysLeft} days remaining · ${update.deadline}`
                  : update.deadline
                }
              </span>
            )}
            <div className="flex gap-1 flex-wrap">
              {update.affected_operations?.map(op => (
                <span key={op} className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded">{op}</span>
              ))}
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          <span className={`text-xs font-bold px-2 py-0.5 rounded border ${urgencyStyle[update.urgency]}`}>
            {update.urgency}
          </span>
          <span className="text-xs text-gray-500">{update.date}</span>
          <a href={update.url} className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
            Source <ExternalLink size={10} />
          </a>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-gray-500 hover:text-gray-300 flex items-center gap-1"
          >
            {expanded ? <><ChevronUp size={12} /> Less</> : <><ChevronDown size={12} /> More</>}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-gray-800 pt-3 text-xs text-gray-500 space-y-1">
          <div>Circular ID: <span className="text-gray-400">{update.id}</span></div>
          <div>Published: <span className="text-gray-400">{update.date}</span></div>
          <div>Affected areas: <span className="text-gray-400">{update.affected_operations?.join(', ')}</span></div>
        </div>
      )}
    </div>
  )
}

function SummarizePanel({ api, authMode }) {
  const [text, setText] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSummarize = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const { data } = await api.post('/api/regulatory/summarize', { text })
      setResult(data)
    } catch (err) {
      if (authMode === 'mock') {
        setResult({
          summary: 'This circular introduces new compliance requirements for financial institutions operating in Nigeria.',
          action_required: 'Review your current systems and ensure compliance before the stated deadline.',
          deadline: null,
          affected_operations: ['Compliance', 'Operations'],
          urgency: 'MEDIUM',
        })
      } else {
        setError(getApiErrorMessage(err, 'Summarization failed.'))
      }
    }
    setLoading(false)
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5 space-y-4">
      <div className="flex items-center gap-2">
        <FileText size={16} className="text-purple-400" />
        <span className="font-semibold text-sm text-gray-200">Summarize a Circular</span>
        <span className="text-xs text-gray-500 ml-1">— paste any CBN/FIRS/SEC document</span>
      </div>

      <form onSubmit={handleSummarize} className="space-y-3">
        <textarea
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-purple-500 resize-none"
          rows={5}
          placeholder="Paste the full text of a regulatory circular here..."
          value={text}
          onChange={e => setText(e.target.value)}
          required
          minLength={20}
        />
        {error && <div className="text-xs text-red-400">{error}</div>}
        <button
          type="submit"
          disabled={loading || text.length < 20}
          className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
        >
          <Send size={14} />
          {loading ? 'Summarizing with AI...' : 'Summarize'}
        </button>
      </form>

      {result && (
        <div className={`rounded-lg border p-4 space-y-3 ${urgencyStyle[result.urgency]}`}>
          <div className="flex items-center gap-2">
            <span className={`text-xs font-bold px-2 py-0.5 rounded border ${urgencyStyle[result.urgency]}`}>
              {result.urgency}
            </span>
            {result.deadline && (
              <span className="text-xs text-gray-400">Deadline: <span className="text-white">{result.deadline}</span></span>
            )}
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-1">Summary</div>
            <p className="text-sm text-gray-200">{result.summary}</p>
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-1">Action Required</div>
            <p className="text-sm text-gray-200">{result.action_required}</p>
          </div>
          <div className="flex gap-1 flex-wrap">
            {result.affected_operations?.map(op => (
              <span key={op} className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded">{op}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function Regulatory() {
  const { authMode } = useAuth()
  const api = useApiClient()
  const [updates, setUpdates] = useState([])
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState('ALL')
  const [error, setError] = useState('')
  const [tab, setTab] = useState('feed') // feed | summarize

  const fetchUpdates = async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.get('/api/regulatory/updates')
      setUpdates(data.updates)
    } catch (err) {
      if (authMode === 'mock') {
        setUpdates(MOCK_UPDATES)
      } else {
        setUpdates([])
        setError(getApiErrorMessage(err, 'Unable to load regulatory updates.'))
      }
    }
    setLoading(false)
  }

  useEffect(() => { fetchUpdates() }, [])

  const filtered = filter === 'ALL' ? updates : updates.filter(u => u.urgency === filter)

  const counts = updates.reduce((acc, u) => {
    acc[u.urgency] = (acc[u.urgency] || 0) + 1
    return acc
  }, {})

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bell className="text-purple-400" size={22} /> Regulatory Intelligence
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            AI-summarized CBN, FIRS, SEC, FCCPC, and NITDA updates mapped to your operations
          </p>
        </div>
        <button
          onClick={fetchUpdates}
          disabled={loading}
          className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-sm text-gray-400 hover:text-white px-3 py-2 rounded-lg transition-colors"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2">
        {[
          { id: 'feed', label: 'Regulatory Feed' },
          { id: 'summarize', label: 'Summarize Circular' },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`text-sm px-4 py-2 rounded-lg transition-colors ${
              tab === t.id ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'summarize' ? (
        <SummarizePanel api={api} authMode={authMode} />
      ) : (
        <>
          {/* Filter with counts */}
          <div className="flex gap-2 flex-wrap">
            {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`text-xs px-3 py-1.5 rounded-full transition-colors flex items-center gap-1.5 ${
                  filter === f ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'
                }`}
              >
                {f}
                {f !== 'ALL' && counts[f] && (
                  <span className={`text-xs rounded-full px-1.5 ${
                    f === 'HIGH' ? 'bg-red-700' : f === 'MEDIUM' ? 'bg-yellow-700' : 'bg-green-700'
                  } text-white`}>
                    {counts[f]}
                  </span>
                )}
              </button>
            ))}
            <span className="text-xs text-gray-500 self-center ml-2">
              {filtered.length} update{filtered.length !== 1 ? 's' : ''}
            </span>
          </div>

          <div className="space-y-4">
            {filtered.map(update => (
              <UpdateCard key={update.id} update={update} />
            ))}
            {filtered.length === 0 && (
              <div className="text-center text-gray-500 text-sm py-8">
                No {filter !== 'ALL' ? filter.toLowerCase() + ' urgency ' : ''}updates found.
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
