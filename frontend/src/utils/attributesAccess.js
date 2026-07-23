import axios from 'axios'
import { getCurrentUserEmail } from '../auth/azureAuth.js'

let cachedAccess = null
let inflight = null

export function clearAttributesAccessCache() {
  cachedAccess = null
  inflight = null
}

export async function fetchMyAttributesAccess({ force = false } = {}) {
  if (!force && cachedAccess) return cachedAccess
  if (!force && inflight) return inflight

  inflight = axios
    .get('/api/project-attributes-access/me/')
    .then(({ data }) => {
      cachedAccess = data || {
        email: getCurrentUserEmail(),
        is_super_admin: false,
        authenticated: false,
        tables: {}
      }
      return cachedAccess
    })
    .catch((error) => {
      cachedAccess = {
        email: getCurrentUserEmail(),
        is_super_admin: false,
        authenticated: false,
        tables: {},
        error: error?.response?.data?.error || error.message
      }
      return cachedAccess
    })
    .finally(() => {
      inflight = null
    })

  return inflight
}

export function canAccessAttributesTable(access, tableKey) {
  if (!access) return false
  if (access.is_super_admin) return true
  return !!access.tables?.[tableKey]
}
