/**
 * Shared Axios instance with automatic auth-token injection.
 *
 * All API calls should go through this client so the Bearer token
 * (from localStorage) is attached to every request.
 */

import axios from 'axios'

const TOKEN_KEY = 'argo_auth_token'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach Bearer token to every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// On 401, clear token so the login page shows
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      window.location.reload()
    }
    return Promise.reject(error)
  },
)

export default apiClient
