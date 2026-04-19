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

const azureClientId = readEnv('VITE_AZURE_AD_B2C_CLIENT_ID')
const azureAuthority = readEnv('VITE_AZURE_AD_B2C_AUTHORITY')
const azureKnownAuthorities = parseCsv(readEnv('VITE_AZURE_AD_B2C_KNOWN_AUTHORITIES'))
const azureScopes = parseCsv(readEnv('VITE_AZURE_AD_B2C_SCOPES'))

const azureMissing = []
if (authMode === 'azure_ad_b2c') {
  if (!azureClientId) azureMissing.push('VITE_AZURE_AD_B2C_CLIENT_ID')
  if (!azureAuthority) azureMissing.push('VITE_AZURE_AD_B2C_AUTHORITY')
  if (!azureKnownAuthorities.length) azureMissing.push('VITE_AZURE_AD_B2C_KNOWN_AUTHORITIES')
  if (!azureScopes.length) azureMissing.push('VITE_AZURE_AD_B2C_SCOPES')
}

export const authConfig = {
  mode: authMode === 'azure_ad_b2c' ? 'azure_ad_b2c' : 'mock',
  apiBaseUrl,
  mock: {
    userId: readEnv('VITE_MOCK_AUTH_USER_ID', 'demo-admin'),
    email: readEnv('VITE_MOCK_AUTH_EMAIL', 'admin@wegocomply.local'),
    name: readEnv('VITE_MOCK_AUTH_NAME', 'Demo Admin'),
    roles: parseCsv(readEnv('VITE_MOCK_AUTH_ROLES', 'admin'), ['admin']),
  },
  azure: {
    isConfigured: azureMissing.length === 0,
    configError:
      azureMissing.length > 0
        ? `Azure AD B2C is enabled but missing: ${azureMissing.join(', ')}`
        : '',
    scopes: azureScopes,
    msal: {
      auth: {
        clientId: azureClientId,
        authority: azureAuthority,
        knownAuthorities: azureKnownAuthorities,
        redirectUri: readEnv('VITE_AZURE_AD_B2C_REDIRECT_URI', browserOrigin),
        postLogoutRedirectUri: readEnv('VITE_AZURE_AD_B2C_POST_LOGOUT_REDIRECT_URI', browserOrigin),
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
