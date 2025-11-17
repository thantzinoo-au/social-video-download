import React, { useState } from 'react'
import PropTypes from 'prop-types'
import './Settings.css'
import { FiSave, FiKey, FiUser, FiCheckCircle, FiAlertCircle } from 'react-icons/fi'
import { isValidApiKey, isValidUserId } from '../utils/constants'

function Settings({ apiKey, userId, onApiKeyChange, onUserIdChange }) {
  const [localApiKey, setLocalApiKey] = useState(apiKey)
  const [localUserId, setLocalUserId] = useState(userId)
  const [saved, setSaved] = useState(false)
  const [errors, setErrors] = useState({})

  const validate = () => {
    const newErrors = {}

    if (!isValidApiKey(localApiKey)) {
      newErrors.apiKey = 'API key must be at least 8 characters'
    }

    if (!isValidUserId(localUserId)) {
      newErrors.userId = 'User ID must contain only letters, numbers, dots, dashes, or underscores'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSave = (e) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    onApiKeyChange(localApiKey)
    onUserIdChange(localUserId)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const handleApiKeyChange = (e) => {
    setLocalApiKey(e.target.value)
    if (errors.apiKey) {
      setErrors({ ...errors, apiKey: null })
    }
  }

  const handleUserIdChange = (e) => {
    setLocalUserId(e.target.value)
    if (errors.userId) {
      setErrors({ ...errors, userId: null })
    }
  }

  return (
    <div className="settings">
      <h2>Settings</h2>
      <p className="settings-description">
        Configure your API key and user preferences
      </p>

      <form onSubmit={handleSave} className="settings-form">
        <div className="form-group">
          <label htmlFor="apiKey">
            <FiKey /> API Key
          </label>
          <input
            type="text"
            id="apiKey"
            value={localApiKey}
            onChange={handleApiKeyChange}
            placeholder="Enter your API key"
            className={`settings-input ${errors.apiKey ? 'input-error' : ''}`}
          />
          {errors.apiKey && (
            <small className="error-text">
              <FiAlertCircle /> {errors.apiKey}
            </small>
          )}
          <small>Required to authenticate with the API server (min. 8 characters)</small>
        </div>

        <div className="form-group">
          <label htmlFor="userId">
            <FiUser /> User ID
          </label>
          <input
            type="text"
            id="userId"
            value={localUserId}
            onChange={handleUserIdChange}
            placeholder="Enter your user ID"
            className={`settings-input ${errors.userId ? 'input-error' : ''}`}
          />
          {errors.userId && (
            <small className="error-text">
              <FiAlertCircle /> {errors.userId}
            </small>
          )}
          <small>Files will be organized by this user ID</small>
        </div>

        <button type="submit" className="save-btn">
          {saved ? (
            <>
              <FiCheckCircle /> Saved!
            </>
          ) : (
            <>
              <FiSave /> Save Settings
            </>
          )}
        </button>
      </form>

      <div className="info-section">
        <h3>How to get started:</h3>
        <ol>
          <li>Make sure the API server is running on port 5001</li>
          <li>Enter your API key (check docker-compose.yml for the configured key)</li>
          <li>Set your user ID (or keep the default)</li>
          <li>Save settings and start downloading videos!</li>
        </ol>

        <div className="api-info">
          <strong>API Server:</strong> http://localhost:5001
        </div>
      </div>
    </div>
  )
}

Settings.propTypes = {
  apiKey: PropTypes.string.isRequired,
  userId: PropTypes.string.isRequired,
  onApiKeyChange: PropTypes.func.isRequired,
  onUserIdChange: PropTypes.func.isRequired,
}

export default Settings

