import axios from 'axios'
import { useAuth } from '../auth/AuthProvider'
import { authConfig } from '../auth/config'

const apiClient = axios.create({
  baseURL: authConfig.apiBaseUrl || 'http://localhost:8000',
})

export function useApiClient() {
  const { getAuthHeaders } = useAuth()

  async function request(config) {
    const authHeaders = await getAuthHeaders()
    return apiClient.request({
      ...config,
      headers: {
        ...(config.headers || {}),
        ...authHeaders,
      },
    })
  }

  return {
    request,
    get(url, config = {}) {
      return request({
        ...config,
        method: 'get',
        url,
      })
    },
    post(url, data, config = {}) {
      return request({
        ...config,
        method: 'post',
        url,
        data,
      })
    },
  }
}

export function getApiErrorMessage(error, fallbackMessage = 'Request failed.') {
  const backendMessage = error?.response?.data?.error?.message
  const requestId = error?.response?.headers?.['x-request-id']
  const message = backendMessage || error?.message || fallbackMessage

  return requestId ? `${message} Request ID: ${requestId}` : message
}
