import React, { createContext, useContext, useEffect, useState } from 'react'
import axios from 'axios'
import { InteractionRequiredAuthError, PublicClientApplication } from '@azure/msal-browser'
import { authConfig, buildMockHeaders } from './config'
import { hasAnyRole } from './roles'

const AuthContext = createContext(null)
const authHttp = axios.create({
  baseURL: authConfig.apiBaseUrl || undefined,
})

const msalInstance =
  authConfig.mode === 'entra_id' && authConfig.entra.isConfigured
    ? new PublicClientApplication(authConfig.entra.msal)
    : null

function formatAuthError(error, fallbackMessage) {
  const backendMessage = error?.response?.data?.error?.message
  return backendMessage || error?.message || fallbackMessage
}

async function fetchCurrentUser(headers) {
  const { data } = await authHttp.get('/api/auth/me', { headers })
  return data
}

async function acquireEntraHeaders(account) {
  if (!msalInstance || !account) {
    throw new Error('No authenticated Entra ID account is available.')
  }

  try {
    const tokenResult = await msalInstance.acquireTokenSilent({
      account,
      scopes: authConfig.entra.scopes,
    })
    return { Authorization: `Bearer ${tokenResult.accessToken}` }
  } catch (error) {
    if (error instanceof InteractionRequiredAuthError) {
      await msalInstance.acquireTokenRedirect({
        account,
        scopes: authConfig.entra.scopes,
      })
    }
    throw error
  }
}

export function AuthProvider({ children }) {
  const [authState, setAuthState] = useState({
    status: 'loading',
    user: null,
    account: null,
    error: '',
  })
  const [refreshNonce, setRefreshNonce] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function initializeMockSession() {
      try {
        const user = await fetchCurrentUser(buildMockHeaders())
        if (!cancelled) {
          setAuthState({
            status: 'authenticated',
            user,
            account: null,
            error: '',
          })
        }
      } catch (error) {
        if (!cancelled) {
          setAuthState({
            status: 'error',
            user: null,
            account: null,
            error: formatAuthError(error, 'Unable to initialize mock authentication.'),
          })
        }
      }
    }

    async function initializeEntraSession() {
      if (!msalInstance || !authConfig.entra.isConfigured) {
        setAuthState({
          status: 'error',
          user: null,
          account: null,
          error: authConfig.entra.configError || 'Entra ID is not configured.',
        })
        return
      }

      try {
        await msalInstance.initialize()
        const redirectResult = await msalInstance.handleRedirectPromise()
        const account =
          redirectResult?.account ||
          msalInstance.getActiveAccount() ||
          msalInstance.getAllAccounts()[0] ||
          null

        if (!account) {
          if (!cancelled) {
            setAuthState({ status: 'unauthenticated', user: null, account: null, error: '' })
          }
          return
        }

        msalInstance.setActiveAccount(account)
        const headers = await acquireEntraHeaders(account)
        const user = await fetchCurrentUser(headers)

        if (!cancelled) {
          setAuthState({ status: 'authenticated', user, account, error: '' })
        }
      } catch (error) {
        if (!cancelled) {
          setAuthState({
            status: 'error',
            user: null,
            account: null,
            error: formatAuthError(error, 'Unable to initialize Entra ID authentication.'),
          })
        }
      }
    }

    if (authConfig.mode === 'entra_id') {
      initializeEntraSession()
    } else {
      initializeMockSession()
    }

    return () => {
      cancelled = true
    }
  }, [refreshNonce])

  async function login() {
    if (authConfig.mode !== 'entra_id') {
      setRefreshNonce((value) => value + 1)
      return
    }

    if (!msalInstance || !authConfig.entra.isConfigured) {
      setAuthState((currentState) => ({
        ...currentState,
        status: 'error',
        error: authConfig.entra.configError || 'Entra ID is not configured.',
      }))
      return
    }

    await msalInstance.loginRedirect({
      scopes: authConfig.entra.scopes,
      redirectStartPage: window.location.href,
    })
  }

  async function logout() {
    if (authConfig.mode !== 'entra_id' || !msalInstance) {
      return
    }

    await msalInstance.logoutRedirect({
      account: authState.account || undefined,
    })
  }

  async function getAuthHeaders() {
    if (authConfig.mode === 'mock') {
      return buildMockHeaders()
    }

    if (!authState.account) {
      return {}
    }

    return acquireEntraHeaders(authState.account)
  }

  const value = {
    authMode: authConfig.mode,
    status: authState.status,
    user: authState.user,
    error: authState.error,
    isAuthenticated: authState.status === 'authenticated',
    login,
    logout,
    getAuthHeaders,
    hasAnyRole: (allowedRoles) => hasAnyRole(authState.user?.roles || [], allowedRoles),
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider.')
  }

  return context
}
