import React, { useState, useEffect } from 'react'
import { Shield, AlertTriangle, TrendingUp, Clock, CheckCircle, XCircle, Info } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { useApiClient } from '../lib/api'

const COMPLIANCE_COLORS = {
  EXCELLENT: '#10b981',
  GOOD: '#3b82f6',
  FAIR: '#f59e0b',
  POOR: '#f97316',
  CRITICAL: '#ef4444'
}

const PILLAR_COLORS = {
  KYC: '#8b5cf6',
  AML: '#06b6d4',
  TIN: '#10b981',
  Reporting: '#f59e0b'
}

export default function ComplianceDashboard() {
  const [complianceData, setComplianceData] = useState(null)
  const [metrics, setMetrics] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const api = useApiClient()

  useEffect(() => {
    fetchComplianceData()
  }, [])

  const fetchComplianceData = async () => {
    try {
      setLoading(true)
      
      // Fetch all metrics
      const [kycMetrics, amlMetrics, tinMetrics, reportingMetrics] = await Promise.all([
        api.get('/compliance/metrics/kyc'),
        api.get('/compliance/metrics/aml'),
        api.get('/compliance/metrics/tin'),
        api.get('/compliance/metrics/reporting')
      ])

      // Calculate compliance score
      const scoreResponse = await api.post('/compliance/score', {
        kyc_metrics: kycMetrics.data,
        aml_metrics: amlMetrics.data,
        tin_metrics: tinMetrics.data,
        reporting_metrics: reportingMetrics.data
      })

      setComplianceData(scoreResponse.data)
      setMetrics({
        kyc: kycMetrics.data,
        aml: amlMetrics.data,
        tin: tinMetrics.data,
        reporting: reportingMetrics.data
      })
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch compliance data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen grid place-items-center bg-gray-950 px-6 text-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <div>Loading compliance data...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen grid place-items-center bg-gray-950 px-6 text-gray-100">
        <div className="text-center max-w-md">
          <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <div className="text-red-400 mb-2">Error loading compliance data</div>
          <div className="text-gray-400 text-sm">{error}</div>
          <button 
            onClick={fetchComplianceData}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!complianceData) return null

  const { compliance_posture, pillar_breakdown, recommendations, critical_issues } = complianceData

  // Prepare chart data
  const pillarData = Object.entries(pillar_breakdown).map(([key, value]) => ({
    name: key,
    score: value.score,
    weight: value.weight,
    status: value.status
  }))

  const pieData = pillarData.map(item => ({
    name: item.name,
    value: item.score * parseFloat(item.weight) / 100,
    color: PILLAR_COLORS[item.name]
  }))

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Compliance Posture Score</h1>
        <p className="text-gray-400 text-sm mt-1">Real-time compliance monitoring across all 4 pillars</p>
      </div>

      {/* Critical Issues Alert */}
      {critical_issues.length > 0 && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="text-red-400 mt-1" size={20} />
            <div>
              <div className="text-red-400 font-semibold mb-2">Critical Issues Requiring Immediate Attention</div>
              <ul className="space-y-1">
                {critical_issues.map((issue, index) => (
                  <li key={index} className="text-red-300 text-sm">• {issue}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Overall Score */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <div className="text-center">
              <div 
                className="text-5xl font-bold mb-2"
                style={{ color: COMPLIANCE_COLORS[compliance_posture.compliance_level] }}
              >
                {compliance_posture.overall_score.toFixed(1)}
              </div>
              <div 
                className="text-sm font-semibold mb-4"
                style={{ color: COMPLIANCE_COLORS[compliance_posture.compliance_level] }}
              >
                {compliance_posture.compliance_level}
              </div>
              <div className="text-gray-400 text-xs">
                Last calculated: {new Date(compliance_posture.last_calculated).toLocaleString()}
              </div>
            </div>
          </div>
        </div>

        {/* Pillar Breakdown Chart */}
        <div className="lg:col-span-2">
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <h3 className="text-lg font-semibold mb-4">Pillar Breakdown</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={pillarData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" domain={[0, 100]} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                  labelStyle={{ color: '#f3f4f6' }}
                />
                <Bar dataKey="score" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Pillar Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Object.entries(pillar_breakdown).map(([key, value]) => (
          <div key={key} className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div 
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: PILLAR_COLORS[key] }}
                />
                <h3 className="text-lg font-semibold">{key}</h3>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold">{value.score.toFixed(1)}</div>
                <div className="text-sm text-gray-400">{value.weight}</div>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">Status</span>
                <span 
                  className="text-sm font-semibold"
                  style={{ color: COMPLIANCE_COLORS[value.status] }}
                >
                  {value.status}
                </span>
              </div>
              
              {Object.entries(value.metrics).map(([metric, val]) => (
                <div key={metric} className="flex justify-between items-center">
                  <span className="text-sm text-gray-400 capitalize">
                    {metric.replace(/_/g, ' ')}
                  </span>
                  <span className="text-sm font-semibold">
                    {typeof val === 'number' ? val.toFixed(1) : val}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <Info className="mr-2" size={20} />
            Recommendations
          </h3>
          <ul className="space-y-2">
            {recommendations.map((rec, index) => (
              <li key={index} className="flex items-start space-x-3">
                <CheckCircle className="text-blue-400 mt-1" size={16} />
                <span className="text-gray-300">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Weight Distribution */}
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
        <h3 className="text-lg font-semibold mb-4">Weight Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, value }) => `${name}: ${(value * 100).toFixed(1)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
