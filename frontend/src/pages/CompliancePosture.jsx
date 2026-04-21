import React, { useState, useEffect } from 'react'
import { Activity, Shield, AlertTriangle, FileText, TrendingUp } from 'lucide-react'
import { RadialBarChart, RadialBar, ResponsiveContainer, Tooltip } from 'recharts'
import axios from 'axios'

const INSTITUTIONS = [
  { id: 'inst-moniepoint', name: 'Moniepoint MFB' },
  { id: 'inst-kuda',       name: 'Kuda Bank' },
  { id: 'inst-opay',       name: 'OPay Digital Services' },
]

const statusStyle = {
  'COMPLIANT':     'bg-green-900/40 text-green-300 border border-green-700',
  'AT RISK':       'bg-yellow-900/40 text-yellow-300 border border-yellow-700',
  'NON-COMPLIANT': 'bg-red-900/40 text-red-300 border border-red-700',
}

const priorityStyle = {
  CRITICAL: 'bg-red-900/50 text-red-300',
  HIGH:     'bg-orange-900/50 text-orange-300',
  MEDIUM:   'bg-yellow-900/50 text-yellow-300',
}

const pillarIcon = {
  kyc:       Shield,
  aml:       AlertTriangle,
  tin:       FileText,
  reporting: Activity,
}

function ScoreGauge({ score, status }) {
  const color = score >= 80 ? '#22c55e' : score >= 60 ? '#eab308' : '#ef4444'
  const data = [{ value: score, fill: color }]
  return (
    <div className="relative w-40 h-40">
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart innerRadius="70%" outerRadius="100%" data={data}
          startAngle={180} endAngle={-180}>
          <RadialBar dataKey="value" cornerRadius={8} background={{ fill: '#1f2937' }} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold" style={{ color }}>{score}</span>
        <span className="text-xs text-gray-400">/100</span>
      </div>
    </div>
  )
}

export default function CompliancePosture() {
  const [selected, setSelected] = useState('inst-moniepoint')
  const [posture, setPosture] = useState(null)
  const [loading, setLoading] = useState(false)
  const [view, setView] = useState('institution') // institution | suptech

  const fetchPosture = async (id) => {
    setLoading(true)
    try {
      const { data } = await axios.get(`/api/compliance/posture/${id}`)
      setPosture(data)
    } catch {
      // Demo fallback
      setPosture(MOCK_POSTURE[id] || MOCK_POSTURE['inst-moniepoint'])
    }
    setLoading(false)
  }

  useEffect(() => { fetchPosture(selected) }, [selected])

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <TrendingUp className="text-blue-400" size={22} /> Compliance Posture
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Real-time compliance scoring across KYC, AML, TIN, and Regulatory Reporting
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setView('institution')}
            className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${view === 'institution' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400'}`}>
            Institution View
          </button>
          <button onClick={() => setView('suptech')}
            className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${view === 'suptech' ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400'}`}>
            SupTech View (Regulator)
          </button>
        </div>
      </div>

      {view === 'institution' ? (
        <InstitutionView
          institutions={INSTITUTIONS}
          selected={selected}
          setSelected={(id) => { setSelected(id); fetchPosture(id) }}
          posture={posture}
          loading={loading}
        />
      ) : (
        <SupTechView />
      )}
    </div>
  )
}

function InstitutionView({ institutions, selected, setSelected, posture, loading }) {
  return (
    <div className="space-y-6">
      {/* Institution selector */}
      <div className="flex gap-2">
        {institutions.map(inst => (
          <button key={inst.id} onClick={() => setSelected(inst.id)}
            className={`text-sm px-4 py-2 rounded-lg transition-colors ${selected === inst.id ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'}`}>
            {inst.name}
          </button>
        ))}
      </div>

      {loading && <div className="text-gray-400 text-sm">Loading compliance data...</div>}

      {posture && !loading && (
        <>
          {/* Overall score */}
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 flex items-center gap-8">
            <ScoreGauge score={posture.overall_score} status={posture.status} />
            <div>
              <div className="text-2xl font-bold">{posture.institution_name}</div>
              <div className="text-sm text-gray-400 mt-1">{posture.institution_type} · {posture.cbn_license}</div>
              <span className={`inline-block mt-3 text-sm font-bold px-3 py-1 rounded-full ${statusStyle[posture.status]}`}>
                {posture.status}
              </span>
              <div className="text-xs text-gray-500 mt-2">As of {new Date(posture.as_of).toLocaleString()}</div>
            </div>
          </div>

          {/* Pillar scores */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(posture.pillars).map(([key, pillar]) => {
              const Icon = pillarIcon[key]
              const color = pillar.score >= 80 ? 'text-green-400' : pillar.score >= 60 ? 'text-yellow-400' : 'text-red-400'
              const bg    = pillar.score >= 80 ? 'bg-green-900/20' : pillar.score >= 60 ? 'bg-yellow-900/20' : 'bg-red-900/20'
              return (
                <div key={key} className="bg-gray-900 rounded-xl p-4 border border-gray-800">
                  <div className={`inline-flex p-2 rounded-lg ${bg} mb-2`}>
                    <Icon className={color} size={16} />
                  </div>
                  <div className={`text-2xl font-bold ${color}`}>{pillar.score}</div>
                  <div className="text-xs text-gray-400 mt-1">{pillar.label}</div>
                  <div className="text-xs text-gray-600 mt-0.5">{pillar.weight} weight</div>
                  <div className="text-xs text-gray-500 mt-1">{pillar.framework}</div>
                </div>
              )
            })}
          </div>

          {/* Pillar details */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {Object.entries(posture.pillars).map(([key, pillar]) => (
              <div key={key} className="bg-gray-900 rounded-xl p-4 border border-gray-800">
                <div className="text-sm font-semibold text-gray-300 mb-3">{pillar.label} — Details</div>
                <div className="space-y-2">
                  {Object.entries(pillar.details).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-xs">
                      <span className="text-gray-400 capitalize">{k.replace(/_/g, ' ')}</span>
                      <span className="text-gray-200 font-medium">{typeof v === 'number' ? v.toLocaleString() : v}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Action items */}
          {posture.action_items?.length > 0 && (
            <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
              <div className="text-sm font-semibold text-gray-300 mb-3">Action Items ({posture.action_items.length})</div>
              <div className="space-y-2">
                {posture.action_items.map((item, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 bg-gray-800 rounded-lg">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded shrink-0 ${priorityStyle[item.priority]}`}>
                      {item.priority}
                    </span>
                    <div className="flex-1">
                      <div className="text-sm text-gray-200">{item.action}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{item.framework} · Due: {item.deadline}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function SupTechView() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get('/api/compliance/suptech/report')
      .then(r => setReport(r.data))
      .catch(() => setReport(MOCK_SUPTECH))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-gray-400 text-sm">Loading sector data...</div>
  if (!report) return null

  return (
    <div className="space-y-6">
      <div className="bg-purple-900/20 border border-purple-800 rounded-xl p-4 text-sm text-purple-300">
        🏛 SupTech View — This dashboard is designed for CBN/NITDA regulators to monitor sector-wide compliance in real-time, replacing annual self-reporting.
      </div>

      {/* Sector summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          ['Total Institutions', report.summary.total_institutions, 'text-blue-400'],
          ['Sector Average', `${report.summary.sector_average_score}/100`, report.summary.sector_average_score >= 80 ? 'text-green-400' : 'text-yellow-400'],
          ['Compliant', report.summary.compliant_count, 'text-green-400'],
          ['At Risk', report.summary.at_risk_count, 'text-red-400'],
        ].map(([label, val, color]) => (
          <div key={label} className="bg-gray-900 rounded-xl p-4 border border-gray-800 text-center">
            <div className={`text-2xl font-bold ${color}`}>{val}</div>
            <div className="text-xs text-gray-400 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Regulator alerts */}
      {report.regulator_alerts?.length > 0 && (
        <div className="bg-gray-900 rounded-xl p-4 border border-red-900">
          <div className="text-sm font-semibold text-red-400 mb-3">⚠ Regulator Alerts</div>
          <div className="space-y-2">
            {report.regulator_alerts.map((alert, i) => (
              <div key={i} className={`p-3 rounded-lg text-sm ${alert.severity === 'CRITICAL' ? 'bg-red-900/30 text-red-300' : 'bg-yellow-900/30 text-yellow-300'}`}>
                <span className="font-bold">[{alert.severity}]</span> {alert.message}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Institution table */}
      <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
        <div className="text-sm font-semibold text-gray-300 mb-3">All Institutions — Compliance Posture</div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400">
                {['Institution', 'Type', 'Overall', 'KYC', 'AML', 'TIN', 'Reporting', 'Status'].map(h => (
                  <th key={h} className="text-left py-2 pr-4 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {report.institutions.map(inst => (
                <tr key={inst.institution_id} className="border-b border-gray-800/50">
                  <td className="py-2 pr-4 font-medium text-gray-200">{inst.name}</td>
                  <td className="py-2 pr-4 text-gray-400">{inst.type}</td>
                  <td className={`py-2 pr-4 font-bold ${inst.overall_score >= 80 ? 'text-green-400' : inst.overall_score >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {inst.overall_score}
                  </td>
                  <td className="py-2 pr-4 text-gray-300">{inst.kyc_score}</td>
                  <td className="py-2 pr-4 text-gray-300">{inst.aml_score}</td>
                  <td className="py-2 pr-4 text-gray-300">{inst.tin_score}</td>
                  <td className="py-2 pr-4 text-gray-300">{inst.reporting_score}</td>
                  <td className="py-2 pr-4">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${statusStyle[inst.status]}`}>
                      {inst.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Demo fallback data
// ---------------------------------------------------------------------------
const MOCK_POSTURE = {
  'inst-moniepoint': {
    institution_id: 'inst-moniepoint', institution_name: 'Moniepoint MFB',
    institution_type: 'FINTECH', cbn_license: 'MFB/2019/001',
    as_of: new Date().toISOString(), overall_score: 84.2, status: 'COMPLIANT', color: 'green',
    pillars: {
      kyc:       { score: 89.6, weight: '30%', label: 'KYC / Identity Verification', framework: 'CBN KYC Guidelines', details: { total_customers: '10,000,000', nin_rate: '92.0%', bvn_rate: '95.0%', face_rate: '88.0%', high_risk_unreviewed: 12, avg_onboarding_minutes: 2.3 } },
      aml:       { score: 83.5, weight: '35%', label: 'AML / Transaction Monitoring', framework: 'CBN AML/CFT Rules', details: { total_transactions_today: '1,500,000', monitoring_coverage: '100%', flagged_today: 23, review_rate: '91.3%', str_timeliness: '85.7%', strs_filed_late: 1 } },
      tin:       { score: 86.5, weight: '20%', label: 'Tax ID (TIN) Verification', framework: 'FIRS TIN Mandate', details: { total_customers: '10,000,000', tin_rate: '91.0%', accounts_restricted: '45,000', restriction_rate: '0.45%', deadline_status: 'PASSED' } },
      reporting: { score: 71.7, weight: '15%', label: 'Regulatory Reporting', framework: 'NITDA / CBN Reporting', details: { total_required_actions: 12, completed_actions: 10, pending_actions: 2, missed_deadlines: 0, completion_rate: '83.3%' } },
    },
    action_items: [
      { priority: 'HIGH', pillar: 'KYC', action: 'Review 12 HIGH risk customers within 24 hours', framework: 'CBN KYC Guidelines', deadline: '24 hours' },
      { priority: 'HIGH', pillar: 'AML', action: 'File 1 overdue STR with NFIU immediately', framework: 'NFIU STR Requirements', deadline: 'Immediate' },
      { priority: 'MEDIUM', pillar: 'Reporting', action: 'Complete 2 pending regulatory action items', framework: 'NITDA / CBN Reporting', deadline: 'This week' },
    ]
  },
  'inst-kuda': {
    institution_id: 'inst-kuda', institution_name: 'Kuda Bank',
    institution_type: 'FINTECH', cbn_license: 'MFB/2020/002',
    as_of: new Date().toISOString(), overall_score: 67.3, status: 'AT RISK', color: 'yellow',
    pillars: {
      kyc:       { score: 74.2, weight: '30%', label: 'KYC / Identity Verification', framework: 'CBN KYC Guidelines', details: { total_customers: '5,000,000', nin_rate: '82.0%', bvn_rate: '96.0%', face_rate: '78.0%', high_risk_unreviewed: 45, avg_onboarding_minutes: 3.1 } },
      aml:       { score: 58.3, weight: '35%', label: 'AML / Transaction Monitoring', framework: 'CBN AML/CFT Rules', details: { total_transactions_today: '800,000', monitoring_coverage: '90%', flagged_today: 15, review_rate: '60.0%', str_timeliness: '50.0%', strs_filed_late: 2 } },
      tin:       { score: 63.6, weight: '20%', label: 'Tax ID (TIN) Verification', framework: 'FIRS TIN Mandate', details: { total_customers: '5,000,000', tin_rate: '70.0%', accounts_restricted: '180,000', restriction_rate: '3.6%', deadline_status: 'PASSED' } },
      reporting: { score: 43.3, weight: '15%', label: 'Regulatory Reporting', framework: 'NITDA / CBN Reporting', details: { total_required_actions: 12, completed_actions: 7, pending_actions: 5, missed_deadlines: 1, completion_rate: '58.3%' } },
    },
    action_items: [
      { priority: 'CRITICAL', pillar: 'AML', action: 'File 2 overdue STRs with NFIU immediately', framework: 'NFIU STR Requirements', deadline: 'Immediate' },
      { priority: 'HIGH', pillar: 'KYC', action: 'Review 45 HIGH risk customers within 24 hours', framework: 'CBN KYC Guidelines', deadline: '24 hours' },
      { priority: 'HIGH', pillar: 'TIN', action: 'Verify TIN for 1,500,000 unverified customers', framework: 'FIRS TIN Mandate', deadline: 'Immediate' },
      { priority: 'HIGH', pillar: 'Reporting', action: 'Complete 5 pending regulatory action items', framework: 'NITDA / CBN Reporting', deadline: 'This week' },
    ]
  },
  'inst-opay': {
    institution_id: 'inst-opay', institution_name: 'OPay Digital Services',
    institution_type: 'PSP', cbn_license: 'PSP/2018/003',
    as_of: new Date().toISOString(), overall_score: 52.1, status: 'NON-COMPLIANT', color: 'red',
    pillars: {
      kyc:       { score: 63.4, weight: '30%', label: 'KYC / Identity Verification', framework: 'CBN KYC Guidelines', details: { total_customers: '35,000,000', nin_rate: '80.0%', bvn_rate: '85.7%', face_rate: '71.4%', high_risk_unreviewed: 120, avg_onboarding_minutes: 4.5 } },
      aml:       { score: 44.5, weight: '35%', label: 'AML / Transaction Monitoring', framework: 'CBN AML/CFT Rules', details: { total_transactions_today: '5,000,000', monitoring_coverage: '80%', flagged_today: 89, review_rate: '61.8%', str_timeliness: '63.6%', strs_filed_late: 8 } },
      tin:       { score: 50.3, weight: '20%', label: 'Tax ID (TIN) Verification', framework: 'FIRS TIN Mandate', details: { total_customers: '35,000,000', tin_rate: '62.9%', accounts_restricted: '850,000', restriction_rate: '2.43%', deadline_status: 'PASSED' } },
      reporting: { score: 26.7, weight: '15%', label: 'Regulatory Reporting', framework: 'NITDA / CBN Reporting', details: { total_required_actions: 12, completed_actions: 5, pending_actions: 7, missed_deadlines: 2, completion_rate: '41.7%' } },
    },
    action_items: [
      { priority: 'CRITICAL', pillar: 'AML', action: 'File 8 overdue STRs with NFIU immediately', framework: 'NFIU STR Requirements', deadline: 'Immediate' },
      { priority: 'HIGH', pillar: 'KYC', action: 'Review 120 HIGH risk customers within 24 hours', framework: 'CBN KYC Guidelines', deadline: '24 hours' },
      { priority: 'HIGH', pillar: 'TIN', action: 'Verify TIN for 13,000,000 unverified customers', framework: 'FIRS TIN Mandate', deadline: 'Immediate' },
      { priority: 'HIGH', pillar: 'Reporting', action: 'Complete 7 pending regulatory action items', framework: 'NITDA / CBN Reporting', deadline: 'This week' },
    ]
  }
}

const MOCK_SUPTECH = {
  report_type: 'SupTech Sector Compliance Report',
  as_of: new Date().toISOString(),
  frameworks_monitored: ['CBN AML/CFT Rules', 'CBN KYC Guidelines', 'FIRS TIN Mandate', 'NITDA Reporting Requirements'],
  summary: { total_institutions: 3, sector_average_score: 67.9, compliant_count: 1, at_risk_count: 2, sector_status: 'AT RISK' },
  institutions: [
    { institution_id: 'inst-opay',       name: 'OPay Digital Services', type: 'PSP',     overall_score: 52.1, kyc_score: 63.4, aml_score: 44.5, tin_score: 50.3, reporting_score: 26.7, status: 'NON-COMPLIANT', cbn_license: 'PSP/2018/003' },
    { institution_id: 'inst-kuda',       name: 'Kuda Bank',             type: 'FINTECH', overall_score: 67.3, kyc_score: 74.2, aml_score: 58.3, tin_score: 63.6, reporting_score: 43.3, status: 'AT RISK',       cbn_license: 'MFB/2020/002' },
    { institution_id: 'inst-moniepoint', name: 'Moniepoint MFB',        type: 'FINTECH', overall_score: 84.2, kyc_score: 89.6, aml_score: 83.5, tin_score: 86.5, reporting_score: 71.7, status: 'COMPLIANT',     cbn_license: 'MFB/2019/001' },
  ],
  regulator_alerts: [
    { severity: 'CRITICAL', institution: 'OPay Digital Services', score: 52.1, message: 'OPay Digital Services compliance score is critically low (52.1/100). Immediate regulatory intervention recommended.' },
    { severity: 'WARNING',  institution: 'Kuda Bank',             score: 67.3, message: 'Kuda Bank compliance score is below acceptable threshold (67.3/100). Follow-up required.' },
  ]
}
