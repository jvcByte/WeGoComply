import React from 'react'
import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import {
  Shield,
  Activity,
  FileText,
  Bell,
  LogOut,
  Loader,
  LockKeyhole,
  UserCircle2,
} from 'lucide-react'
import { useAuth } from './auth/AuthProvider'
import ProtectedRoute from './auth/ProtectedRoute'
import { ALL_ROLES, USER_ROLES, formatRole } from './auth/roles'
import Dashboard from './pages/Dashboard'
import KYC from './pages/KYC'
import AML from './pages/AML'
import TaxVerification from './pages/TaxVerification'
import Regulatory from './pages/Regulatory'

const nav = [
  { to: '/', label: 'Dashboard', icon: Activity, roles: ALL_ROLES },
  {
    to: '/kyc',
    label: 'KYC',
    icon: Shield,
    roles: [USER_ROLES.ADMIN, USER_ROLES.COMPLIANCE_OFFICER, USER_ROLES.ANALYST],
  },
  {
    to: '/aml',
    label: 'AML Monitor',
    icon: Bell,
    roles: [USER_ROLES.ADMIN, USER_ROLES.COMPLIANCE_OFFICER, USER_ROLES.ANALYST],
  },
  {
    to: '/tax',
    label: 'Tax / TIN',
    icon: FileText,
    roles: [USER_ROLES.ADMIN, USER_ROLES.COMPLIANCE_OFFICER, USER_ROLES.ANALYST],
  },
  { to: '/regulatory', label: 'Regulatory', icon: Bell, roles: ALL_ROLES },
]

export default function App() {
  const { authMode, status, user, error, isAuthenticated, login, logout, hasAnyRole } = useAuth()

  if (status === 'loading') {
    return (
      <div className="min-h-screen grid place-items-center bg-gray-950 px-6 text-gray-100">
        <div className="rounded-2xl border border-gray-800 bg-gray-900 px-8 py-6 text-center">
          <Loader className="mx-auto animate-spin text-blue-500" size={26} />
          <p className="mt-4 text-sm text-gray-300">Initializing authentication...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen grid place-items-center bg-gray-950 px-6 text-gray-100">
        <div className="w-full max-w-md rounded-3xl border border-gray-800 bg-gray-900 p-8 shadow-2xl shadow-black/30">
          <div className="inline-flex rounded-2xl bg-blue-900/40 p-3 text-blue-300">
            <LockKeyhole size={24} />
          </div>
          <h1 className="mt-5 text-2xl font-bold">Secure Sign-In Required</h1>
          <p className="mt-2 text-sm text-gray-400">
            {authMode === 'azure_ad_b2c'
              ? 'Authenticate with Azure AD B2C to access role-based compliance workflows.'
              : 'Mock authentication is enabled, but the local session could not be initialized.'}
          </p>
          {error && (
            <div className="mt-5 rounded-xl border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-200">
              {error}
            </div>
          )}
          <button
            onClick={login}
            className="mt-6 w-full rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
          >
            {authMode === 'azure_ad_b2c' ? 'Sign in with Azure AD B2C' : 'Retry mock session'}
          </button>
        </div>
      </div>
    )
  }

  const availableNav = nav.filter((item) => hasAnyRole(item.roles))
  const homePath = availableNav[0]?.to || '/'

  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="flex w-56 flex-col border-r border-gray-800 bg-gray-900">
        <div className="border-b border-gray-800 p-5">
          <div className="flex items-center gap-2">
            <Shield className="text-blue-500" size={22} />
            <span className="text-lg font-bold tracking-tight">WeGoComply</span>
          </div>
          <p className="mt-1 text-xs text-gray-500">Nigeria RegTech Platform</p>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {availableNav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
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
        <div className="border-t border-gray-800 p-4 text-xs text-gray-600">
          <div>RegTech Hackathon 2026</div>
          <div className="mt-2 rounded-lg border border-gray-800 bg-gray-950 px-2 py-1 text-[11px] uppercase tracking-wide text-gray-500">
            {authMode === 'azure_ad_b2c' ? 'Azure AD B2C' : 'Mock Auth'}
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto bg-gray-950">
        <header className="sticky top-0 z-10 border-b border-gray-800 bg-gray-950/95 backdrop-blur">
          <div className="flex items-center justify-between gap-4 px-6 py-4">
            <div className="min-w-0">
              <div className="text-xs uppercase tracking-wide text-gray-500">Authenticated session</div>
              <div className="mt-1 flex items-center gap-2 text-sm text-gray-200">
                <UserCircle2 size={16} className="shrink-0 text-blue-400" />
                <span className="truncate font-medium">
                  {user.display_name || user.email || user.user_id}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {user.roles?.map((role) => (
                <span
                  key={role}
                  className="rounded-full border border-gray-700 bg-gray-900 px-3 py-1 text-xs text-gray-300"
                >
                  {formatRole(role)}
                </span>
              ))}
              {authMode === 'azure_ad_b2c' && (
                <button
                  onClick={logout}
                  className="inline-flex items-center gap-2 rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-200 transition-colors hover:border-gray-600 hover:bg-gray-800"
                >
                  <LogOut size={14} />
                  Sign out
                </button>
              )}
            </div>
          </div>
        </header>

        <Routes>
          <Route
            path="/"
            element={
              <ProtectedRoute allowedRoles={ALL_ROLES}>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/kyc"
            element={
              <ProtectedRoute
                allowedRoles={[USER_ROLES.ADMIN, USER_ROLES.COMPLIANCE_OFFICER, USER_ROLES.ANALYST]}
              >
                <KYC />
              </ProtectedRoute>
            }
          />
          <Route
            path="/aml"
            element={
              <ProtectedRoute
                allowedRoles={[USER_ROLES.ADMIN, USER_ROLES.COMPLIANCE_OFFICER, USER_ROLES.ANALYST]}
              >
                <AML />
              </ProtectedRoute>
            }
          />
          <Route
            path="/tax"
            element={
              <ProtectedRoute
                allowedRoles={[USER_ROLES.ADMIN, USER_ROLES.COMPLIANCE_OFFICER, USER_ROLES.ANALYST]}
              >
                <TaxVerification />
              </ProtectedRoute>
            }
          />
          <Route
            path="/regulatory"
            element={
              <ProtectedRoute allowedRoles={ALL_ROLES}>
                <Regulatory />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to={homePath} replace />} />
        </Routes>
      </main>
    </div>
  )
}
