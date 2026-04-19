import React, { useState } from 'react'
import { Shield, CheckCircle, XCircle, Loader } from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import { getApiErrorMessage, useApiClient } from '../lib/api'

export default function KYC() {
  const { authMode } = useAuth()
  const api = useApiClient()
  const [form, setForm] = useState({ nin: '', bvn: '' })
  const [selfie, setSelfie] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setResult(null)
    setError('')

    try {
      const formData = new FormData()
      formData.append('nin', form.nin)
      formData.append('bvn', form.bvn)
      if (selfie) formData.append('selfie', selfie)

      const { data } = await api.post('/api/kyc/verify', formData)
      setResult(data)
    } catch (requestError) {
      if (authMode === 'mock') {
        setResult({
          status: 'VERIFIED',
          risk_score: 0.12,
          risk_level: 'LOW',
          details: {
            nin_verified: true,
            bvn_verified: true,
            face_match: true,
            face_confidence: 0.94,
            name: 'Demo User',
            dob: '1990-01-01',
            phone: '080XXXXXXXX',
          },
        })
      } else {
        setError(getApiErrorMessage(requestError, 'KYC verification failed.'))
      }
    }

    setLoading(false)
  }

  const riskColor = {
    LOW: 'text-green-400 bg-green-900/30',
    MEDIUM: 'text-yellow-400 bg-yellow-900/30',
    HIGH: 'text-red-400 bg-red-900/30',
  }

  return (
    <div className="max-w-2xl space-y-6 p-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <Shield className="text-blue-500" size={22} /> KYC Verification
        </h1>
        <p className="mt-1 text-sm text-gray-400">
          Multi-source identity verification with AI risk scoring
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-gray-800 bg-gray-900 p-5">
        <div>
          <label className="mb-1 block text-sm text-gray-400">
            NIN (National Identification Number)
          </label>
          <input
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            placeholder="12345678901"
            value={form.nin}
            onChange={(event) => setForm({ ...form, nin: event.target.value })}
            required
          />
        </div>

        <div>
          <label className="mb-1 block text-sm text-gray-400">
            BVN (Bank Verification Number)
          </label>
          <input
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            placeholder="12345678901"
            value={form.bvn}
            onChange={(event) => setForm({ ...form, bvn: event.target.value })}
            required
          />
        </div>

        <div>
          <label className="mb-1 block text-sm text-gray-400">Selfie / Photo ID</label>
          <input
            type="file"
            accept="image/*"
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-400"
            required
            onChange={(event) => setSelfie(event.target.files[0])}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? (
            <>
              <Loader size={16} className="animate-spin" /> Verifying...
            </>
          ) : (
            'Verify Identity'
          )}
        </button>
      </form>

      {result && (
        <div className="space-y-4 rounded-xl border border-gray-800 bg-gray-900 p-5">
          <div className="flex items-center gap-3">
            {result.status === 'VERIFIED' ? (
              <CheckCircle className="text-green-400" size={24} />
            ) : (
              <XCircle className="text-red-400" size={24} />
            )}
            <div>
              <div className="text-lg font-bold">{result.status}</div>
              <div className="text-xs text-gray-400">Identity verification complete</div>
            </div>
            <span className={`ml-auto rounded-full px-3 py-1 text-sm font-bold ${riskColor[result.risk_level]}`}>
              {result.risk_level} RISK
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm">
            {[
              ['NIN Verified', result.details.nin_verified],
              ['BVN Verified', result.details.bvn_verified],
              ['Face Match', result.details.face_match],
              ['Face Confidence', `${(result.details.face_confidence * 100).toFixed(0)}%`],
              ['Name', result.details.name],
              ['Risk Score', result.risk_score],
            ].map(([label, value]) => (
              <div key={label} className="rounded-lg bg-gray-800 p-3">
                <div className="text-xs text-gray-400">{label}</div>
                <div className="mt-0.5 font-medium">
                  {typeof value === 'boolean' ? (
                    value ? (
                      <span className="text-green-400">Yes</span>
                    ) : (
                      <span className="text-red-400">No</span>
                    )
                  ) : (
                    value
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
