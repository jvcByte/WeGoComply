import React, { useState, useEffect } from 'react'
import { Bell, ExternalLink, RefreshCw } from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import { getApiErrorMessage, useApiClient } from '../lib/api'

const MOCK_UPDATES = [
  {
    id: 'CBN-2026-AML-001',
    source: 'CBN',
    title: 'Baseline Standards for Automated AML Solutions',
    date: '2026-03-15',
    url: '#',
    summary:
      'All financial institutions must implement real-time AML transaction monitoring by June 30, 2026.',
    action_required:
      'Deploy automated AML monitoring system and configure real-time STR filing within 24 hours of detection.',
    deadline: '2026-06-30',
    affected_operations: ['AML', 'Transaction Monitoring', 'STR Filing'],
    urgency: 'HIGH',
  },
  {
    id: 'FIRS-2026-TIN-002',
    source: 'FIRS',
    title: 'Mandatory TIN Verification for Financial Accounts',
    date: '2026-01-10',
    url: '#',
    summary:
      'Accounts without verified TINs will be restricted from transactions above N500,000 from April 1, 2026.',
    action_required:
      'Complete bulk TIN verification for all existing customers and enforce TIN collection for new onboarding.',
    deadline: '2026-04-01',
    affected_operations: ['KYC', 'Account Management', 'Tax Compliance'],
    urgency: 'HIGH',
  },
  {
    id: 'FCCPC-2026-DL-003',
    source: 'FCCPC',
    title: 'Digital Lender Registration Deadline',
    date: '2026-01-05',
    url: '#',
    summary:
      'All digital money lenders must complete FCCPC registration by April 30, 2026 or face delisting.',
    action_required:
      'Submit registration documents to FCCPC and ensure consumer protection compliance.',
    deadline: '2026-04-30',
    affected_operations: ['Digital Lending', 'Consumer Protection'],
    urgency: 'MEDIUM',
  },
  {
    id: 'CBN-2026-OB-004',
    source: 'CBN',
    title: 'Open Banking API Framework Go-Live',
    date: '2026-02-01',
    url: '#',
    summary:
      'Open Banking is now live in Nigeria. Only CBN-licensed entities may access standardized bank APIs.',
    action_required:
      'Ensure your institution is CBN-licensed before integrating Open Banking APIs.',
    deadline: null,
    affected_operations: ['API Integration', 'Data Sharing', 'Licensing'],
    urgency: 'MEDIUM',
  },
]

const urgencyStyle = {
  HIGH: 'border-red-800 bg-red-900/40 text-red-300',
  MEDIUM: 'border-yellow-800 bg-yellow-900/40 text-yellow-300',
  LOW: 'border-green-800 bg-green-900/40 text-green-300',
}

const sourceStyle = {
  CBN: 'bg-blue-900/50 text-blue-300',
  FIRS: 'bg-purple-900/50 text-purple-300',
  FCCPC: 'bg-orange-900/50 text-orange-300',
  SEC: 'bg-teal-900/50 text-teal-300',
}

export default function Regulatory() {
  const { authMode } = useAuth()
  const api = useApiClient()
  const [updates, setUpdates] = useState([])
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState('ALL')
  const [error, setError] = useState('')

  const fetchUpdates = async () => {
    setLoading(true)
    setError('')

    try {
      const { data } = await api.get('/api/regulatory/updates')
      setUpdates(data.updates)
    } catch (requestError) {
      if (authMode === 'mock') {
        setUpdates(MOCK_UPDATES)
      } else {
        setUpdates([])
        setError(getApiErrorMessage(requestError, 'Unable to load regulatory updates.'))
      }
    }

    setLoading(false)
  }

  useEffect(() => {
    fetchUpdates()
  }, [])

  const filtered = filter === 'ALL' ? updates : updates.filter((update) => update.urgency === filter)

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <Bell className="text-purple-400" size={22} /> Regulatory Intelligence
          </h1>
          <p className="mt-1 text-sm text-gray-400">
            AI-summarized CBN, FIRS, SEC, and FCCPC updates mapped to your operations
          </p>
        </div>
        <button
          onClick={fetchUpdates}
          disabled={loading}
          className="flex items-center gap-2 rounded-lg bg-gray-800 px-3 py-2 text-sm text-gray-400 transition-colors hover:text-white"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      <div className="flex gap-2">
        {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((item) => (
          <button
            key={item}
            onClick={() => setFilter(item)}
            className={`rounded-full px-3 py-1.5 text-xs transition-colors ${
              filter === item ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            {item}
          </button>
        ))}
      </div>

      <div className="space-y-4">
        {filtered.map((update) => (
          <div
            key={update.id}
            className={`rounded-xl border bg-gray-900 p-5 ${urgencyStyle[update.urgency]}`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`rounded px-2 py-0.5 text-xs font-bold ${
                      sourceStyle[update.source] || 'bg-gray-700 text-gray-300'
                    }`}
                  >
                    {update.source}
                  </span>
                  <span className="text-sm font-semibold">{update.title}</span>
                </div>
                <p className="mt-2 text-sm text-gray-300">{update.summary}</p>

                <div className="mt-3 rounded-lg bg-gray-800/60 p-3">
                  <div className="mb-1 text-xs text-gray-400">Action Required</div>
                  <p className="text-sm text-gray-200">{update.action_required}</p>
                </div>

                <div className="mt-3 flex flex-wrap items-center gap-4">
                  {update.deadline && (
                    <span className="text-xs text-gray-400">
                      Deadline: <span className="font-medium text-white">{update.deadline}</span>
                    </span>
                  )}
                  <div className="flex flex-wrap gap-1">
                    {update.affected_operations?.map((operation) => (
                      <span
                        key={operation}
                        className="rounded bg-gray-800 px-2 py-0.5 text-xs text-gray-400"
                      >
                        {operation}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex shrink-0 flex-col items-end gap-2">
                <span className={`rounded border px-2 py-0.5 text-xs font-bold ${urgencyStyle[update.urgency]}`}>
                  {update.urgency}
                </span>
                <span className="text-xs text-gray-500">{update.date}</span>
                <a
                  href={update.url}
                  className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
                >
                  Source <ExternalLink size={10} />
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
