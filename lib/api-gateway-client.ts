/**
 * API Gateway Client
 * All frontend requests should go through the API Gateway at /api/*
 * The Gateway routes requests to the appropriate microservice
 */

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8000'

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  headers?: Record<string, string>
  body?: any
}

interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  status: number
}

/**
 * Get token from localStorage
 */
function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('token')
}

/**
 * Make API request to Gateway
 */
async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<ApiResponse<T>> {
  const url = `${API_GATEWAY_URL}${endpoint}`
  const token = getToken()

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  try {
    const response = await fetch(url, {
      method: options.method || 'GET',
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    })

    const data = await response.json()

    return {
      success: response.ok,
      data: response.ok ? data : undefined,
      error: !response.ok ? data.detail || data.error || 'Unknown error' : undefined,
      status: response.status,
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Network error',
      status: 0,
    }
  }
}

// ==================== AUTH ENDPOINTS ====================

export const auth = {
  register: async (email: string, name: string, password: string) => {
    return request('/api/auth/register', {
      method: 'POST',
      body: { email, name, password },
    })
  },

  login: async (email: string, password: string) => {
    return request('/api/auth/login', {
      method: 'POST',
      body: { email, password },
    })
  },

  refresh: async (refreshToken: string) => {
    return request('/api/auth/refresh', {
      method: 'POST',
      body: { refresh_token: refreshToken },
    })
  },

  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  },
}

// ==================== DRAFTS ENDPOINTS ====================

export const drafts = {
  list: async (skip: number = 0, limit: number = 50) => {
    return request('/api/drafts', {
      method: 'GET',
    })
  },

  create: async (data: {
    to_email: string
    cc?: string
    bcc?: string
    subject?: string
    body?: string
  }) => {
    return request('/api/drafts', {
      method: 'POST',
      body: data,
    })
  },

  get: async (draftId: string) => {
    return request(`/api/drafts/${draftId}`, {
      method: 'GET',
    })
  },

  update: async (
    draftId: string,
    data: {
      to_email?: string
      cc?: string
      bcc?: string
      subject?: string
      body?: string
    }
  ) => {
    return request(`/api/drafts/${draftId}`, {
      method: 'PUT',
      body: data,
    })
  },

  delete: async (draftId: string) => {
    return request(`/api/drafts/${draftId}`, {
      method: 'DELETE',
    })
  },

  send: async (draftId: string) => {
    return request(`/api/drafts/${draftId}/send`, {
      method: 'POST',
      body: {},
    })
  },
}

// ==================== EMAIL ENDPOINTS ====================

export const emails = {
  getInbox: async (skip: number = 0, limit: number = 50) => {
    return request(`/api/inbox?skip=${skip}&limit=${limit}`, {
      method: 'GET',
    })
  },

  getSent: async (skip: number = 0, limit: number = 50) => {
    return request(`/api/sent?skip=${skip}&limit=${limit}`, {
      method: 'GET',
    })
  },

  get: async (emailId: string) => {
    return request(`/api/emails/${emailId}`, {
      method: 'GET',
    })
  },

  search: async (query: string, skip: number = 0, limit: number = 50) => {
    return request(`/api/emails/search?query=${encodeURIComponent(query)}&skip=${skip}&limit=${limit}`, {
      method: 'GET',
    })
  },

  markRead: async (emailId: string, isRead: boolean) => {
    return request(`/api/emails/${emailId}/mark-read`, {
      method: 'POST',
      body: { is_read: isRead },
    })
  },

  delete: async (emailId: string) => {
    return request(`/api/emails/${emailId}`, {
      method: 'DELETE',
    })
  },
}

// ==================== UTILITY FUNCTIONS ====================

/**
 * Store authentication tokens
 */
export function setAuthTokens(token: string, refreshToken: string, user: any) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('token', token)
    localStorage.setItem('refresh_token', refreshToken)
    localStorage.setItem('user', JSON.stringify(user))
  }
}

/**
 * Get stored user
 */
export function getStoredUser() {
  if (typeof window === 'undefined') return null
  const userJson = localStorage.getItem('user')
  return userJson ? JSON.parse(userJson) : null
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  if (typeof window === 'undefined') return false
  return !!localStorage.getItem('token')
}

/**
 * Clear all auth data
 */
export function clearAuth() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }
}
