import { useState, useEffect, useCallback } from 'react'
import AuthForm from './components/AuthForm'
import { submitTask, fetchUserTasks, ApiError } from './api'
import './App.css'

function App() {
  const [token, setToken] = useState(() => localStorage.getItem('swarm_token') || '')
  const [username, setUsername] = useState(() => localStorage.getItem('swarm_username') || '')
  const [taskInput, setTaskInput] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [taskResult, setTaskResult] = useState(null)
  const [taskHistory, setTaskHistory] = useState([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  const handleLogout = useCallback(() => {
    setToken('')
    setUsername('')
    setTaskInput('')
    setTaskResult(null)
    setTaskHistory([])
    setErrorMessage('')
    localStorage.removeItem('swarm_token')
    localStorage.removeItem('swarm_username')
  }, [])

  const loadTaskHistory = useCallback(async (authToken) => {
    if (!authToken) return
    setIsLoadingHistory(true)
    try {
      const history = await fetchUserTasks(authToken)
      setTaskHistory(history)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        handleLogout()
        setErrorMessage('Session expired. Please log in again.')
      } else {
        console.error('Failed to load task history:', err.message)
      }
    } finally {
      setIsLoadingHistory(false)
    }
  }, [handleLogout])

  useEffect(() => {
    let isCancelled = false
    if (token) {
      localStorage.setItem('swarm_token', token)
      fetchUserTasks(token)
        .then((history) => {
          if (!isCancelled) {
            setTaskHistory(history)
          }
        })
        .catch((err) => {
          if (!isCancelled) {
            if (err instanceof ApiError && err.status === 401) {
              handleLogout()
              setErrorMessage('Session expired. Please log in again.')
            } else {
              console.error('Failed to load task history:', err.message)
            }
          }
        })
    } else {
      localStorage.removeItem('swarm_token')
    }
    return () => {
      isCancelled = true
    }
  }, [token, handleLogout])

  useEffect(() => {
    if (username) {
      localStorage.setItem('swarm_username', username)
    } else {
      localStorage.removeItem('swarm_username')
    }
  }, [username])

  const handleAuthSuccess = (newToken, authUsername) => {
    setErrorMessage('')
    setToken(newToken)
    setUsername(authUsername)
  }

  const handleRunSwarm = async () => {
    const trimmedInput = taskInput.trim()
    if (!trimmedInput) {
      setErrorMessage('Please enter a task description before running the swarm.')
      return
    }

    setIsSubmitting(true)
    setErrorMessage('')
    setTaskResult(null)

    try {
      const result = await submitTask(trimmedInput, token)
      setTaskResult(result)
      setTaskInput('')
      await loadTaskHistory(token)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        handleLogout()
        setErrorMessage('Session expired or invalid authentication token. Please log in again.')
      } else {
        setErrorMessage(err.message || 'An error occurred while executing the task.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    try {
      return new Date(dateString).toLocaleString()
    } catch {
      return dateString
    }
  }

  return (
    <div className="app-root">
      {token && (
        <nav className="navbar">
          <div className="navbar-brand">AI Swarm Platform</div>
          <div className="navbar-user">
            <span className="user-badge">User: <strong>{username || 'Authenticated User'}</strong></span>
            <button
              type="button"
              className="logout-btn"
              onClick={handleLogout}
            >
              Log Out
            </button>
          </div>
        </nav>
      )}

      <div className="dashboard-container">
        <header className="dashboard-header">
          <h1 className="dashboard-title">AI Swarm Platform</h1>
          <p className="dashboard-description">
            An autonomous multi-agent swarm system for dynamic task routing, code generation, automated testing, code review, and documentation.
          </p>
        </header>

        <main className="dashboard-main">
          {!token ? (
            <div>
              {errorMessage && (
                <div className="status-banner status-error" role="alert">
                  {errorMessage}
                </div>
              )}
              <AuthForm onAuthSuccess={handleAuthSuccess} />
            </div>
          ) : (
            <div className="dashboard-content">
              {/* Task Submission Card */}
              <div className="task-card">
                <h2 className="card-title">Submit Swarm Task</h2>
                <div className="input-group">
                  <label htmlFor="task-input" className="task-label">
                    Task Description
                  </label>
                  <textarea
                    id="task-input"
                    className="task-textarea"
                    rows={6}
                    placeholder="Describe the task for the AI Swarm (e.g., Write a Python function to parse logs and detect anomalies)..."
                    value={taskInput}
                    disabled={isSubmitting}
                    onChange={(e) => setTaskInput(e.target.value)}
                  />
                </div>

                <div className="action-row">
                  <button
                    id="run-swarm-btn"
                    type="button"
                    className={`run-button ${isSubmitting ? 'loading' : ''}`}
                    onClick={handleRunSwarm}
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? (
                      <span className="button-loading-content">
                        <span className="spinner" />
                        Executing AI Swarm...
                      </span>
                    ) : (
                      'Run AI Swarm'
                    )}
                  </button>
                </div>

                {errorMessage && (
                  <div className="status-banner status-error" role="alert">
                    {errorMessage}
                  </div>
                )}
              </div>

              {/* Task Result Card */}
              {taskResult && (
                <div className="result-card">
                  <div className="result-header">
                    <h2 className="card-title">Swarm Execution Result</h2>
                    <span className={`status-badge status-${(taskResult.status || 'unknown').toLowerCase()}`}>
                      {taskResult.status}
                    </span>
                  </div>

                  <div className="result-meta">
                    <div className="meta-item">
                      <span className="meta-label">Task ID:</span>
                      <span className="meta-value">#{taskResult.id}</span>
                    </div>
                    {taskResult.task_type && (
                      <div className="meta-item">
                        <span className="meta-label">Task Type:</span>
                        <span className="meta-value">{taskResult.task_type}</span>
                      </div>
                    )}
                    <div className="meta-item">
                      <span className="meta-label">Created:</span>
                      <span className="meta-value">{formatDate(taskResult.created_at)}</span>
                    </div>
                    {taskResult.result && (
                      <div className="meta-item">
                        <span className="meta-label">Iterations:</span>
                        <span className="meta-value">{taskResult.result.iteration_count}</span>
                      </div>
                    )}
                  </div>

                  <div className="result-section">
                    <h3 className="section-subtitle">Submitted Task:</h3>
                    <p className="task-summary-text">{taskResult.task_text}</p>
                  </div>

                  {taskResult.result && (
                    <div className="result-section">
                      <div className="section-header-inline">
                        <h3 className="section-subtitle">Final Swarm Output:</h3>
                        <span className={`status-badge status-${(taskResult.result.execution_status || 'unknown').toLowerCase()}`}>
                          {taskResult.result.execution_status}
                        </span>
                      </div>
                      <pre className="output-code-block">
                        {taskResult.result.final_output || 'No output returned.'}
                      </pre>
                    </div>
                  )}
                </div>
              )}

              {/* Task History Section */}
              <div className="history-card">
                <div className="history-header">
                  <h2 className="card-title">Task History</h2>
                  {isLoadingHistory && <span className="history-loading">Refreshing...</span>}
                </div>

                {taskHistory.length === 0 ? (
                  <p className="history-empty">
                    {isLoadingHistory ? 'Loading task history...' : 'No previous tasks found.'}
                  </p>
                ) : (
                  <div className="history-list">
                    {taskHistory.map((task) => (
                      <div key={task.id} className="history-item">
                        <div className="history-item-header">
                          <div className="history-item-title">
                            <span className="history-task-id">#{task.id}</span>
                            <span className="history-date">{formatDate(task.created_at)}</span>
                          </div>
                          <span className={`status-badge status-${(task.status || 'unknown').toLowerCase()}`}>
                            {task.status}
                          </span>
                        </div>

                        <p className="history-task-text">{task.task_text}</p>

                        {task.result && (
                          <details className="history-details">
                            <summary className="history-summary font-semibold">
                              View Output ({task.result.execution_status} - {task.result.iteration_count} iteration{task.result.iteration_count !== 1 ? 's' : ''})
                            </summary>
                            <pre className="output-code-block snippet">
                              {task.result.final_output || 'No output returned.'}
                            </pre>
                          </details>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default App

