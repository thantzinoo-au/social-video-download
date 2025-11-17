import React, { useState, useEffect, useCallback } from 'react'
import PropTypes from 'prop-types'
import './FileList.css'
import { FiRefreshCw, FiTrash2, FiFile, FiAlertCircle } from 'react-icons/fi'
import { listFiles, deleteFile } from '../services/api'
import { formatFileSize, formatDate } from '../utils/constants'

function FileList({ apiKey, userId }) {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [deleting, setDeleting] = useState(null)

  const loadFiles = useCallback(async () => {
    if (!apiKey) {
      setError('Please set your API key in Settings')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await listFiles(userId)

      if (response.success && response.data.success) {
        setFiles(response.data.files || [])
      } else {
        setError(response.error || 'Failed to load files')
      }
    } catch (err) {
      setError(err.message || 'Failed to load files')
    } finally {
      setLoading(false)
    }
  }, [apiKey, userId])

  const handleDeleteFile = async (filePath) => {
    if (!window.confirm('Are you sure you want to delete this file?')) {
      return
    }

    setDeleting(filePath)

    try {
      const response = await deleteFile(filePath)

      if (response.success) {
        setFiles(files.filter(f => f.path !== filePath))
      } else {
        alert(`Failed to delete file: ${response.error}`)
      }
    } catch (err) {
      alert(`Failed to delete file: ${err.message}`)
    } finally {
      setDeleting(null)
    }
  }

  useEffect(() => {
    if (apiKey && userId) {
      loadFiles()
    }
  }, [apiKey, userId, loadFiles])

  const getFileIcon = (filename) => {
    if (filename.endsWith('.json')) return '📄'
    if (filename.endsWith('.mp4')) return '🎥'
    if (filename.endsWith('.mp3')) return '🎵'
    return '📦'
  }

  return (
    <div className="file-list">
      <div className="file-list-header">
        <h2>My Downloads</h2>
        <button onClick={loadFiles} disabled={loading || !apiKey} className="refresh-btn">
          <FiRefreshCw className={loading ? 'spin' : ''} /> Refresh
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          <FiAlertCircle />
          <span>{error}</span>
        </div>
      )}

      {!loading && !error && files.length === 0 && (
        <div className="empty-state">
          <FiFile size={48} />
          <p>No files yet</p>
          <span>Download some videos to see them here!</span>
        </div>
      )}

      {files.length > 0 && (
        <div className="files-grid">
          {files.map((file, index) => (
            <div key={index} className="file-card">
              <div className="file-info">
                <div className="file-icon">
                  {getFileIcon(file.name)}
                </div>
                <div className="file-details">
                  <h3 className="file-name" title={file.name}>
                    {file.name}
                  </h3>
                  <p className="file-meta">
                    {formatFileSize(file.size)} • {formatDate(file.modified)}
                  </p>
                </div>
              </div>
              <div className="file-actions">
                <button
                  className="action-btn delete-btn"
                  onClick={() => handleDeleteFile(file.path)}
                  disabled={deleting === file.path}
                  title="Delete file"
                >
                  {deleting === file.path ? (
                    <FiRefreshCw className="spin" />
                  ) : (
                    <FiTrash2 />
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

FileList.propTypes = {
  apiKey: PropTypes.string.isRequired,
  userId: PropTypes.string.isRequired,
}

export default FileList

