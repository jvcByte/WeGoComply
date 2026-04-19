export const USER_ROLES = {
  ADMIN: 'admin',
  COMPLIANCE_OFFICER: 'compliance_officer',
  ANALYST: 'analyst',
  VIEWER: 'viewer',
}

export const ALL_ROLES = Object.values(USER_ROLES)

export function hasAnyRole(userRoles = [], allowedRoles = []) {
  if (!allowedRoles.length) {
    return true
  }

  const roleSet = new Set(userRoles)
  return allowedRoles.some((role) => roleSet.has(role))
}

export function formatRole(role) {
  return role
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}
