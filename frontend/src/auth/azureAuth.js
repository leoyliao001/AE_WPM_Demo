import { reactive } from 'vue'

const DEFAULT_CLIENT_ID = '9017db46-5822-46b7-8d47-c2bcf3a57876'
const DEFAULT_TENANT_ID = 'common'
const DEFAULT_USER_NAME = 'Signed in user'
const CLIENT_ID = import.meta.env.VITE_AZURE_CLIENT_ID || DEFAULT_CLIENT_ID
const TENANT_ID = import.meta.env.VITE_AZURE_TENANT_ID || DEFAULT_TENANT_ID
const REDIRECT_URI_OVERRIDE = import.meta.env.VITE_AZURE_REDIRECT_URI || ''
const AUTHORITY_BASE_URL = `https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0`
const SCOPES = ['openid', 'profile', 'offline_access', 'User.Read']
const STORAGE_PREFIX = 'wpm.azure.auth'
const ACCESS_TOKEN_KEY = `${STORAGE_PREFIX}.accessToken`
const REFRESH_TOKEN_KEY = `${STORAGE_PREFIX}.refreshToken`
const ID_TOKEN_KEY = `${STORAGE_PREFIX}.idToken`
const EXPIRES_AT_KEY = `${STORAGE_PREFIX}.expiresAt`
const USER_KEY = `${STORAGE_PREFIX}.user`
const STATE_KEY = `${STORAGE_PREFIX}.state`
const NONCE_KEY = `${STORAGE_PREFIX}.nonce`
const VERIFIER_KEY = `${STORAGE_PREFIX}.verifier`
const RETURN_URL_KEY = `${STORAGE_PREFIX}.returnUrl`
const CLOCK_SKEW_MS = 60 * 1000

export const azureAuthState = reactive({
  status: 'idle',
  isAuthenticated: false,
  user: null,
  accessToken: '',
  error: ''
})

function getRedirectUri() {
  const raw = REDIRECT_URI_OVERRIDE || `${window.location.origin}${window.location.pathname}`

  let normalized
  try {
    normalized = new URL(raw, window.location.origin)
  } catch {
    throw new Error('Azure SSO redirect URI is invalid. Check VITE_AZURE_REDIRECT_URI.')
  }

  const isLocalhost =
    normalized.hostname === 'localhost' ||
    normalized.hostname === '127.0.0.1' ||
    normalized.hostname === '::1'

  if (normalized.protocol !== 'https:' && !isLocalhost) {
    throw new Error('Azure SSO requires HTTPS redirect URI for non-localhost hosts.')
  }

  return normalized.toString()
}

function toBase64Url(input) {
  const bytes = input instanceof Uint8Array ? input : new Uint8Array(input)
  let binary = ''

  for (const byte of bytes) {
    binary += String.fromCharCode(byte)
  }

  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '')
}

function generateRandomString() {
  return toBase64Url(crypto.getRandomValues(new Uint8Array(32)))
}

async function sha256(value) {
  const buffer = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value))
  return new Uint8Array(buffer)
}

async function createPkcePair() {
  const verifier = generateRandomString()
  const challenge = toBase64Url(await sha256(verifier))

  return { verifier, challenge }
}

function parseJwt(token) {
  if (!token) {
    return null
  }

  const parts = token.split('.')

  if (parts.length < 2) {
    return null
  }

  try {
    const normalized = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), '=')
    const decoded = atob(padded)
    const json = decodeURIComponent(
      decoded
        .split('')
        .map((char) => `%${char.charCodeAt(0).toString(16).padStart(2, '0')}`)
        .join('')
    )

    return JSON.parse(json)
  } catch {
    return null
  }
}

function buildUserFromIdToken(idToken) {
  const claims = parseJwt(idToken) || {}

  return {
    name: claims.name || claims.preferred_username || claims.email || DEFAULT_USER_NAME,
    username: claims.preferred_username || claims.email || '',
    oid: claims.oid || '',
    tenantId: claims.tid || ''
  }
}

function loadStoredUser() {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function persistSession({ accessToken, refreshToken, idToken, expiresIn, user }) {
  const expiresAt = Date.now() + Number(expiresIn || 0) * 1000

  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken || '')
  localStorage.setItem(ID_TOKEN_KEY, idToken || '')
  localStorage.setItem(EXPIRES_AT_KEY, String(expiresAt))

  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  }

  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  }
}

function clearAuthSession() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(ID_TOKEN_KEY)
  localStorage.removeItem(EXPIRES_AT_KEY)
  localStorage.removeItem(USER_KEY)
}

function clearTransientAuthState() {
  sessionStorage.removeItem(STATE_KEY)
  sessionStorage.removeItem(NONCE_KEY)
  sessionStorage.removeItem(VERIFIER_KEY)
  sessionStorage.removeItem(RETURN_URL_KEY)
}

function setAuthenticatedState({ accessToken, user }) {
  azureAuthState.status = 'authenticated'
  azureAuthState.isAuthenticated = true
  azureAuthState.accessToken = accessToken
  azureAuthState.user = user
  azureAuthState.error = ''
}

function setErrorState(message) {
  azureAuthState.status = 'error'
  azureAuthState.isAuthenticated = false
  azureAuthState.accessToken = ''
  azureAuthState.user = null
  azureAuthState.error = message
}

async function fetchGraphProfile(accessToken, fallbackUser) {
  try {
    const response = await fetch('https://graph.microsoft.com/v1.0/me', {
      headers: {
        Authorization: `Bearer ${accessToken}`
      }
    })

    if (!response.ok) {
      return fallbackUser
    }

    const profile = await response.json()

    return {
      ...fallbackUser,
      name: profile.displayName || fallbackUser.name,
      username: profile.mail || profile.userPrincipalName || fallbackUser.username
    }
  } catch {
    return fallbackUser
  }
}

async function exchangeToken(body) {
  const response = await fetch(`${AUTHORITY_BASE_URL}/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: new URLSearchParams(body)
  })

  const payload = await response.json()

  if (!response.ok) {
    const errorMessage = payload.error_description || payload.error || 'Azure sign-in failed.'
    throw new Error(errorMessage)
  }

  return payload
}

async function refreshSession(refreshToken) {
  const tokenPayload = await exchangeToken({
    client_id: CLIENT_ID,
    grant_type: 'refresh_token',
    refresh_token: refreshToken,
    redirect_uri: getRedirectUri(),
    scope: SCOPES.join(' ')
  })
  const fallbackUser = buildUserFromIdToken(tokenPayload.id_token)
  const user = await fetchGraphProfile(tokenPayload.access_token, fallbackUser)

  persistSession({
    accessToken: tokenPayload.access_token,
    refreshToken: tokenPayload.refresh_token || refreshToken,
    idToken: tokenPayload.id_token,
    expiresIn: tokenPayload.expires_in,
    user
  })

  setAuthenticatedState({
    accessToken: tokenPayload.access_token,
    user
  })

  return true
}

async function handleAuthCallback(searchParams) {
  const returnedState = searchParams.get('state')
  const expectedState = sessionStorage.getItem(STATE_KEY)
  const codeVerifier = sessionStorage.getItem(VERIFIER_KEY)

  if (!returnedState || returnedState !== expectedState || !codeVerifier) {
    throw new Error('Azure sign-in state validation failed.')
  }

  const tokenPayload = await exchangeToken({
    client_id: CLIENT_ID,
    code: searchParams.get('code') || '',
    code_verifier: codeVerifier,
    grant_type: 'authorization_code',
    redirect_uri: getRedirectUri(),
    scope: SCOPES.join(' ')
  })
  const fallbackUser = buildUserFromIdToken(tokenPayload.id_token)
  const user = await fetchGraphProfile(tokenPayload.access_token, fallbackUser)
  const returnUrl = sessionStorage.getItem(RETURN_URL_KEY) || window.location.pathname

  persistSession({
    accessToken: tokenPayload.access_token,
    refreshToken: tokenPayload.refresh_token,
    idToken: tokenPayload.id_token,
    expiresIn: tokenPayload.expires_in,
    user
  })

  clearTransientAuthState()
  window.history.replaceState({}, document.title, returnUrl)
  setAuthenticatedState({
    accessToken: tokenPayload.access_token,
    user
  })
}

async function redirectToMicrosoftLogin() {
  const { verifier, challenge } = await createPkcePair()
  const state = generateRandomString()
  const nonce = generateRandomString()
  const currentUrl = `${window.location.pathname}${window.location.search}${window.location.hash}`
  const authorizeUrl = new URL(`${AUTHORITY_BASE_URL}/authorize`)

  sessionStorage.setItem(STATE_KEY, state)
  sessionStorage.setItem(NONCE_KEY, nonce)
  sessionStorage.setItem(VERIFIER_KEY, verifier)
  sessionStorage.setItem(RETURN_URL_KEY, currentUrl)

  authorizeUrl.search = new URLSearchParams({
    client_id: CLIENT_ID,
    response_type: 'code',
    redirect_uri: getRedirectUri(),
    response_mode: 'query',
    scope: SCOPES.join(' '),
    state,
    nonce,
    code_challenge: challenge,
    code_challenge_method: 'S256'
  }).toString()

  azureAuthState.status = 'redirecting'
  window.location.assign(authorizeUrl.toString())
}

async function restoreSession() {
  const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY)
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
  const expiresAt = Number(localStorage.getItem(EXPIRES_AT_KEY) || '0')
  const storedUser = loadStoredUser()

  if (accessToken && expiresAt > Date.now() + CLOCK_SKEW_MS && storedUser) {
    setAuthenticatedState({ accessToken, user: storedUser })
    return true
  }

  if (refreshToken) {
    try {
      return await refreshSession(refreshToken)
    } catch {
      clearAuthSession()
    }
  }

  return false
}

export async function initAzureAuth() {
  azureAuthState.status = 'loading'
  azureAuthState.error = ''

  if (!CLIENT_ID) {
    setErrorState('Azure SSO is not configured. Set VITE_AZURE_CLIENT_ID in the frontend environment.')
    return
  }

  const searchParams = new URLSearchParams(window.location.search)
  const authError = searchParams.get('error')

  if (authError) {
    const description = searchParams.get('error_description') || authError
    clearTransientAuthState()
    clearAuthSession()
    window.history.replaceState({}, document.title, window.location.pathname)
    setErrorState(`Azure sign-in failed: ${description}`)
    return
  }

  try {
    if (searchParams.get('code')) {
      await handleAuthCallback(searchParams)
      return
    }

    if (await restoreSession()) {
      return
    }

    await redirectToMicrosoftLogin()
  } catch (error) {
    clearTransientAuthState()
    clearAuthSession()
    setErrorState(error instanceof Error ? error.message : 'Azure sign-in failed.')
  }
}