import React, { useState, useEffect } from 'react'
import DownloadForm from './components/DownloadForm'
import FileList from './components/FileList'
import Settings from './components/Settings'
import Login from './components/Login'
import AdminDashboard from './components/AdminDashboard'
import './App.css'
import { FiDownload, FiSettings, FiList } from 'react-icons/fi'
import { setApiKey, setSessionToken, verifySession } from './services/api'
import { STORAGE_KEYS, DEFAULTS } from './utils/constants'

function App() {
  const [activeTab, setActiveTab] = useState('download')
  const [apiKey, setApiKeyState] = useState(
    localStorage.getItem(STORAGE_KEYS.API_KEY) || DEFAULTS.API_KEY
  )
  const [userId, setUserIdState] = useState(
    localStorage.getItem(STORAGE_KEYS.USER_ID) || DEFAULTS.USER_ID
  )
  
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [sessionToken, setSessionTokenState] = useState(
    localStorage.getItem('session_token') || ''
  )
  const [user, setUser] = useState(null)
  const [isVerifying, setIsVerifying] = useState(true)

  useEffect(() => {
    const checkSession = async () => {
      const storedToken = localStorage.getItem('session_token')
      const storedUser = localStorage.getItem('user')
      
      if (storedToken && storedUser) {
        setSessionToken(storedToken)
        const result = await verifySession()
        
        if (result.success) {
          setIsAuthenticated(true)
          setUser(result.data.user)
        } else {
          localStorage.removeItem('session_token')
          localStorage.removeItem('user')
          setSessionToken('')
        }
      }
      
      setIsVerifying(false)
    }
    
    checkSession()
  }, [])

  useEffect(() => {
    if (apiKey) {
      setApiKey(apiKey)
    }
  }, [apiKey])

  const handleLoginSuccess = (token, userData) => {
    setSessionTokenState(token)
    setSessionToken(token)
    setUser(userData)
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    setSessionTokenState('')
    setSessionToken('')
    setUser(null)
    setIsAuthenticated(false)
    localStorage.removeItem('session_token')
    localStorage.removeItem('user')
  }

  const handleApiKeyChange = (key) => {
    setApiKeyState(key)
    localStorage.setItem(STORAGE_KEYS.API_KEY, key)
    setApiKey(key) // Update API service
  }

  const handleUserIdChange = (id) => {
    setUserIdState(id)
    localStorage.setItem(STORAGE_KEYS.USER_ID, id)
  }

  if (isVerifying) {
    return (
      <div className="app loading-screen">
        <div className="loading-spinner">Verifying session...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />
  }

  if (user && user.role === 'admin') {
    return (
      <AdminDashboard
        sessionToken={sessionToken}
        user={user}
        onLogout={handleLogout}
      />
    )
  }

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <div className="header-content">
            <div>
              <h1>🎥 Social Video Downloader</h1>
              <p>Download videos from your favorite platforms</p>
            </div>
            <div className="user-info">
              <span className="user-welcome">Welcome, {user?.username}</span>
              <button onClick={handleLogout} className="btn btn-logout">
                Logout
              </button>
            </div>
          </div>
        </header>

        <nav className="tabs">
          <button
            className={`tab ${activeTab === 'download' ? 'active' : ''}`}
            onClick={() => setActiveTab('download')}
          >
            <FiDownload /> Download
          </button>
          <button
            className={`tab ${activeTab === 'files' ? 'active' : ''}`}
            onClick={() => setActiveTab('files')}
          >
            <FiList /> My Files
          </button>
          <button
            className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <FiSettings /> Settings
          </button>
        </nav>

        <main className="content">
          {activeTab === 'download' && <DownloadForm apiKey={apiKey} userId={userId} />}
          {activeTab === 'files' && <FileList apiKey={apiKey} userId={userId} />}
          {activeTab === 'settings' && (
            <Settings
              apiKey={apiKey}
              userId={userId}
              onApiKeyChange={handleApiKeyChange}
              onUserIdChange={handleUserIdChange}
            />
          )}
        </main>
      </div>
    </div>
  )
}

export default App

