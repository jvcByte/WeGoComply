import React from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'
import { Shield, Activity, FileText, Bell } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import KYC from './pages/KYC'
import AML from './pages/AML'
import TaxVerification from './pages/TaxVerification'
import Regulatory from './pages/Regulatory'

const nav = [
  { to: '/', label: 'Dashboard', icon: Activity },
  { to: '/kyc', label: 'KYC', icon: Shield },
  { to: '/aml', label: 'AML Monitor', icon: Bell },
  { to: '/tax', label: 'Tax / TIN', icon: FileText },
  { to: '/regulatory', label: 'Regulatory', icon: Bell },
]

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-5 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <Shield className="text-blue-500" size={22} />
            <span className="font-bold text-lg tracking-tight">WeGoComply</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">Nigeria RegTech Platform</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-800 text-xs text-gray-600">
          RegTech Hackathon 2026
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto bg-gray-950">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/kyc" element={<KYC />} />
          <Route path="/aml" element={<AML />} />
          <Route path="/tax" element={<TaxVerification />} />
          <Route path="/regulatory" element={<Regulatory />} />
        </Routes>
      </main>
    </div>
  )
}
