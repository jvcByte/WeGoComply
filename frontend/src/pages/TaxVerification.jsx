import React, { useState } from 'react'
import {
  FileText, Upload, CheckCircle, XCircle, AlertTriangle,
  Search, RefreshCw, ExternalLink, Info, Receipt, BarChart3
} from 'lucide-react'
import { useAuth } from '../auth/AuthProvider'
import { getApiErrorMessage, useApiClient } from '../lib/api'

// ---------------------------------------------------------------------------
// Sample data
// ---------------------------------------------------------------------------
const SAMPLE_RECORDS = [
  { customer_id: 'CUST-001', name: 'Adaeze Okonkwo',  tin: '1234567890' },
  { customer_id: 'CUST-002', name: 'Emeka Nwosu',     tin: '0987654321' },
  { customer_id: 'CUST-003', name: 'Fatima Aliyu',    tin: '1122334455' },
  { customer_id: 'CUST-004', name: 'Chukwuemeka Eze', tin: '5566778899' },
  { customer_id: 'CUST-005', name: 'Ngozi Adeyemi',   tin: '9988776655' },
]

const MOCK_BULK = (() => {
  const records = SAMPLE_RECORDS.map((r, i) => ({
    customer_id: r.customer_id, tin: r.tin,
    status: i === 2 || i === 4 ? 'NOT_FOUND' : 'MATCHED',
    firs_name: i === 2 || i === 4 ? '' : r.name,
    submitted_name: r.name,
    match_confidence: i === 2 || i === 4 ? 0 : 0.95,
  }))
  const matched = records.filter(r => r.status === 'MATCHED').length
  return { total: 5, matched, failed: 5 - matched, match_rate: ((matched / 5) * 100).toFixed(1), deadline_risk: 'HIGH', records }
})()

const MOCK_BILL_RESPONSE = {
  status: true,
  uid: 'FIRS-UID-20260421-001',
  bill_number: 'INV-2026-001',
  message: 'Bill reported successfully',
  security_code: 'a3f5c8d2e1b4a7f9c2d5e8b1a4f7c0d3',
  submitted_at: new Date().toISOString(),
}

const MOCK_ANNUAL = {
  institution_id: 'inst-moniepoint', company_name: 'Moniepoint MFB',
  tin: '1234567890', tax_year: 2025,
  total_revenue: 4962000000, total_vat_collected: 372150000,
  total_vat_remitted: 344400000, vat_outstanding: 27750000,
  total_transactions: 16350000, taxable_transactions: 15369000,
  compliance_status: 'OUTSTANDING_VAT',
  outstanding_filings: ['2025-08', '2025-11'],
  total_firs_submissions: 10,
  generated_at: new Date().toISOString(),
  taxpromax_upload_ready: false,
  firs_submissions: [
    { uid: 'FIRS-UID-202501-001', month: '2025-01', amount: 28500000, status: 'ACCEPTED', submitted_date: '2025-01-21' },
    { uid: 'FIRS-UID-202502-002', month: '2025-02', amount: 29250000, status: 'ACCEPTED', submitted_date: '2025-02-21' },
    { uid: 'FIRS-UID-202503-003', month: '2025-03', amount: 30000000, status: 'ACCEPTED', submitted_date: '2025-03-21' },
  ],
  monthly_breakdown: Array.from({ length: 12 }, (_, i) => ({
    month: `2025-${String(i + 1).padStart(2, '0')}`,
    revenue: 350000000 + i * 12000000,
    vat_collected: (350000000 + i * 12000000) * 0.075,
    vat_remitted: [7, 10].includes(i) ? 0 : (350000000 + i * 12000000) * 0.075,
    transaction_count: 1200000 + i * 50000,
    firs_uid: [7, 10].includes(i) ? null : `FIRS-UID-2025${String(i + 1).padStart(2, '0')}-00${i + 1}`,
  })),
}

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------
function StatusBadge({ status }) {
  const s = {
    MATCHED:       'bg-green-900/50 text-green-300 border border-green-800',
    NOT_FOUND:     'bg-red-900/50 text-red-300 border border-red-800',
    NAME_MISMATCH: 'bg-yellow-900/50 text-yellow-300 border border-yellow-800',
  }
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${s[status] || ''}`}>{status}</span>
}

function FIRSStatus() {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
          <span className="text-sm font-medium text-gray-200">FIRS ATRS Connection</span>
          <span className="text-xs bg-yellow-900/40 text-yellow-300 border border-yellow-800 px-2 py-0.5 rounded-full">Mock Mode</span>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span>Dev: api-dev.i-fis.com</span>
          <span>Prod: atrs-api.firs.gov.ng</span>
          <a href="https://atrs.firs.gov.ng/getting-started/" target="_blank" rel="noreferrer"
            className="text-blue-400 hover:underline flex items-center gap-1">
            Get credentials <ExternalLink size={10} />
          </a>
        </div>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-3 text-xs">
        {[
          ['Auth', 'OAuth 2.0 Bearer Token', 'text-green-400'],
          ['Signing', 'MD5 SID (client_secret + fields)', 'text-blue-400'],
          ['Switch to Live', 'Set FIRS_MODE=live in .env', 'text-yellow-400'],
        ].map(([label, value, color]) => (
          <div key={label} className="bg-gray-800/60 rounded-lg p-2">
            <div className="text-gray-500">{label}</div>
            <div className={`${color} font-medium mt-0.5`}>{value}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Tab 1: Single TIN Verify
// ---------------------------------------------------------------------------
function SingleVerify({ api, authMode }) {
  const [form, setForm] = useState({ customer_id: '', name: '', tin: '' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleVerify = async (e) => {
    e.preventDefault()
    setLoading(true); setError(''); setResult(null)
    try {
      const { data } = await api.post('/api/tax/verify-tin', form)
      setResult(data)
    } catch (err) {
      if (authMode === 'mock') {
        const tin = form.tin
        setResult({
          customer_id: form.customer_id, tin,
          status: tin.endsWith('55') ? 'NOT_FOUND' : tin.endsWith('99') ? 'NAME_MISMATCH' : 'MATCHED',
          firs_name: tin.endsWith('55') ? '' : tin.endsWith('99') ? `${form.name.split(' ')[0]} Holdings Ltd` : form.name,
          submitted_name: form.name,
          match_confidence: tin.endsWith('55') ? 0 : tin.endsWith('99') ? 0.62 : 0.95,
        })
      } else { setError(getApiErrorMessage(err, 'TIN verification failed.')) }
    }
    setLoading(false)
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5 space-y-4">
      <div className="flex items-center gap-2">
        <Search size={16} className="text-yellow-400" />
        <span className="font-semibold text-sm text-gray-200">Single TIN Lookup</span>
        <span className="ml-auto text-xs text-gray-500">FIRS ATRS · GET /v1/taxpayer/verify</span>
      </div>
      <form onSubmit={handleVerify} className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {[['Customer ID','customer_id','CUST-001'],['Full Name','name','Adaeze Okonkwo'],['TIN (10 digits)','tin','1234567890']].map(([label, key, ph]) => (
          <div key={key}>
            <label className="text-xs text-gray-400 block mb-1">{label}</label>
            <input className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-yellow-500"
              placeholder={ph} value={form[key]} onChange={e => setForm({ ...form, [key]: e.target.value })} required />
          </div>
        ))}
        <div className="md:col-span-3">
          <button type="submit" disabled={loading}
            className="flex items-center gap-2 bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
            {loading ? <><RefreshCw size={14} className="animate-spin" /> Verifying...</> : <><Search size={14} /> Verify TIN</>}
          </button>
        </div>
      </form>
      {error && <div className="rounded-lg border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-200">{error}</div>}
      {result && (
        <div className={`rounded-lg p-4 border space-y-3 ${result.status === 'MATCHED' ? 'border-green-800 bg-green-900/20' : result.status === 'NAME_MISMATCH' ? 'border-yellow-800 bg-yellow-900/20' : 'border-red-800 bg-red-900/20'}`}>
          <div className="flex items-center gap-3">
            {result.status === 'MATCHED' ? <CheckCircle className="text-green-400" size={20} /> : result.status === 'NAME_MISMATCH' ? <AlertTriangle className="text-yellow-400" size={20} /> : <XCircle className="text-red-400" size={20} />}
            <StatusBadge status={result.status} />
            <span className="text-xs text-gray-400 ml-auto">Confidence: {(result.match_confidence * 100).toFixed(0)}%</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {[['TIN', result.tin], ['Submitted Name', result.submitted_name], ['FIRS Name', result.firs_name || '—'], ['Customer ID', result.customer_id]].map(([l, v]) => (
              <div key={l} className="bg-gray-800/60 rounded-lg p-2">
                <div className="text-gray-500">{l}</div>
                <div className="text-gray-200 font-medium mt-0.5">{v}</div>
              </div>
            ))}
          </div>
          {result.status === 'NOT_FOUND' && (
            <div className="flex items-start gap-2 bg-gray-800/60 rounded-lg p-3 text-xs text-gray-300">
              <Info size={13} className="text-blue-400 shrink-0 mt-0.5" />
              Customer must register free TIN at <a href="https://jtb.gov.ng" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline ml-1">jtb.gov.ng</a> — takes 5 minutes with NIN.
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Tab 2: Bulk TIN Verify
// ---------------------------------------------------------------------------
function BulkVerify({ api, authMode }) {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const run = async () => {
    setLoading(true); setError('')
    try {
      const { data } = await api.post('/api/tax/bulk-verify', { records: SAMPLE_RECORDS })
      setResults(data)
    } catch (err) {
      authMode === 'mock' ? setResults(MOCK_BULK) : setError(getApiErrorMessage(err, 'Bulk verification failed.'))
    }
    setLoading(false)
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Upload size={16} className="text-yellow-400" />
          <span className="font-semibold text-sm text-gray-200">Bulk TIN Verification</span>
          <span className="text-xs text-gray-500">— {SAMPLE_RECORDS.length} records</span>
        </div>
        <button onClick={run} disabled={loading}
          className="flex items-center gap-2 bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
          {loading ? <><RefreshCw size={14} className="animate-spin" /> Verifying...</> : <><Upload size={14} /> Run Bulk Verification</>}
        </button>
      </div>
      <table className="w-full text-xs text-gray-400">
        <thead><tr className="border-b border-gray-800">{['Customer ID','Name','TIN', results ? 'Status' : ''].filter(Boolean).map(h => <th key={h} className="text-left py-2 pr-4 font-medium">{h}</th>)}</tr></thead>
        <tbody>
          {SAMPLE_RECORDS.map((r, i) => {
            const res = results?.records[i]
            return (
              <tr key={r.customer_id} className="border-b border-gray-800/50">
                <td className="py-2 pr-4">{r.customer_id}</td>
                <td className="py-2 pr-4">{r.name}</td>
                <td className="py-2 pr-4 font-mono">{r.tin}</td>
                {results && <td className="py-2 pr-4"><div className="flex items-center gap-2">{res.status === 'MATCHED' ? <CheckCircle size={13} className="text-green-400" /> : <XCircle size={13} className="text-red-400" />}<StatusBadge status={res.status} /><span className="text-gray-500">{(res.match_confidence * 100).toFixed(0)}%</span></div></td>}
              </tr>
            )
          })}
        </tbody>
      </table>
      {error && <div className="text-xs text-red-400">{error}</div>}
      {results && (
        <div className="space-y-3">
          <div className="grid grid-cols-4 gap-3">
            {[['Total', results.total, 'text-blue-400'], ['Matched', results.matched, 'text-green-400'], ['Failed', results.failed, 'text-red-400'], ['Match Rate', `${results.match_rate}%`, parseFloat(results.match_rate) >= 80 ? 'text-green-400' : 'text-red-400']].map(([l, v, c]) => (
              <div key={l} className="rounded-lg border border-gray-800 bg-gray-800/50 p-3 text-center">
                <div className={`text-xl font-bold ${c}`}>{v}</div>
                <div className="text-xs text-gray-500 mt-0.5">{l}</div>
              </div>
            ))}
          </div>
          <div className={`rounded-lg border p-3 text-sm font-medium flex items-center gap-2 ${results.deadline_risk === 'HIGH' ? 'border-red-800 bg-red-900/30 text-red-300' : 'border-green-800 bg-green-900/30 text-green-300'}`}>
            {results.deadline_risk === 'HIGH' ? <AlertTriangle size={16} /> : <CheckCircle size={16} />}
            Deadline Risk: {results.deadline_risk} — {results.deadline_risk === 'HIGH' ? 'Send TIN registration links to failed customers immediately.' : 'On track to meet FIRS mandate.'}
          </div>
          {results.failed > 0 && (
            <div className="rounded-lg border border-blue-900 bg-blue-900/20 p-3 text-xs text-blue-300 space-y-1">
              <div className="font-semibold flex items-center gap-1"><Info size={13} /> Action for {results.failed} failed customer(s)</div>
              <div className="bg-gray-800 rounded p-2 text-gray-300 font-mono">"Your account requires TIN verification. Register free at jtb.gov.ng using your NIN. Deadline: April 1, 2026."</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Tab 3: Bill Reporting → FIRS ATRS POST /v1/bills/report
// ---------------------------------------------------------------------------
function BillReporting({ api, authMode }) {
  const [form, setForm] = useState({
    bill_number: 'INV-2026-001',
    bill_datetime: new Date().toISOString().slice(0, 16),
    total_value: '',
    base_value: '',
    vat_value: '',
    payment_type: 'T',
    currency_code: 'NGN',
    client_vat_number: '',
    item_name: 'Compliance Service Fee',
    item_qty: '1',
    item_price: '',
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(''); setResult(null)
    const payload = {
      bill_number: form.bill_number,
      bill_datetime: form.bill_datetime,
      total_value: parseFloat(form.total_value),
      tax_free: 0,
      payment_type: form.payment_type,
      currency_code: form.currency_code,
      client_vat_number: form.client_vat_number || null,
      rate: 7.5,
      base_value: parseFloat(form.base_value),
      vat_value: parseFloat(form.vat_value),
      resend: 0,
      items: [{ name: form.item_name, quantity: parseInt(form.item_qty), price: parseFloat(form.item_price), vat: parseFloat(form.vat_value) }],
    }
    try {
      const { data } = await api.post('/api/tax/report-bill', payload)
      setResult(data)
    } catch (err) {
      authMode === 'mock' ? setResult({ ...MOCK_BILL_RESPONSE, bill_number: form.bill_number }) : setError(getApiErrorMessage(err, 'Bill submission failed.'))
    }
    setLoading(false)
  }

  const PAYMENT_TYPES = [['T','Bank Transfer'],['C','Cash'],['K','Credit Card'],['D','Debit Card'],['P','Post Payment'],['O','Other']]

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5 space-y-4">
      <div className="flex items-center gap-2">
        <Receipt size={16} className="text-blue-400" />
        <span className="font-semibold text-sm text-gray-200">Submit Bill / Receipt to FIRS</span>
        <span className="ml-auto text-xs text-gray-500">FIRS ATRS · POST /v1/bills/report</span>
      </div>

      <div className="bg-gray-800/40 rounded-lg p-3 text-xs text-gray-400 space-y-1">
        <div className="font-medium text-gray-300">How it works:</div>
        <div>1. Fill in bill details → WeGoComply generates MD5 SID signature</div>
        <div>2. POST to FIRS ATRS with signed payload</div>
        <div>3. FIRS validates and returns UID (proof of submission)</div>
        <div>4. UID stored as audit evidence for annual return reconciliation</div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[
            ['Bill Number', 'bill_number', 'INV-2026-001', 'text'],
            ['Bill Date/Time', 'bill_datetime', '', 'datetime-local'],
            ['Total Value (₦)', 'total_value', '15000', 'number'],
            ['Base Value (pre-VAT)', 'base_value', '13953.49', 'number'],
            ['VAT Amount (7.5%)', 'vat_value', '1046.51', 'number'],
            ['Client VAT/TIN', 'client_vat_number', '9876543210 (optional)', 'text'],
          ].map(([label, key, ph, type]) => (
            <div key={key}>
              <label className="text-xs text-gray-400 block mb-1">{label}</label>
              <input type={type} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
                placeholder={ph} value={form[key]} onChange={e => setForm({ ...form, [key]: e.target.value })}
                required={key !== 'client_vat_number'} step={type === 'number' ? '0.01' : undefined} />
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div>
            <label className="text-xs text-gray-400 block mb-1">Payment Type</label>
            <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              value={form.payment_type} onChange={e => setForm({ ...form, payment_type: e.target.value })}>
              {PAYMENT_TYPES.map(([v, l]) => <option key={v} value={v}>{v} — {l}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1">Currency</label>
            <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              value={form.currency_code} onChange={e => setForm({ ...form, currency_code: e.target.value })}>
              {['NGN','USD','EUR','GBP'].map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1">Item Name</label>
            <input className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              value={form.item_name} onChange={e => setForm({ ...form, item_name: e.target.value })} required />
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1">Item Price (₦)</label>
            <input type="number" step="0.01" className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              placeholder="15000" value={form.item_price} onChange={e => setForm({ ...form, item_price: e.target.value })} required />
          </div>
        </div>

        {error && <div className="text-xs text-red-400">{error}</div>}

        <button type="submit" disabled={loading}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
          {loading ? <><RefreshCw size={14} className="animate-spin" /> Submitting to FIRS...</> : <><Receipt size={14} /> Submit Bill to FIRS</>}
        </button>
      </form>

      {result && (
        <div className={`rounded-lg border p-4 space-y-3 ${result.status ? 'border-green-800 bg-green-900/20' : 'border-red-800 bg-red-900/20'}`}>
          <div className="flex items-center gap-2">
            {result.status ? <CheckCircle className="text-green-400" size={20} /> : <XCircle className="text-red-400" size={20} />}
            <span className="font-semibold text-sm">{result.status ? 'Bill Accepted by FIRS' : 'Submission Failed'}</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {[
              ['FIRS UID (Proof of Submission)', result.uid],
              ['Bill Number', result.bill_number],
              ['Message', result.message],
              ['Submitted At', new Date(result.submitted_at).toLocaleString()],
              ['Security Code (MD5 SID)', result.security_code],
            ].map(([l, v]) => (
              <div key={l} className={`bg-gray-800/60 rounded-lg p-2 ${l.includes('UID') ? 'col-span-2' : ''}`}>
                <div className="text-gray-500">{l}</div>
                <div className="text-gray-200 font-mono mt-0.5 break-all">{v}</div>
              </div>
            ))}
          </div>
          <div className="flex items-start gap-2 bg-gray-800/60 rounded-lg p-3 text-xs text-gray-300">
            <Info size={13} className="text-green-400 shrink-0 mt-0.5" />
            Store the FIRS UID as proof of submission. It will be included in your annual return reconciliation.
          </div>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Tab 4: Annual Return Summary
// ---------------------------------------------------------------------------
function AnnualReturn({ api, authMode }) {
  const [form, setForm] = useState({ institution_id: 'inst-moniepoint', company_name: 'Moniepoint MFB', tin: '1234567890', tax_year: '2025' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(''); setResult(null)
    try {
      const { data } = await api.post('/api/tax/annual-return', { ...form, tax_year: parseInt(form.tax_year) })
      setResult(data)
    } catch (err) {
      authMode === 'mock' ? setResult(MOCK_ANNUAL) : setError(getApiErrorMessage(err, 'Annual return generation failed.'))
    }
    setLoading(false)
  }

  const statusStyle = {
    COMPLIANT:            'border-green-800 bg-green-900/20 text-green-300',
    OUTSTANDING_VAT:      'border-red-800 bg-red-900/20 text-red-300',
    MISSING_SUBMISSIONS:  'border-yellow-800 bg-yellow-900/20 text-yellow-300',
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5 space-y-4">
      <div className="flex items-center gap-2">
        <BarChart3 size={16} className="text-purple-400" />
        <span className="font-semibold text-sm text-gray-200">Annual Tax Return Summary</span>
        <span className="ml-auto text-xs text-gray-500">For TaxPro Max upload</span>
      </div>

      <div className="bg-gray-800/40 rounded-lg p-3 text-xs text-gray-400 space-y-1">
        <div className="font-medium text-gray-300">Annual Return Process:</div>
        <div>1. WeGoComply aggregates all monthly FIRS bill submissions for the year</div>
        <div>2. Calculates total revenue, VAT collected, VAT remitted, and outstanding</div>
        <div>3. Identifies missing months and compliance status</div>
        <div>4. Company uploads this summary to <a href="https://taxpromax.firs.gov.ng" target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">taxpromax.firs.gov.ng</a> to file CIT return</div>
        <div>5. FIRS issues Tax Clearance Certificate (TCC) upon acceptance</div>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[['Institution ID','institution_id','inst-moniepoint'],['Company Name','company_name','Moniepoint MFB'],['TIN','tin','1234567890'],['Tax Year','tax_year','2025']].map(([l, k, ph]) => (
          <div key={k}>
            <label className="text-xs text-gray-400 block mb-1">{l}</label>
            <input className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
              placeholder={ph} value={form[k]} onChange={e => setForm({ ...form, [k]: e.target.value })} required />
          </div>
        ))}
        <div className="col-span-2 md:col-span-4">
          <button type="submit" disabled={loading}
            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
            {loading ? <><RefreshCw size={14} className="animate-spin" /> Generating...</> : <><BarChart3 size={14} /> Generate Annual Return</>}
          </button>
        </div>
      </form>

      {error && <div className="text-xs text-red-400">{error}</div>}

      {result && (
        <div className="space-y-4">
          {/* Status banner */}
          <div className={`rounded-lg border p-4 flex items-start gap-3 ${statusStyle[result.compliance_status]}`}>
            {result.compliance_status === 'COMPLIANT' ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
            <div>
              <div className="font-semibold">{result.compliance_status.replace(/_/g, ' ')}</div>
              <div className="text-xs opacity-80 mt-0.5">
                {result.compliance_status === 'COMPLIANT' && 'All VAT remitted. Ready for TaxPro Max upload.'}
                {result.compliance_status === 'OUTSTANDING_VAT' && `₦${result.vat_outstanding.toLocaleString()} VAT outstanding. Settle before filing.`}
                {result.compliance_status === 'MISSING_SUBMISSIONS' && `Missing FIRS submissions for: ${result.outstanding_filings.join(', ')}`}
              </div>
            </div>
            <div className="ml-auto text-right text-xs opacity-70">
              <div>TaxPro Max Ready: {result.taxpromax_upload_ready ? '✓ Yes' : '✗ No'}</div>
              <div>{result.total_firs_submissions} FIRS submissions</div>
            </div>
          </div>

          {/* Financial summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              ['Total Revenue', `₦${(result.total_revenue / 1e9).toFixed(2)}B`, 'text-blue-400'],
              ['VAT Collected', `₦${(result.total_vat_collected / 1e6).toFixed(1)}M`, 'text-green-400'],
              ['VAT Remitted', `₦${(result.total_vat_remitted / 1e6).toFixed(1)}M`, 'text-green-400'],
              ['VAT Outstanding', `₦${(result.vat_outstanding / 1e6).toFixed(1)}M`, result.vat_outstanding > 0 ? 'text-red-400' : 'text-green-400'],
            ].map(([l, v, c]) => (
              <div key={l} className="rounded-lg border border-gray-800 bg-gray-800/50 p-3 text-center">
                <div className={`text-xl font-bold ${c}`}>{v}</div>
                <div className="text-xs text-gray-500 mt-0.5">{l}</div>
              </div>
            ))}
          </div>

          {/* Monthly breakdown */}
          <div className="rounded-lg border border-gray-800 bg-gray-800/30 overflow-hidden">
            <div className="px-4 py-2 border-b border-gray-800 text-xs font-medium text-gray-300">Monthly Breakdown — {result.tax_year}</div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead><tr className="border-b border-gray-800 text-gray-500">
                  {['Month','Revenue','VAT Collected','VAT Remitted','Transactions','FIRS UID'].map(h => <th key={h} className="text-left py-2 px-3 font-medium">{h}</th>)}
                </tr></thead>
                <tbody>
                  {result.monthly_breakdown.map(m => (
                    <tr key={m.month} className={`border-b border-gray-800/50 ${!m.firs_uid ? 'bg-red-900/10' : ''}`}>
                      <td className="py-2 px-3 font-medium text-gray-300">{m.month}</td>
                      <td className="py-2 px-3 text-gray-400">₦{(m.revenue / 1e6).toFixed(1)}M</td>
                      <td className="py-2 px-3 text-gray-400">₦{(m.vat_collected / 1e6).toFixed(2)}M</td>
                      <td className={`py-2 px-3 ${m.vat_remitted > 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {m.vat_remitted > 0 ? `₦${(m.vat_remitted / 1e6).toFixed(2)}M` : '— Not remitted'}
                      </td>
                      <td className="py-2 px-3 text-gray-400">{m.transaction_count.toLocaleString()}</td>
                      <td className="py-2 px-3">
                        {m.firs_uid
                          ? <span className="text-green-400 font-mono">{m.firs_uid.slice(-12)}</span>
                          : <span className="text-red-400">⚠ Missing</span>
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* TaxPro Max CTA */}
          <div className="rounded-lg border border-purple-800 bg-purple-900/20 p-4 flex items-start gap-3">
            <Info size={16} className="text-purple-400 shrink-0 mt-0.5" />
            <div className="text-sm text-purple-300 space-y-1">
              <div className="font-semibold">Next Step: File on TaxPro Max</div>
              <div className="text-xs opacity-80">
                {result.taxpromax_upload_ready
                  ? 'Your annual return is ready. Upload this summary to TaxPro Max to file your Company Income Tax (CIT) return and obtain your Tax Clearance Certificate.'
                  : `Resolve ${result.outstanding_filings.length} outstanding filing(s) and settle ₦${result.vat_outstanding.toLocaleString()} VAT before uploading to TaxPro Max.`
                }
              </div>
              <a href="https://taxpromax.firs.gov.ng" target="_blank" rel="noreferrer"
                className="inline-flex items-center gap-1 text-xs text-purple-400 hover:underline mt-1">
                Open TaxPro Max <ExternalLink size={10} />
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
export default function TaxVerification() {
  const { authMode } = useAuth()
  const api = useApiClient()
  const [tab, setTab] = useState('bulk')

  const TABS = [
    { id: 'bulk',   label: 'Bulk Verify',    icon: Upload },
    { id: 'single', label: 'Single Lookup',  icon: Search },
    { id: 'bill',   label: 'Report Bill',    icon: Receipt },
    { id: 'annual', label: 'Annual Return',  icon: BarChart3 },
  ]

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <FileText className="text-yellow-400" size={22} /> Tax ID (TIN) & Annual Returns
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          TIN verification · Bill reporting · Annual return filing — all via FIRS ATRS API
        </p>
      </div>

      {/* FIRS mandate banner */}
      <div className="rounded-xl border border-yellow-800 bg-yellow-900/20 p-4 text-sm text-yellow-300 flex items-start gap-3">
        <AlertTriangle size={18} className="shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold">FIRS Mandate Active:</span> Accounts without verified TINs restricted above ₦500,000 (April 1, 2026).
          VAT returns due by 21st of each month. Annual CIT return due June 30.
          <a href="https://jtb.gov.ng" target="_blank" rel="noreferrer" className="underline hover:text-yellow-200 ml-2 inline-flex items-center gap-1">
            Register TIN <ExternalLink size={11} />
          </a>
        </div>
      </div>

      {/* FIRS connection status */}
      <FIRSStatus />

      {/* Tabs */}
      <div className="flex gap-2 flex-wrap">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setTab(id)}
            className={`flex items-center gap-2 text-sm px-4 py-2 rounded-lg transition-colors ${tab === id ? 'bg-yellow-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'}`}>
            <Icon size={14} /> {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'bulk'   && <BulkVerify   api={api} authMode={authMode} />}
      {tab === 'single' && <SingleVerify api={api} authMode={authMode} />}
      {tab === 'bill'   && <BillReporting api={api} authMode={authMode} />}
      {tab === 'annual' && <AnnualReturn  api={api} authMode={authMode} />}

      {/* TIN Registration Guide */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-5 space-y-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-gray-200">
          <Info size={16} className="text-blue-400" /> TIN Registration Guide
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
          {[
            { step: '1', title: 'Visit JTB Portal', desc: 'Go to jtb.gov.ng → click "Register for TIN"', color: 'border-blue-800 bg-blue-900/20 text-blue-300' },
            { step: '2', title: 'Provide Details', desc: 'Full name (must match BVN), NIN, date of birth, phone, state', color: 'border-yellow-800 bg-yellow-900/20 text-yellow-300' },
            { step: '3', title: 'Get TIN Instantly', desc: 'Free 10-digit TIN issued immediately. No office visit needed.', color: 'border-green-800 bg-green-900/20 text-green-300' },
          ].map(item => (
            <div key={item.step} className={`rounded-lg border p-3 ${item.color}`}>
              <div className="font-bold text-lg mb-1">Step {item.step}</div>
              <div className="font-semibold mb-1">{item.title}</div>
              <div className="opacity-80">{item.desc}</div>
            </div>
          ))}
        </div>
        <div className="flex gap-4 text-xs flex-wrap">
          {[['JTB TIN Registration','https://jtb.gov.ng'],['TaxPro Max (Annual Returns)','https://taxpromax.firs.gov.ng'],['FIRS ATRS API Docs','https://atrs.firs.gov.ng/docs/category/api-documentation-for-devs/']].map(([l, u]) => (
            <a key={l} href={u} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-blue-400 hover:underline">
              {l} <ExternalLink size={10} />
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}
