import React from 'react'
import { Shield, AlertTriangle, CheckCircle, FileText } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'

const stats = [
  { label: 'KYC Verified Today', value: '1,284', change: '+12%', icon: Shield, color: 'text-green-400', bg: 'bg-green-900/30' },
  { label: 'Flagged Transactions', value: '23', change: '+3 new', icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-900/30' },
  { label: 'TIN Match Rate', value: '91.4%', change: '↑ from 87%', icon: CheckCircle, color: 'text-blue-400', bg: 'bg-blue-900/30' },
  { label: 'STRs Generated', value: '7', change: 'This week', icon: FileText, color: 'text-yellow-400', bg: 'bg-yellow-900/30' },
]

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
  { time: '08:00', verified: 45 }, { time: '10:00', verified: 120 },
  { time: '12:00', verified: 200 }, { time: '14:00', verified: 310 },
  { time: '16:00', verified: 420 }, { time: '18:00', verified: 480 },
]

export default function Dashboard() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Compliance Overview</h1>
        <p className="text-gray-400 text-sm mt-1">Real-time monitoring across KYC, AML, and Tax compliance</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s) => (
          <div key={s.label} className="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <div className={`inline-flex p-2 rounded-lg ${s.bg} mb-3`}>
              <s.icon className={s.color} size={18} />
            </div>
            <div className="text-2xl font-bold">{s.value}</div>
            <div className="text-xs text-gray-400 mt-1">{s.label}</div>
            <div className="text-xs text-gray-500 mt-1">{s.change}</div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <h2 className="text-sm font-semibold mb-4 text-gray-300">Transaction Monitoring (7 days)</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={txData}>
              <XAxis dataKey="day" tick={{ fill: '#9ca3af', fontSize: 12 }} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} />
              <Tooltip contentStyle={{ background: '#1f2937', border: 'none', borderRadius: 8 }} />
              <Bar dataKey="clean" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Clean" />
              <Bar dataKey="flagged" fill="#ef4444" radius={[4, 4, 0, 0]} name="Flagged" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <h2 className="text-sm font-semibold mb-4 text-gray-300">KYC Verifications Today</h2>
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

      {/* Regulatory alerts */}
      <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
        <h2 className="text-sm font-semibold mb-3 text-gray-300">Active Regulatory Alerts</h2>
        <div className="space-y-2">
          {[
            { source: 'CBN', msg: 'Real-time AML monitoring required by June 30, 2026', urgency: 'HIGH' },
            { source: 'FIRS', msg: 'TIN verification mandate — accounts restricted above ₦500k without TIN', urgency: 'HIGH' },
            { source: 'FCCPC', msg: 'Digital lender registration deadline: April 30, 2026', urgency: 'MEDIUM' },
          ].map((alert) => (
            <div key={alert.msg} className="flex items-start gap-3 p-3 bg-gray-800 rounded-lg">
              <span className={`text-xs font-bold px-2 py-0.5 rounded ${alert.urgency === 'HIGH' ? 'bg-red-900 text-red-300' : 'bg-yellow-900 text-yellow-300'}`}>
                {alert.source}
              </span>
              <span className="text-sm text-gray-300">{alert.msg}</span>
              <span className={`ml-auto text-xs ${alert.urgency === 'HIGH' ? 'text-red-400' : 'text-yellow-400'}`}>
                {alert.urgency}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
