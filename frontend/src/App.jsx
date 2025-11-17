import React, { useState, useEffect } from 'react'
import DownloadForm from './components/DownloadForm'
import FileList from './components/FileList'
import Login from './components/Login'
import AdminDashboard from './components/AdminDashboard'
import './App.css'
import { FiDownload, FiList } from 'react-icons/fi'
import { setSessionToken, verifySession } from './services/api'

function App() {
  const [activeTab, setActiveTab] = useState('download')
  
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
        </nav>

        <main className="content">
          {activeTab === 'download' && <DownloadForm />}
          {activeTab === 'files' && <FileList />}
        </main>
      </div>
    </div>
  )
}

export default App

