import React, { useState } from 'react'
import {
  Shield, CheckCircle, XCircle, Loader,
  AlertTriangle, User, Fingerprint, Camera
} from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import { getApiErrorMessage, useApiClient } from '../lib/api'

const STEPS = [
  { id: 1, label: 'NIN Verification', icon: Fingerprint, key: 'nin_verified' },
  { id: 2, label: 'BVN Verification', icon: Shield, key: 'bvn_verified' },
  { id: 3, label: 'Facial Match', icon: Camera, key: 'face_match' },
]

const riskStyle = {
  LOW:    'text-green-400 bg-green-900/30 border border-green-800',
  MEDIUM: 'text-yellow-400 bg-yellow-900/30 border border-yellow-800',
  HIGH:   'text-red-400 bg-red-900/30 border border-red-800',
}

const MOCK_RESULT = {
  status: 'VERIFIED',
  risk_score: 0.12,
  risk_level: 'LOW',
  details: {
    nin_verified: true,
    bvn_verified: true,
    face_match: true,
    face_confidence: 0.94,
    name: 'Adaeze Okonkwo',
    dob: '1990-01-01',
    phone: '080XXXXXXXX',
  },
}

export default function KYC() {
  const { authMode } = useAuth()
  const api = useApiClient()
  const [form, setForm] = useState({ nin: '', bvn: '' })
  const [selfie, setSelfie] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [history, setHistory] = useState([])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)
    setError('')

    try {
      const fd = new FormData()
      fd.append('nin', form.nin)
      fd.append('bvn', form.bvn)
      if (selfie) fd.append('selfie', selfie)
      const { data } = await api.post('/api/kyc/verify', fd)
      setResult(data)
      setHistory(prev => [{ ...data, nin: form.nin, ts: new Date().toLocaleTimeString() }, ...prev].slice(0, 5))
    } catch (err) {
      if (authMode === 'mock') {
        setResult(MOCK_RESULT)
        setHistory(prev => [{ ...MOCK_RESULT, nin: form.nin, ts: new Date().toLocaleTimeString() }, ...prev].slice(0, 5))
      } else {
        setError(getApiErrorMessage(err, 'KYC verification failed.'))
      }
    }
    setLoading(false)
  }

  return (
    <div className="p-6 space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Shield className="text-blue-500" size={22} /> KYC Verification
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Multi-source identity verification — NIN · BVN · Facial Match · AI Risk Scoring
        </p>
      </div>

      {/* Verification steps indicator */}
      <div className="grid grid-cols-3 gap-3">
        {STEPS.map((step) => (
          <div key={step.id} className={`rounded-xl border p-3 flex items-center gap-3 transition-colors ${
            result
              ? result.details[step.key]
                ? 'border-green-800 bg-green-900/20'
                : 'border-red-800 bg-red-900/20'
              : 'border-gray-800 bg-gray-900'
          }`}>
            <step.icon size={16} className={
              result
                ? result.details[step.key] ? 'text-green-400' : 'text-red-400'
                : 'text-gray-500'
            } />
            <div>
              <div className="text-xs font-medium text-gray-300">{step.label}</div>
              <div className="text-xs text-gray-500 mt-0.5">
                {result
                  ? result.details[step.key] ? '✓ Verified' : '✗ Failed'
                  : 'Pending'
                }
              </div>
            </div>
          </div>
        ))}
      </div>

      {error && (
        <div className="rounded-xl border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="rounded-xl border border-gray-800 bg-gray-900 p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-gray-400 block mb-1">NIN (11 digits)</label>
            <input
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-blue-500"
              placeholder="12345678901"
              value={form.nin}
              maxLength={11}
              onChange={e => setForm({ ...form, nin: e.target.value.replace(/\D/g, '') })}
              required
            />
          </div>
          <div>
            <label className="text-sm text-gray-400 block mb-1">BVN (11 digits)</label>
            <input
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-blue-500"
              placeholder="22334455667"
              value={form.bvn}
              maxLength={11}
              onChange={e => setForm({ ...form, bvn: e.target.value.replace(/\D/g, '') })}
              required
            />
          </div>
        </div>

        <div>
          <label className="text-sm text-gray-400 block mb-1">Selfie / Photo ID</label>
          <div className={`border-2 border-dashed rounded-lg p-4 text-center transition-colors ${
            selfie ? 'border-blue-600 bg-blue-900/10' : 'border-gray-700 hover:border-gray-600'
          }`}>
            <input
              type="file"
              accept="image/*"
              className="hidden"
              id="selfie-upload"
              onChange={e => setSelfie(e.target.files[0])}
              required
            />
            <label htmlFor="selfie-upload" className="cursor-pointer">
              <Camera size={24} className={`mx-auto mb-2 ${selfie ? 'text-blue-400' : 'text-gray-500'}`} />
              <div className="text-sm text-gray-400">
                {selfie ? selfie.name : 'Click to upload selfie or ID photo'}
              </div>
              <div className="text-xs text-gray-600 mt-1">JPG, PNG — used for facial verification</div>
            </label>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg text-sm transition-colors"
        >
          {loading
            ? <><Loader size={16} className="animate-spin" /> Verifying identity...</>
            : <><Shield size={16} /> Verify Identity</>
          }
        </button>
      </form>

      {/* Result */}
      {result && (
        <div className={`rounded-xl border p-5 space-y-4 ${
          result.status === 'VERIFIED'
            ? 'border-green-800 bg-green-900/10'
            : 'border-red-800 bg-red-900/10'
        }`}>
          <div className="flex items-center gap-3">
            {result.status === 'VERIFIED'
              ? <CheckCircle className="text-green-400" size={28} />
              : <XCircle className="text-red-400" size={28} />
            }
            <div>
              <div className="text-xl font-bold">
                {result.status === 'VERIFIED' ? 'Identity Verified' : 'Verification Failed'}
              </div>
              <div className="text-xs text-gray-400 mt-0.5">
                {result.status === 'VERIFIED'
                  ? `Welcome, ${result.details.name || 'Customer'}`
                  : 'One or more checks failed. Review details below.'
                }
              </div>
            </div>
            <span className={`ml-auto text-sm font-bold px-3 py-1 rounded-full ${riskStyle[result.risk_level]}`}>
              {result.risk_level} RISK
            </span>
          </div>

          {/* Detail grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            {[
              ['NIN Verified', result.details.nin_verified, 'bool'],
              ['BVN Verified', result.details.bvn_verified, 'bool'],
              ['Face Match', result.details.face_match, 'bool'],
              ['Face Confidence', `${(result.details.face_confidence * 100).toFixed(0)}%`, 'text'],
              ['Risk Score', result.risk_score.toFixed(2), 'text'],
              ['Name', result.details.name || '—', 'text'],
              ['Date of Birth', result.details.dob || '—', 'text'],
              ['Phone', result.details.phone || '—', 'text'],
            ].map(([label, value, type]) => (
              <div key={label} className="bg-gray-800/60 rounded-lg p-3">
                <div className="text-xs text-gray-400">{label}</div>
                <div className="font-medium mt-0.5">
                  {type === 'bool'
                    ? value
                      ? <span className="text-green-400">✓ Yes</span>
                      : <span className="text-red-400">✗ No</span>
                    : <span className="text-gray-200">{value}</span>
                  }
                </div>
              </div>
            ))}
          </div>

          {result.risk_level === 'HIGH' && (
            <div className="flex items-start gap-2 bg-red-900/20 border border-red-800 rounded-lg p-3 text-xs text-red-300">
              <AlertTriangle size={14} className="shrink-0 mt-0.5" />
              High risk customer detected. Manual review required before account activation per CBN KYC Guidelines.
            </div>
          )}
        </div>
      )}

      {/* Recent verifications */}
      {history.length > 0 && (
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
          <div className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
            <User size={14} /> Recent Verifications (this session)
          </div>
          <div className="space-y-2">
            {history.map((h, i) => (
              <div key={i} className="flex items-center gap-3 text-xs text-gray-400 bg-gray-800/50 rounded-lg px-3 py-2">
                {h.status === 'VERIFIED'
                  ? <CheckCircle size={12} className="text-green-400" />
                  : <XCircle size={12} className="text-red-400" />
                }
                <span className="font-mono">{h.nin?.slice(0, 4)}****{h.nin?.slice(-3)}</span>
                <span className={`px-1.5 py-0.5 rounded text-xs ${riskStyle[h.risk_level]}`}>{h.risk_level}</span>
                <span className="ml-auto text-gray-600">{h.ts}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
