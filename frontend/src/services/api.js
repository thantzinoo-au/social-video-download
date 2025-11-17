import axios from 'axios'

const API_BASE_URL = '/api'
const DEFAULT_TIMEOUT = 30000
const DOWNLOAD_TIMEOUT = 300000

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: DEFAULT_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const setApiKey = (apiKey) => {
  if (apiKey) {
    apiClient.defaults.headers.common['X-API-Key'] = apiKey
  } else {
    delete apiClient.defaults.headers.common['X-API-Key']
  }
}

export const setSessionToken = (token) => {
  if (token) {
    apiClient.defaults.headers.common['X-Session-Token'] = token
  } else {
    delete apiClient.defaults.headers.common['X-Session-Token']
  }
}

const handleError = (error) => {
  if (error.response) {
    const message = error.response.data?.error || error.response.statusText || 'Server error'
    return {
      success: false,
      error: message,
      status: error.response.status,
    }
  } else if (error.request) {
    return {
      success: false,
      error: 'No response from server. Please check your connection.',
      status: 0,
    }
  } else {
    return {
      success: false,
      error: error.message || 'An unexpected error occurred',
      status: 0,
    }
  }
}

export const checkHealth = async () => {
  try {
    const response = await apiClient.get('/health')
    return { success: true, data: response.data }
  } catch (error) {
    return handleError(error)
  }
}

export const login = async (username, password) => {
  try {
    const response = await apiClient.post('/auth/login', { username, password })
    return { success: true, data: response.data }
  } catch (error) {
    return handleError(error)
  }
}

export const logout = async () => {
  try {
    const response = await apiClient.post('/auth/logout')
    return { success: true, data: response.data }
  } catch (error) {
    return handleError(error)
  }
}

export const verifySession = async () => {
  try {
    const response = await apiClient.get('/auth/verify')
    return { success: true, data: response.data }
  } catch (error) {
    return handleError(error)
  }
}

export const downloadVideo = async (url, userId, format = 'bestvideo+bestaudio/best') => {
  try {
    const response = await apiClient.post(
      '/download',
      { url, userId, format },
      { timeout: DOWNLOAD_TIMEOUT }
    )
    return { success: true, data: response.data }
  } catch (error) {
    return handleError(error)
  }
}

export const listFiles = async (userId) => {
  try {
    const response = await apiClient.get(`/list-files/${userId}`)
    return { success: true, data: response.data }
  } catch (error) {
    return handleError(error)
  }
}

export const deleteFile = async (filePath) => {
  try {
    const response = await apiClient.delete('/delete-file', {
      data: { file_path: filePath }
    })
    return { success: true, data: response.data }
  } catch (error) {
    return handleError(error)
  }
}

export const getFormats = async (url) => {
  try {
    const response = await apiClient.post('/formats', { url })
    return { success: true, data: response.data }
  } catch (error) {
    return handleError(error)
  }
}

export const getDiskUsage = async () => {
  try {
    const response = await apiClient.get('/disk-usage')
    return { success: true, data: response.data }
  } catch (error) {
    return handleError(error)
  }
}

export const downloadFileToDevice = (filePath, apiKey) => {
  const url = `${API_BASE_URL}/files/${filePath}`
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', '')
  
  if (apiKey) {
    fetch(url, {
      headers: { 'X-API-Key': apiKey }
    })
      .then(response => response.blob())
      .then(blob => {
        const blobUrl = window.URL.createObjectURL(blob)
        link.href = blobUrl
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(blobUrl)
      })
      .catch(error => {
        console.error('Download failed:', error)
      })
  } else {
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}

export default {
  setApiKey,
  setSessionToken,
  checkHealth,
  login,
  logout,
  verifySession,
  downloadVideo,
  listFiles,
  deleteFile,
  getFormats,
  getDiskUsage,
  downloadFileToDevice,
}
