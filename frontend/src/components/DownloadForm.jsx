import React, { useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import './DownloadForm.css'
import { FiDownload, FiLoader, FiCheckCircle, FiAlertCircle } from 'react-icons/fi'
import { downloadVideo } from '../services/api'
import { isValidUrl, formatDuration, SUPPORTED_PLATFORMS, FILE_SIZE } from '../utils/constants'

function DownloadForm({ apiKey, userId }) {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    setResult(null)
    setError(null)
  }, [userId])

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!apiKey) {
      setError('Please set your API key in Settings')
      return
    }

    if (!url) {
      setError('Please enter a video URL')
      return
    }

    if (!isValidUrl(url)) {
      setError('Please enter a valid URL (must start with http:// or https://)')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await downloadVideo(url, userId)

      if (response.success && response.data.success) {
        setResult(response.data)
        setUrl('') // Clear input on success
      } else {
        setError(response.error || response.data?.error || 'Download failed')
      }
    } catch (err) {
      setError(err.message || 'An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleUrlChange = (e) => {
    setUrl(e.target.value)
    if (error) setError(null)
    if (result) setResult(null)
  }

  return (
    <div className="download-form">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="url">Video URL</label>
          <input
            type="text"
            id="url"
            value={url}
            onChange={handleUrlChange}
            placeholder="Paste video URL here..."
            disabled={loading}
            className="url-input"
            autoComplete="off"
          />
        </div>

        <button type="submit" disabled={loading || !apiKey || !url} className="download-btn">
          {loading ? (
            <>
              <FiLoader className="spin" /> Downloading...
            </>
          ) : (
            <>
              <FiDownload /> Download Video
            </>
          )}
        </button>
      </form>

      {error && (
        <div className="alert alert-error">
          <FiAlertCircle />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className="alert alert-success">
          <FiCheckCircle />
          <div>
            <strong>Download Complete!</strong>
            <p><strong>Title:</strong> {result.title}</p>
            {result.duration && (
              <p><strong>Duration:</strong> {formatDuration(result.duration)}</p>
            )}
            <p className="file-path">
              <strong>File:</strong> {result.file_path}
            </p>
          </div>
        </div>
      )}

      <div className="info-box">
        <h3>Supported Platforms</h3>
        <p>Download videos from {SUPPORTED_PLATFORMS.length}+ platforms!</p>
        <ul>
          {SUPPORTED_PLATFORMS.slice(0, 5).map((platform, idx) => (
            <li key={idx}>✓ {platform}</li>
          ))}
        </ul>
        <p style={{ marginTop: '15px', fontSize: '0.9rem', color: '#6c757d' }}>
          <strong>Note:</strong> Maximum file size is {FILE_SIZE.MAX_MB}MB
        </p>
      </div>
    </div>
  )
}

DownloadForm.propTypes = {
  apiKey: PropTypes.string.isRequired,
  userId: PropTypes.string.isRequired,
}

export default DownloadForm

