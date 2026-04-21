function readEnv(name, fallback = '') {
  const value = import.meta.env[name]
  return typeof value === 'string' ? value.trim() : fallback
}

function parseCsv(value, fallback = []) {
  if (!value) {
    return fallback
  }

  const entries = value
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean)

  return entries.length ? entries : fallback
}

function normalizeBaseUrl(value) {
  return value ? value.replace(/\/+$/, '') : ''
}

const browserOrigin =
  typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:5173'

const authMode = readEnv('VITE_AUTH_MODE', 'mock').toLowerCase()
const apiBaseUrl = normalizeBaseUrl(readEnv('VITE_API_BASE_URL', ''))

const entraClientId  = readEnv('VITE_ENTRA_CLIENT_ID')
const entraTenantId  = readEnv('VITE_ENTRA_TENANT_ID')
const entraScopes    = parseCsv(readEnv('VITE_ENTRA_SCOPES'))

const entraMissing = []
if (authMode === 'entra_id') {
  if (!entraClientId) entraMissing.push('VITE_ENTRA_CLIENT_ID')
  if (!entraTenantId) entraMissing.push('VITE_ENTRA_TENANT_ID')
  if (!entraScopes.length) entraMissing.push('VITE_ENTRA_SCOPES')
}

export const authConfig = {
  mode: authMode === 'entra_id' ? 'entra_id' : 'mock',
  apiBaseUrl,
  mock: {
    userId: readEnv('VITE_MOCK_AUTH_USER_ID', 'demo-admin'),
    email: readEnv('VITE_MOCK_AUTH_EMAIL', 'admin@wegocomply.local'),
    name: readEnv('VITE_MOCK_AUTH_NAME', 'Demo Admin'),
    roles: parseCsv(readEnv('VITE_MOCK_AUTH_ROLES', 'admin'), ['admin']),
  },
  entra: {
    isConfigured: entraMissing.length === 0,
    configError:
      entraMissing.length > 0
        ? `Entra ID is enabled but missing: ${entraMissing.join(', ')}`
        : '',
    scopes: entraScopes.length ? entraScopes : [`api://${entraClientId}/.default`],
    msal: {
      auth: {
        clientId: entraClientId,
        authority: `https://login.microsoftonline.com/${entraTenantId}`,
        redirectUri: readEnv('VITE_ENTRA_REDIRECT_URI', browserOrigin),
        postLogoutRedirectUri: readEnv('VITE_ENTRA_POST_LOGOUT_REDIRECT_URI', browserOrigin),
      },
      cache: {
        cacheLocation: 'sessionStorage',
        storeAuthStateInCookie: false,
      },
    },
  },
}

export function buildMockHeaders() {
  return {
    'X-Mock-User': authConfig.mock.userId,
    'X-Mock-Email': authConfig.mock.email,
    'X-Mock-Name': authConfig.mock.name,
    'X-Mock-Roles': authConfig.mock.roles.join(','),
  }
}
