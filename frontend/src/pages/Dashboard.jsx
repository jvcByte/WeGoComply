import React, { useState, useEffect } from 'react'
import { Shield, AlertTriangle, CheckCircle, FileText, TrendingUp, RefreshCw } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import { useApiClient } from '../lib/api'
import { useAuth } from '../auth/AuthProvider'

const txData = [
  { day: 'Mon', clean: 420, flagged: 4 },
  { day: 'Tue', clean: 380, flagged: 7 },
  { day: 'Wed', clean: 510, flagged: 2 },
  { day: 'Thu', clean: 460, flagged: 5 },
  { day: 'Fri', clean: 530, flagged: 3 },
  { day: 'Sat', clean: 290, flagged: 1 },
  { day: 'Sun', clean: 210, flagged: 1 },
]

const kycTrend = [
  { time: '08:00', verified: 45 },
  { time: '10:00', verified: 120 },
  { time: '12:00', verified: 200 },
  { time: '14:00', verified: 310 },
  { time: '16:00', verified: 420 },
  { time: '18:00', verified: 480 },
]

const MOCK_POSTURE = {
  overall_score: 84.2,
  status: 'COMPLIANT',
  pillars: {
    kyc:       { score: 89.6, details: { total_customers: 10000000, nin_rate: '92.0%', avg_onboarding_minutes: 2.3 } },
    aml:       { score: 83.5, details: { total_transactions_today: 1500000, flagged_today: 23, strs_filed_late: 1 } },
    tin:       { score: 86.5, details: { tin_rate: '91.0%', accounts_restricted: 45000 } },
    reporting: { score: 71.7, details: { completed_actions: 10, total_required_actions: 12 } },
  },
  action_items: [
    { priority: 'HIGH',   pillar: 'KYC',       action: 'Review 12 HIGH risk customers within 24 hours',    deadline: '24 hours' },
    { priority: 'HIGH',   pillar: 'AML',       action: 'File 1 overdue STR with NFIU immediately',          deadline: 'Immediate' },
    { priority: 'MEDIUM', pillar: 'Reporting', action: 'Complete 2 pending regulatory action items',        deadline: 'This week' },
  ],
}

const statusStyle = {
  COMPLIANT:       'text-green-400 bg-green-900/30 border border-green-800',
  'AT RISK':       'text-yellow-400 bg-yellow-900/30 border border-yellow-800',
  'NON-COMPLIANT': 'text-red-400 bg-red-900/30 border border-red-800',
}

const priorityStyle = {
  CRITICAL: 'bg-red-900/50 text-red-300',
  HIGH:     'bg-orange-900/50 text-orange-300',
  MEDIUM:   'bg-yellow-900/50 text-yellow-300',
}

const pillarColor = (score) =>
  score >= 80 ? 'text-green-400' : score >= 60 ? 'text-yellow-400' : 'text-red-400'

export default function Dashboard() {
  const { authMode } = useAuth()
  const api = useApiClient()
  const [posture, setPosture] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)

  const fetchPosture = async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/api/compliance/posture/inst-moniepoint')
      setPosture(data)
    } catch {
      setPosture(MOCK_POSTURE)
    }
    setLastUpdated(new Date().toLocaleTimeString())
    setLoading(false)
  }

  useEffect(() => { fetchPosture() }, [])

  const stats = posture ? [
    {
      label: 'KYC Score',
      value: `${posture.pillars.kyc.score}/100`,
      sub: `${posture.pillars.kyc.details.nin_rate || '—'} NIN verified`,
      icon: Shield,
      color: pillarColor(posture.pillars.kyc.score),
      bg: 'bg-blue-900/20',
    },
    {
      label: 'AML Score',
      value: `${posture.pillars.aml.score}/100`,
      sub: `${posture.pillars.aml.details.flagged_today || 0} flagged today`,
      icon: AlertTriangle,
      color: pillarColor(posture.pillars.aml.score),
      bg: 'bg-red-900/20',
    },
    {
      label: 'TIN Score',
      value: `${posture.pillars.tin.score}/100`,
      sub: `${posture.pillars.tin.details.tin_rate || '—'} verified`,
      icon: FileText,
      color: pillarColor(posture.pillars.tin.score),
      bg: 'bg-yellow-900/20',
    },
    {
      label: 'Overall Posture',
      value: `${posture.overall_score}/100`,
      sub: posture.status,
      icon: TrendingUp,
      color: pillarColor(posture.overall_score),
      bg: 'bg-purple-900/20',
    },
  ] : []

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">Compliance Overview</h1>
          <p className="text-sm text-gray-400 mt-1">
            Real-time monitoring across KYC, AML, and Tax compliance
          </p>
        </div>
        <div className="flex items-center gap-3">
          {lastUpdated && (
            <span className="text-xs text-gray-500">Updated {lastUpdated}</span>
          )}
          <button
            onClick={fetchPosture}
            disabled={loading}
            className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-sm text-gray-400 hover:text-white px-3 py-2 rounded-lg transition-colors"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Compliance posture banner */}
      {posture && (
        <div className={`rounded-xl border p-4 flex items-center gap-4 ${statusStyle[posture.status]}`}>
          <div>
            <div className="text-3xl font-bold">{posture.overall_score}</div>
            <div className="text-xs opacity-70">/ 100</div>
          </div>
          <div className="flex-1">
            <div className="font-semibold">{posture.status}</div>
            <div className="text-xs opacity-70 mt-0.5">
              Moniepoint MFB · Compliance Posture Score
            </div>
          </div>
          {posture.action_items?.length > 0 && (
            <div className="text-xs opacity-80">
              {posture.action_items.length} action item{posture.action_items.length !== 1 ? 's' : ''} pending
            </div>
          )}
        </div>
      )}

      {/* Pillar stats */}
      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[1,2,3,4].map(i => (
            <div key={i} className="bg-gray-900 rounded-xl p-4 border border-gray-800 animate-pulse h-24" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map(s => (
            <div key={s.label} className="bg-gray-900 rounded-xl p-4 border border-gray-800">
              <div className={`inline-flex p-2 rounded-lg ${s.bg} mb-3`}>
                <s.icon className={s.color} size={18} />
              </div>
              <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
              <div className="text-xs text-gray-400 mt-1">{s.label}</div>
              <div className="text-xs text-gray-500 mt-0.5">{s.sub}</div>
            </div>
          ))}
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <div className="text-sm font-semibold mb-4 text-gray-300">Transaction Monitoring (7 days)</div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={txData}>
              <XAxis dataKey="day" tick={{ fill: '#9ca3af', fontSize: 12 }} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} />
              <Tooltip contentStyle={{ background: '#1f2937', border: 'none', borderRadius: 8 }} />
              <Bar dataKey="clean" fill="#3b82f6" radius={[4,4,0,0]} name="Clean" />
              <Bar dataKey="flagged" fill="#ef4444" radius={[4,4,0,0]} name="Flagged" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <div className="text-sm font-semibold mb-4 text-gray-300">KYC Verifications Today</div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={kycTrend}>
              <XAxis dataKey="time" tick={{ fill: '#9ca3af', fontSize: 12 }} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} />
              <Tooltip contentStyle={{ background: '#1f2937', border: 'none', borderRadius: 8 }} />
              <Line type="monotone" dataKey="verified" stroke="#22c55e" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Action items from posture */}
      {posture?.action_items?.length > 0 && (
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <div className="text-sm font-semibold mb-3 text-gray-300">Pending Action Items</div>
          <div className="space-y-2">
            {posture.action_items.map((item, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-gray-800 rounded-lg">
                <span className={`text-xs font-bold px-2 py-0.5 rounded shrink-0 ${priorityStyle[item.priority]}`}>
                  {item.priority}
                </span>
                <div className="flex-1">
                  <div className="text-sm text-gray-200">{item.action}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{item.pillar} · Due: {item.deadline}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Regulatory alerts */}
      <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
        <div className="text-sm font-semibold mb-3 text-gray-300">Active Regulatory Alerts</div>
        <div className="space-y-2">
          {[
            { source: 'CBN',   msg: 'Real-time AML monitoring required by June 30, 2026',                    urgency: 'HIGH' },
            { source: 'FIRS',  msg: 'TIN verification mandate — accounts restricted above ₦500k without TIN', urgency: 'HIGH' },
            { source: 'FCCPC', msg: 'Digital lender registration deadline: April 30, 2026',                   urgency: 'MEDIUM' },
          ].map(alert => (
            <div key={alert.msg} className="flex items-start gap-3 p-3 bg-gray-800 rounded-lg">
              <span className={`text-xs font-bold px-2 py-0.5 rounded shrink-0 ${
                alert.urgency === 'HIGH' ? 'bg-red-900 text-red-300' : 'bg-yellow-900 text-yellow-300'
              }`}>
                {alert.source}
              </span>
              <span className="text-sm text-gray-300 flex-1">{alert.msg}</span>
              <span className={`text-xs shrink-0 ${alert.urgency === 'HIGH' ? 'text-red-400' : 'text-yellow-400'}`}>
                {alert.urgency}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
