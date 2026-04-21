import React, { useState, useEffect } from 'react'
import { Shield, CheckCircle, XCircle, Loader, AlertCircle, Info } from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import { getApiErrorMessage, useApiClient } from '../lib/api'

function sanitizeNumericId(value) {
  return value.replace(/\D/g, '').slice(0, 11)
}

function isBackendUnavailable(error) {
  const status = error?.response?.status
  return !error?.response || [502, 503, 504].includes(status)
}

export default function KYC() {
  const { authMode } = useAuth()
  const api = useApiClient()
  const [form, setForm] = useState({ 
    nin: '', 
    firstname: '', 
    lastname: '', 
    dob: '',
    phone: '',
    email: ''
  })
  const [selfie, setSelfie] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [providerInfo, setProviderInfo] = useState(null)
  const [showRawResponse, setShowRawResponse] = useState(false)

  // Fetch provider info on component mount
  useEffect(() => {
    const fetchProviderInfo = async () => {
      try {
        const { data } = await api.get('/api/kyc/providers')
        setProviderInfo(data)
      } catch (err) {
        console.error('Failed to fetch provider info:', err)
      }
    }
    fetchProviderInfo()
  }, [api])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setResult(null)
    setError('')

    try {
      const formData = new FormData()
      formData.append('verification_type', 'nin')
      formData.append('identifier', form.nin)
      formData.append('firstname', form.firstname)
      formData.append('lastname', form.lastname)
      formData.append('dob', form.dob)
      formData.append('phone', form.phone)
      formData.append('email', form.email)
      if (selfie) formData.append('selfie', selfie)

      const { data } = await api.post('/api/kyc/verify', formData)
      setResult(data)
    } catch (requestError) {
      if (authMode === 'mock' && isBackendUnavailable(requestError)) {
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
            inputMode="numeric"
            minLength={11}
            maxLength={11}
            pattern="\d{11}"
            title="NIN must be exactly 11 digits."
            value={form.nin}
            onChange={(event) => setForm({ ...form, nin: sanitizeNumericId(event.target.value) })}
            required
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm text-gray-400">
              First Name
            </label>
            <input
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              placeholder="John"
              value={form.firstname}
              onChange={(event) => setForm({ ...form, firstname: event.target.value })}
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-gray-400">
              Last Name
            </label>
            <input
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              placeholder="Doe"
              value={form.lastname}
              onChange={(event) => setForm({ ...form, lastname: event.target.value })}
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm text-gray-400">
              Date of Birth
            </label>
            <input
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              placeholder="DD/MM/YYYY"
              value={form.dob}
              onChange={(event) => setForm({ ...form, dob: event.target.value })}
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-gray-400">
              Phone Number (Optional)
            </label>
            <input
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              placeholder="08012345678"
              value={form.phone}
              onChange={(event) => setForm({ ...form, phone: event.target.value })}
            />
          </div>
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
          {/* Provider Status Badge */}
          {result.provider && (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield size={20} className="text-blue-400" />
                <span className="text-sm text-gray-400">Provider:</span>
                <span className="text-sm font-medium">{result.provider}</span>
                {result.provider === 'nimc_mock' && (
                  <span className="rounded-full bg-purple-900/30 px-2 py-1 text-xs text-purple-300">
                    Mock Mode
                  </span>
                )}
              </div>
              {result.success ? (
                <CheckCircle className="text-green-400" size={24} />
              ) : (
                <XCircle className="text-red-400" size={24} />
              )}
            </div>
          )}

          {/* Match Scores */}
          {result.match_score && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-gray-300">Match Results</h4>
              <div className="grid grid-cols-2 gap-3 text-sm">
                {result.match_score.firstname !== null && (
                  <div className="rounded-lg bg-gray-800 p-3">
                    <div className="text-xs text-gray-400">First Name Match</div>
                    <div className="mt-0.5 font-medium">
                      {result.match_score.firstname ? (
                        <CheckCircle size={16} className="text-green-400" />
                      ) : (
                        <XCircle size={16} className="text-red-400" />
                      )}
                    </div>
                  </div>
                )}
                {result.match_score.lastname !== null && (
                  <div className="rounded-lg bg-gray-800 p-3">
                    <div className="text-xs text-gray-400">Last Name Match</div>
                    <div className="mt-0.5 font-medium">
                      {result.match_score.lastname ? (
                        <CheckCircle size={16} className="text-green-400" />
                      ) : (
                        <XCircle size={16} className="text-red-400" />
                      )}
                    </div>
                  </div>
                )}
                {result.match_score.dob !== null && (
                  <div className="rounded-lg bg-gray-800 p-3">
                    <div className="text-xs text-gray-400">Date of Birth Match</div>
                    <div className="mt-0.5 font-medium">
                      {result.match_score.dob ? (
                        <CheckCircle size={16} className="text-green-400" />
                      ) : (
                        <XCircle size={16} className="text-red-400" />
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Identity Information */}
          {result.identity && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-gray-300">Identity Information</h4>
              <div className="grid grid-cols-2 gap-3 text-sm">
                {result.identity.nin && (
                  <div className="rounded-lg bg-gray-800 p-3">
                    <div className="text-xs text-gray-400">NIN</div>
                    <div className="mt-0.5 font-medium">{result.identity.nin}</div>
                  </div>
                )}
                {result.identity.firstname && result.identity.lastname && (
                  <div className="rounded-lg bg-gray-800 p-3">
                    <div className="text-xs text-gray-400">Full Name</div>
                    <div className="mt-0.5 font-medium">
                      {result.identity.firstname} {result.identity.lastname}
                    </div>
                  </div>
                )}
                {result.identity.gender && (
                  <div className="rounded-lg bg-gray-800 p-3">
                    <div className="text-xs text-gray-400">Gender</div>
                    <div className="mt-0.5 font-medium">{result.identity.gender}</div>
                  </div>
                )}
                {result.identity.birthdate && (
                  <div className="rounded-lg bg-gray-800 p-3">
                    <div className="text-xs text-gray-400">Date of Birth</div>
                    <div className="mt-0.5 font-medium">{result.identity.birthdate}</div>
                  </div>
                )}
                {result.identity.phone && (
                  <div className="rounded-lg bg-gray-800 p-3">
                    <div className="text-xs text-gray-400">Phone</div>
                    <div className="mt-0.5 font-medium">{result.identity.phone}</div>
                  </div>
                )}
                {result.identity.email && (
                  <div className="rounded-lg bg-gray-800 p-3">
                    <div className="text-xs text-gray-400">Email</div>
                    <div className="mt-0.5 font-medium">{result.identity.email}</div>
                  </div>
                )}
                {result.identity.profession && (
                  <div className="rounded-lg bg-gray-800 p-3">
                    <div className="text-xs text-gray-400">Profession</div>
                    <div className="mt-0.5 font-medium">{result.identity.profession}</div>
                  </div>
                )}
                {result.identity.card_status && (
                  <div className="rounded-lg bg-gray-800 p-3">
                    <div className="text-xs text-gray-400">Card Status</div>
                    <div className="mt-0.5 font-medium">{result.identity.card_status}</div>
                  </div>
                )}
                {result.identity.photo && (
                  <div className="rounded-lg bg-gray-800 p-3">
                    <div className="text-xs text-gray-400">Photo</div>
                    <div className="mt-2">
                      <img 
                        src={`data:image/png;base64,${result.identity.photo}`}
                        alt="Identity Photo"
                        className="w-16 h-16 rounded-lg object-cover"
                      />
                    </div>
                  </div>
                )}
                {result.identity.signature && (
                  <div className="rounded-lg bg-gray-800 p-3">
                    <div className="text-xs text-gray-400">Signature</div>
                    <div className="mt-2">
                      <img 
                        src={`data:image/png;base64,${result.identity.signature}`}
                        alt="Signature"
                        className="w-32 h-16 rounded-lg object-contain bg-white"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Address Information */}
              {result.identity.address && (
                <div className="mt-4">
                  <h5 className="mb-2 text-xs font-medium text-gray-400">Address</h5>
                  <div className="rounded-lg bg-gray-800 p-3 text-sm">
                    {result.identity.address.line1 && (
                      <div>{result.identity.address.line1}</div>
                    )}
                    {result.identity.address.line2 && (
                      <div>{result.identity.address.line2}</div>
                    )}
                    {result.identity.address.city && result.identity.address.state && (
                      <div>
                        {result.identity.address.city}, {result.identity.address.state}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Raw Response Toggle (for development) */}
          {result.raw && authMode === 'mock' && (
            <div>
              <button
                onClick={() => setShowRawResponse(!showRawResponse)}
                className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-300"
              >
                <Info size={16} />
                {showRawResponse ? 'Hide' : 'Show'} Raw Response
              </button>
              {showRawResponse && (
                <div className="mt-2 rounded-lg bg-gray-800 p-3">
                  <pre className="text-xs text-gray-300">
                    {JSON.stringify(result.raw, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Provider Info Display */}
      {providerInfo && (
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
          <h3 className="mb-3 text-sm font-medium text-gray-300">Provider Information</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Current Provider:</span>
              <span className="font-medium">{providerInfo.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Mode:</span>
              <span className="font-medium">{providerInfo.mode || 'Unknown'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Supported Operations:</span>
              <span className="font-medium">
                {providerInfo.supported_operations?.join(', ') || 'None'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
