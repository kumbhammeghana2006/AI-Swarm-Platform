const API_BASE_URL = 'http://localhost:8000'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/**
 * Authenticates user credentials with backend /auth/login.
 * @param {{ username: string, password: string }} credentials
 * @returns {Promise<{ access_token: string, token_type: string }>}
 */
export async function loginUser(credentials) {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      const detail = data.detail || 'Invalid username or password.'
      throw new ApiError(typeof detail === 'string' ? detail : JSON.stringify(detail), response.status)
    }

    return data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new ApiError('Unable to connect to authentication server. Please ensure backend is running at http://localhost:8000.', 500)
    }
    throw error
  }
}

/**
 * Registers a new user with backend /auth/register.
 * @param {{ username: string, email: string, password: string }} userData
 * @returns {Promise<{ id: number, username: string, email: string, role: string }>}
 */
export async function registerUser(userData) {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: userData.username,
        email: userData.email,
        password: userData.password,
        role: 'USER',
      }),
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      const detail = data.detail || 'Registration failed. Please check your inputs.'
      throw new ApiError(typeof detail === 'string' ? detail : JSON.stringify(detail), response.status)
    }

    return data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new ApiError('Unable to connect to authentication server. Please ensure backend is running at http://localhost:8000.', 500)
    }
    throw error
  }
}

/**
 * Submits a new task to backend /tasks.
 * @param {string} taskText
 * @param {string} token
 * @returns {Promise<Object>}
 */
export async function submitTask(taskText, token) {
  try {
    const response = await fetch(`${API_BASE_URL}/tasks`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ task_text: taskText }),
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      if (response.status === 401) {
        throw new ApiError('Session expired or invalid authentication token. Please log in again.', 401)
      }
      const detail = data.detail || 'Task execution failed. Please check your input.'
      const message = typeof detail === 'string' ? detail : JSON.stringify(detail)
      throw new ApiError(message, response.status)
    }

    return data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new ApiError('Unable to connect to task server. Please ensure backend is running at http://localhost:8000.', 500)
    }
    throw new ApiError(error.message || 'An unexpected error occurred.', 500)
  }
}

/**
 * Retrieves task history for the authenticated user from backend /tasks.
 * @param {string} token
 * @returns {Promise<Array<Object>>}
 */
export async function fetchUserTasks(token) {
  try {
    const response = await fetch(`${API_BASE_URL}/tasks`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    const data = await response.json().catch(() => ([]))

    if (!response.ok) {
      if (response.status === 401) {
        throw new ApiError('Session expired or invalid authentication token. Please log in again.', 401)
      }
      const detail = data.detail || 'Failed to retrieve task history.'
      const message = typeof detail === 'string' ? detail : JSON.stringify(detail)
      throw new ApiError(message, response.status)
    }

    return data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new ApiError('Unable to connect to task server. Please ensure backend is running at http://localhost:8000.', 500)
    }
    throw new ApiError(error.message || 'An unexpected error occurred while fetching task history.', 500)
  }
}

/**
 * Retrieves empirical evaluation metrics summary from backend /tasks/metrics/summary.
 * @param {string} token
 * @returns {Promise<Object>}
 */
export async function fetchMetricsSummary(token) {
  try {
    const response = await fetch(`${API_BASE_URL}/tasks/metrics/summary`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      if (response.status === 401) {
        throw new ApiError('Session expired or invalid authentication token. Please log in again.', 401)
      }
      const detail = data.detail || 'Failed to retrieve evaluation metrics.'
      const message = typeof detail === 'string' ? detail : JSON.stringify(detail)
      throw new ApiError(message, response.status)
    }

    return data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new ApiError('Unable to connect to metrics server. Please ensure backend is running at http://localhost:8000.', 500)
    }
    throw new ApiError(error.message || 'An unexpected error occurred while fetching metrics.', 500)
  }
}

/**
 * Retrieves registered benchmark experiment and ablation configurations from backend.
 * @param {string} token
 * @returns {Promise<Array<Object>>}
 */
export async function fetchExperimentConfigs(token) {
  try {
    const response = await fetch(`${API_BASE_URL}/tasks/experiments/configurations`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    const data = await response.json().catch(() => ([]))

    if (!response.ok) {
      if (response.status === 401) {
        throw new ApiError('Session expired or invalid authentication token. Please log in again.', 401)
      }
      const detail = data.detail || 'Failed to retrieve experiment configurations.'
      const message = typeof detail === 'string' ? detail : JSON.stringify(detail)
      throw new ApiError(message, response.status)
    }

    return data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new ApiError('Unable to connect to experiment server. Please ensure backend is running at http://localhost:8000.', 500)
    }
    throw new ApiError(error.message || 'An unexpected error occurred while fetching experiment configurations.', 500)
  }
}


