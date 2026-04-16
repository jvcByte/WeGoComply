import React, { useState, useEffect } from 'react'
import { Bell, ExternalLink, RefreshCw } from 'lucide-react'
import axios from 'axios'

const MOCK_UPDATES = [
  {
    id: 'CBN-2026-AML-001', source: 'CBN', title: 'Baseline Standards for Automated AML Solutions',
    date: '2026-03-15', url: '#',
    summary: 'All financial institutions must implement real-time AML transaction monitoring by June 30, 2026.',
    action_required: 'Deploy automated AML monitoring system and configure real-time STR filing within 24 hours of detection.',
    deadline: '2026-06-30',
    affected_operations: ['AML', 'Transaction Monitoring', 'STR Filing'],
    urgency: 'HIGH'
  },
  {
    id: 'FIRS-2026-TIN-002', source: 'FIRS', title: 'Mandatory TIN Verification for Financial Accounts',
    date: '2026-01-10', url: '#',
    summary: 'Accounts without verified TINs will be restricted from transactions above ₦500,000 from April 1, 2026.',
    action_required: 'Complete bulk TIN verification for all existing customers and enforce TIN collection for new onboarding.',
    deadline: '2026-04-01',
    affected_operations: ['KYC', 'Account Management', 'Tax Compliance'],
    urgency: 'HIGH'
  },
  {
    id: 'FCCPC-2026-DL-003', source: 'FCCPC', title: 'Digital Lender Registration Deadline',
    date: '2026-01-05', url: '#',
    summary: 'All digital money lenders must complete FCCPC registration by April 30, 2026 or face delisting.',
    action_required: 'Submit registration documents to FCCPC and ensure consumer protection compliance.',
    deadline: '2026-04-30',
    affected_operations: ['Digital Lending', 'Consumer Protection'],
    urgency: 'MEDIUM'
  },
  {
    id: 'CBN-2026-OB-004', source: 'CBN', title: 'Open Banking API Framework Go-Live',
    date: '2026-02-01', url: '#',
    summary: 'Open Banking is now live in Nigeria. Only CBN-licensed entities may access standardized bank APIs.',
    action_required: 'Ensure your institution is CBN-licensed before integrating Open Banking APIs.',
    deadline: null,
    affected_operations: ['API Integration', 'Data Sharing', 'Licensing'],
    urgency: 'MEDIUM'
  },
]

const urgencyStyle = {
  HIGH: 'bg-red-900/40 text-red-300 border-red-800',
  MEDIUM: 'bg-yellow-900/40 text-yellow-300 border-yellow-800',
  LOW: 'bg-green-900/40 text-green-300 border-green-800',
}

const sourceStyle = {
  CBN: 'bg-blue-900/50 text-blue-300',
  FIRS: 'bg-purple-900/50 text-purple-300',
  FCCPC: 'bg-orange-900/50 text-orange-300',
  SEC: 'bg-teal-900/50 text-teal-300',
}

export default function Regulatory() {
  const [updates, setUpdates] = useState([])
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState('ALL')

  const fetchUpdates = async () => {
    setLoading(true)
    try {
      const { data } = await axios.get('/api/regulatory/updates')
      setUpdates(data.updates)
    } catch {
      setUpdates(MOCK_UPDATES)
    }
    setLoading(false)
  }

  useEffect(() => { fetchUpdates() }, [])

  const filtered = filter === 'ALL' ? updates : updates.filter(u => u.urgency === filter)

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bell className="text-purple-400" size={22} /> Regulatory Intelligence
          </h1>
          <p className="text-gray-400 text-sm mt-1">AI-summarized CBN, FIRS, SEC, and FCCPC updates mapped to your operations</p>
        </div>
        <button
          onClick={fetchUpdates}
          disabled={loading}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-white bg-gray-800 px-3 py-2 rounded-lg transition-colors"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      <div className="flex gap-2">
        {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`text-xs px-3 py-1.5 rounded-full transition-colors ${filter === f ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'}`}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="space-y-4">
        {filtered.map(update => (
          <div key={update.id} className={`bg-gray-900 rounded-xl p-5 border ${urgencyStyle[update.urgency]}`}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`text-xs font-bold px-2 py-0.5 rounded ${sourceStyle[update.source] || 'bg-gray-700 text-gray-300'}`}>
                    {update.source}
                  </span>
                  <span className="font-semibold text-sm">{update.title}</span>
                </div>
                <p className="text-sm text-gray-300 mt-2">{update.summary}</p>

                <div className="mt-3 bg-gray-800/60 rounded-lg p-3">
                  <div className="text-xs text-gray-400 mb-1">Action Required</div>
                  <p className="text-sm text-gray-200">{update.action_required}</p>
                </div>

                <div className="flex items-center gap-4 mt-3 flex-wrap">
                  {update.deadline && (
                    <span className="text-xs text-gray-400">
                      Deadline: <span className="text-white font-medium">{update.deadline}</span>
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
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
