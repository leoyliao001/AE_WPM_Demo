/** Shared Bearer token for API calls (id_token preferred). */
const STORAGE_PREFIX = 'wpm.azure.auth'
const ACCESS_TOKEN_KEY = `${STORAGE_PREFIX}.accessToken`
const ID_TOKEN_KEY = `${STORAGE_PREFIX}.idToken`

export function getAuthBearerToken() {
  try {
    return localStorage.getItem(ID_TOKEN_KEY) || localStorage.getItem(ACCESS_TOKEN_KEY) || ''
  } catch {
    return ''
  }
}
