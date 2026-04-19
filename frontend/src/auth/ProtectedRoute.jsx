import React from 'react'
import { ShieldAlert } from 'lucide-react'
import { useAuth } from './AuthProvider'
import { formatRole } from './roles'

export default function ProtectedRoute({ allowedRoles, children }) {
  const { hasAnyRole } = useAuth()

  if (!hasAnyRole(allowedRoles)) {
    return (
      <div className="p-6">
        <div className="max-w-xl rounded-2xl border border-red-900 bg-red-950/40 p-6">
          <div className="flex items-center gap-3 text-red-300">
            <ShieldAlert size={20} />
            <h1 className="text-lg font-semibold">Access denied</h1>
          </div>
          <p className="mt-3 text-sm text-red-100/80">
            Your current role does not allow this workflow. Required roles:{' '}
            {allowedRoles.map(formatRole).join(', ')}.
          </p>
        </div>
      </div>
    )
  }

  return children
}
