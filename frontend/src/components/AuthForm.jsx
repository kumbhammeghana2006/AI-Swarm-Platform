import { useState } from 'react'
import { loginUser, registerUser } from '../api'

export default function AuthForm({ onAuthSuccess }) {
  const [isRegister, setIsRegister] = useState(false)
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  const handleModeSwitch = (registerMode) => {
    setIsRegister(registerMode)
    setError('')
    setSuccessMessage('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccessMessage('')

    // Basic Validation
    if (!username.trim() || !password.trim()) {
      setError('Please provide both username and password.')
      return
    }

    if (isRegister && !email.trim()) {
      setError('Please provide a valid email address.')
      return
    }

    setIsLoading(true)

    try {
      if (isRegister) {
        await registerUser({
          username: username.trim(),
          email: email.trim(),
          password,
        })
        setSuccessMessage('Account created successfully! Please log in with your credentials.')
        setIsRegister(false)
        setPassword('')
      } else {
        const tokenData = await loginUser({
          username: username.trim(),
          password,
        })
        if (onAuthSuccess) {
          onAuthSuccess(tokenData.access_token, username.trim())
        }
      }
    } catch (err) {
      setError(err.message || 'An unexpected error occurred.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="auth-card">
      <div className="auth-header">
        <h2 className="auth-title">
          {isRegister ? 'Create an Account' : 'Sign In to AI Swarm'}
        </h2>
        <p className="auth-subtitle">
          {isRegister
            ? 'Register to access the multi-agent AI Swarm Platform.'
            : 'Enter your credentials to manage and run swarm tasks.'}
        </p>
      </div>

      <div className="auth-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={!isRegister}
          className={`auth-tab ${!isRegister ? 'active' : ''}`}
          onClick={() => handleModeSwitch(false)}
        >
          Sign In
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={isRegister}
          className={`auth-tab ${isRegister ? 'active' : ''}`}
          onClick={() => handleModeSwitch(true)}
        >
          Register
        </button>
      </div>

      {error && (
        <div className="auth-banner error-banner" role="alert">
          {error}
        </div>
      )}

      {successMessage && (
        <div className="auth-banner success-banner" role="status">
          {successMessage}
        </div>
      )}

      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="input-group">
          <label htmlFor="username-input" className="auth-label">
            Username
          </label>
          <input
            id="username-input"
            type="text"
            className="auth-input"
            placeholder="Enter username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={isLoading}
            required
          />
        </div>

        {isRegister && (
          <div className="input-group">
            <label htmlFor="email-input" className="auth-label">
              Email Address
            </label>
            <input
              id="email-input"
              type="email"
              className="auth-input"
              placeholder="Enter email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
              required
            />
          </div>
        )}

        <div className="input-group">
          <label htmlFor="password-input" className="auth-label">
            Password
          </label>
          <input
            id="password-input"
            type="password"
            className="auth-input"
            placeholder="Enter password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isLoading}
            required
          />
        </div>

        <button
          type="submit"
          className="auth-submit-btn"
          disabled={isLoading}
        >
          {isLoading
            ? isRegister
              ? 'Creating Account...'
              : 'Signing In...'
            : isRegister
            ? 'Register'
            : 'Sign In'}
        </button>
      </form>
    </div>
  )
}
