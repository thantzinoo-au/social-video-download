import React, { useState, useEffect } from 'react'
import './AdminDashboard.css'

function AdminDashboard({ sessionToken, user, onLogout }) {
  const [activeTab, setActiveTab] = useState('api-keys')
  const [apiKeys, setApiKeys] = useState([])
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  
  const [newKeyUsername, setNewKeyUsername] = useState('')
  const [newKeyDescription, setNewKeyDescription] = useState('')
  const [newKeyExpiresDays, setNewKeyExpiresDays] = useState('')
  const [createdApiKey, setCreatedApiKey] = useState('')
  
  const [newUserUsername, setNewUserUsername] = useState('')
  const [newUserPassword, setNewUserPassword] = useState('')
  const [newUserRole, setNewUserRole] = useState('user')

  useEffect(() => {
    if (activeTab === 'api-keys') {
      loadApiKeys()
    } else if (activeTab === 'users') {
      loadUsers()
    }
  }, [activeTab])

  const loadApiKeys = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await fetch('/api/admin/api-keys', {
        headers: {
          'X-Session-Token': sessionToken,
        },
      })
      const data = await response.json()
      
      if (data.success) {
        setApiKeys(data.api_keys)
      } else {
        setError(data.error || 'Failed to load API keys')
      }
    } catch (err) {
      setError('Network error')
      console.error('Load API keys error:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadUsers = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await fetch('/api/admin/users', {
        headers: {
          'X-Session-Token': sessionToken,
        },
      })
      const data = await response.json()
      
      if (data.success) {
        setUsers(data.users)
      } else {
        setError(data.error || 'Failed to load users')
      }
    } catch (err) {
      setError('Network error')
      console.error('Load users error:', err)
    } finally {
      setLoading(false)
    }
  }

  const createApiKey = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setCreatedApiKey('')
    
    try {
      const response = await fetch('/api/admin/api-keys/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': sessionToken,
        },
        body: JSON.stringify({
          username: newKeyUsername,
          description: newKeyDescription,
          expires_days: newKeyExpiresDays ? parseInt(newKeyExpiresDays) : null,
        }),
      })
      
      const data = await response.json()
      
      if (data.success) {
        setSuccess('API key created successfully!')
        setCreatedApiKey(data.api_key)
        setNewKeyUsername('')
        setNewKeyDescription('')
        setNewKeyExpiresDays('')
        loadApiKeys()
      } else {
        setError(data.error || 'Failed to create API key')
      }
    } catch (err) {
      setError('Network error')
      console.error('Create API key error:', err)
    }
  }

  const revokeApiKey = async (keyId) => {
    if (!confirm('Are you sure you want to revoke this API key?')) {
      return
    }
    
    setError('')
    setSuccess('')
    
    try {
      const response = await fetch(`/api/admin/api-keys/${keyId}/revoke`, {
        method: 'POST',
        headers: {
          'X-Session-Token': sessionToken,
        },
      })
      
      const data = await response.json()
      
      if (data.success) {
        setSuccess('API key revoked successfully!')
        loadApiKeys()
      } else {
        setError(data.error || 'Failed to revoke API key')
      }
    } catch (err) {
      setError('Network error')
      console.error('Revoke API key error:', err)
    }
  }

  const createUser = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    
    try {
      const response = await fetch('/api/admin/users/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-Token': sessionToken,
        },
        body: JSON.stringify({
          username: newUserUsername,
          password: newUserPassword,
          role: newUserRole,
        }),
      })
      
      const data = await response.json()
      
      if (data.success) {
        setSuccess('User created successfully!')
        setNewUserUsername('')
        setNewUserPassword('')
        setNewUserRole('user')
        loadUsers()
      } else {
        setError(data.error || 'Failed to create user')
      }
    } catch (err) {
      setError('Network error')
      console.error('Create user error:', err)
    }
  }

  const handleLogout = async () => {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
          'X-Session-Token': sessionToken,
        },
      })
    } catch (err) {
      console.error('Logout error:', err)
    }
    
    localStorage.removeItem('session_token')
    localStorage.removeItem('user')
    onLogout()
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    setSuccess('Copied to clipboard!')
    setTimeout(() => setSuccess(''), 2000)
  }

  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <div className="admin-header-content">
          <h1>🛠️ Admin Dashboard</h1>
          <div className="admin-user-info">
            <span className="user-badge">
              {user.username} ({user.role})
            </span>
            <button onClick={handleLogout} className="btn btn-secondary">
              Logout
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      <div className="admin-tabs">
        <button
          className={`tab ${activeTab === 'api-keys' ? 'active' : ''}`}
          onClick={() => setActiveTab('api-keys')}
        >
          API Keys
        </button>
        <button
          className={`tab ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          Users
        </button>
      </div>

      <div className="admin-content">
        {activeTab === 'api-keys' && (
          <div className="api-keys-section">
            <div className="section-card">
              <h2>Create API Key</h2>
              <form onSubmit={createApiKey} className="create-form">
                <div className="form-row">
                  <div className="form-group">
                    <label>Username</label>
                    <input
                      type="text"
                      value={newKeyUsername}
                      onChange={(e) => setNewKeyUsername(e.target.value)}
                      placeholder="Enter username"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Description (optional)</label>
                    <input
                      type="text"
                      value={newKeyDescription}
                      onChange={(e) => setNewKeyDescription(e.target.value)}
                      placeholder="API key description"
                    />
                  </div>
                  <div className="form-group">
                    <label>Expires in days (optional)</label>
                    <input
                      type="number"
                      value={newKeyExpiresDays}
                      onChange={(e) => setNewKeyExpiresDays(e.target.value)}
                      placeholder="Leave empty for no expiration"
                      min="1"
                    />
                  </div>
                </div>
                <button type="submit" className="btn btn-primary">
                  Create API Key
                </button>
              </form>

              {createdApiKey && (
                <div className="created-key-display">
                  <p><strong>⚠️ Save this API key - it won't be shown again!</strong></p>
                  <div className="key-display">
                    <code>{createdApiKey}</code>
                    <button
                      onClick={() => copyToClipboard(createdApiKey)}
                      className="btn btn-small"
                    >
                      Copy
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="section-card">
              <h2>API Keys ({apiKeys.length})</h2>
              {loading ? (
                <p>Loading...</p>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Username</th>
                        <th>API Key</th>
                        <th>Description</th>
                        <th>Created</th>
                        <th>Expires</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {apiKeys.map((key) => (
                        <tr key={key.id}>
                          <td>{key.username}</td>
                          <td><code>{key.api_key}</code></td>
                          <td>{key.description || '-'}</td>
                          <td>{new Date(key.created_at).toLocaleDateString()}</td>
                          <td>
                            {key.expires_at
                              ? new Date(key.expires_at).toLocaleDateString()
                              : 'Never'}
                          </td>
                          <td>
                            <span className={`status-badge ${
                              !key.is_active ? 'revoked' :
                              key.is_expired ? 'expired' : 'active'
                            }`}>
                              {!key.is_active ? 'Revoked' :
                               key.is_expired ? 'Expired' : 'Active'}
                            </span>
                          </td>
                          <td>
                            {key.is_active && !key.is_expired && (
                              <button
                                onClick={() => revokeApiKey(key.id)}
                                className="btn btn-danger btn-small"
                              >
                                Revoke
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div className="users-section">
            <div className="section-card">
              <h2>Create User</h2>
              <form onSubmit={createUser} className="create-form">
                <div className="form-row">
                  <div className="form-group">
                    <label>Username</label>
                    <input
                      type="text"
                      value={newUserUsername}
                      onChange={(e) => setNewUserUsername(e.target.value)}
                      placeholder="Enter username"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Password</label>
                    <input
                      type="password"
                      value={newUserPassword}
                      onChange={(e) => setNewUserPassword(e.target.value)}
                      placeholder="Min 8 characters"
                      required
                      minLength="8"
                    />
                  </div>
                  <div className="form-group">
                    <label>Role</label>
                    <select
                      value={newUserRole}
                      onChange={(e) => setNewUserRole(e.target.value)}
                    >
                      <option value="user">User</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                </div>
                <button type="submit" className="btn btn-primary">
                  Create User
                </button>
              </form>
            </div>

            <div className="section-card">
              <h2>Users ({users.length})</h2>
              {loading ? (
                <p>Loading...</p>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Role</th>
                        <th>Created</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((u) => (
                        <tr key={u.id}>
                          <td>{u.id}</td>
                          <td>{u.username}</td>
                          <td>
                            <span className={`role-badge ${u.role}`}>
                              {u.role}
                            </span>
                          </td>
                          <td>{new Date(u.created_at).toLocaleDateString()}</td>
                          <td>
                            <span className={`status-badge ${u.is_active ? 'active' : 'inactive'}`}>
                              {u.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AdminDashboard
