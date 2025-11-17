export const STORAGE_KEYS = {
  API_KEY: 'apiKey',
  USER_ID: 'userId',
}

export const DEFAULTS = {
  API_KEY: '',
  USER_ID: 'default-user',
  FORMAT: 'bestvideo+bestaudio/best',
}

export const FILE_SIZE = {
  MAX_MB: 300,
  MAX_BYTES: 300 * 1024 * 1024,
}

export const TIMEOUTS = {
  DEFAULT: 30000,
  DOWNLOAD: 300000,
}

export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${Math.round((bytes / Math.pow(k, i)) * 100) / 100} ${sizes[i]}`
}

export const formatDate = (timestamp) => {
  return new Date(timestamp * 1000).toLocaleString()
}

export const formatDuration = (seconds) => {
  if (!seconds) return 'N/A'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

export const isValidUrl = (url) => {
  if (!url) return false
  try {
    const urlObj = new URL(url)
    return urlObj.protocol === 'http:' || urlObj.protocol === 'https:'
  } catch {
    return false
  }
}

export const isValidApiKey = (key) => {
  return key && key.length >= 8
}

export const isValidUserId = (userId) => {
  return userId && userId.length > 0 && /^[a-zA-Z0-9._-]+$/.test(userId)
}

export const SUPPORTED_PLATFORMS = [
  'YouTube',
  'Facebook',
  'Instagram',
  'Twitter',
  'TikTok',
  'Vimeo',
  'Dailymotion',
  'And many more...',
]
