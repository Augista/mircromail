// /**
//  * API Client for MicroMail
//  * Handles all communication with the API Gateway
//  */

// const API_Gateway_URL = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8000'
// const AuthServiceURL = process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || 'http://localhost:8001'

// interface RequestOptions extends RequestInit {
//   params?: Record<string, string | number | boolean>
// }

// export class APIError extends Error {
//   constructor(
//     public status: number,
//     public message: string,
//     public details?: unknown
//   ) {
//     super(message)
//   }
// }

// interface AuthUser {
//   id: string
//   email: string
//   name: string
// }

// interface AuthResponse {
//   user: AuthUser
//   access_token: string
//   refresh_token: string
//   token_type: string
//   expires_in: number
// }

// interface TokenResponse {
//   access_token: string
//   refresh_token: string
//   token_type: string
//   expires_in: number
// }

// /**
//  * Make an API request with automatic token handling and error handling
//  */
// export async function apiRequest<T>(
//   endpoint: string,
//   options: RequestOptions = {}
// ): Promise<T> {
//   const { params, ...fetchOptions } = options

//   // Build URL with query parameters
//   const url = new URL(`${API_URL}${endpoint}`)
//   if (params) {
//     Object.entries(params).forEach(([key, value]) => {
//       url.searchParams.append(key, String(value))
//     })
//   }

//   // Get auth token from localStorage
//   const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null

//   // Set up headers reliably for all HeadersInit shapes
//   const headers = new Headers({
//     'Content-Type': 'application/json',
//   })

//   if (fetchOptions.headers) {
//     new Headers(fetchOptions.headers).forEach((value, name) => {
//       headers.set(name, value)
//     })
//   }

//   if (token) {
//     headers.set('Authorization', `Bearer ${token}`)
//   }

//   // Make request
//   const response = await fetch(url.toString(), {
//     ...fetchOptions,
//     headers,
//   })

//   // Handle errors
//   if (!response.ok) {
//     const errorData = await response.json().catch(() => ({}))
//     throw new APIError(
//       response.status,
//       errorData.detail || response.statusText,
//       errorData
//     )
//   }

//   // Return parsed response
//   return response.json()
// }

// /**
//  * Auth API endpoints
//  */
// export const authAPI = {
//   register: async (name: string, email: string, password: string) => {
//     return apiRequest<AuthResponse>(
//       '/api/auth/register',
//       {
//         method: 'POST',
//         body: JSON.stringify({ name, email, password }),
//       }
//     )
//   },

//   login: async (email: string, password: string) => {
//     return apiRequest<AuthResponse>(
//       '/api/auth/login',
//       {
//         method: 'POST',
//         body: JSON.stringify({ email, password }),
//       }
//     )
//   },

//   refresh: async (refreshToken: string) => {
//     return apiRequest<{ access_token: string; refresh_token: string; token_type: string }>(
//       '/api/auth/refresh',
//       {
//         method: 'POST',
//         body: JSON.stringify({ refresh_token: refreshToken }),
//       }
//     )
//   },

//   verify: async () => {
//     return apiRequest<{ id: string; name: string; email: string; created_at: string }>(
//       '/api/auth/verify',
//       { method: 'POST' }
//     )
//   },

//   logout: async () => {
//     return apiRequest('/api/auth/logout', { method: 'POST' })
//   },
// }

// /**
//  * Drafts API endpoints
//  */
// export const draftsAPI = {
//   list: async () => {
//     return apiRequest('/api/drafts', { method: 'GET' })
//   },

//   create: async (data: { to: string; subject: string; body: string }) => {
//     return apiRequest('/api/drafts', {
//       method: 'POST',
//       body: JSON.stringify(data),
//     })
//   },

//   get: async (draftId: string) => {
//     return apiRequest(`/api/drafts/${draftId}`, { method: 'GET' })
//   },

//   update: async (draftId: string, data: Partial<{ to: string; subject: string; body: string }>) => {
//     return apiRequest(`/api/drafts/${draftId}`, {
//       method: 'PUT',
//       body: JSON.stringify(data),
//     })
//   },

//   delete: async (draftId: string) => {
//     return apiRequest(`/api/drafts/${draftId}`, { method: 'DELETE' })
//   },

//   send: async (draftId: string) => {
//     return apiRequest(`/api/drafts/${draftId}/send`, { method: 'POST' })
//   },
// }

// /**
//  * Inbox API endpoints
//  */
// export const inboxAPI = {
//   list: async (page = 1, limit = 20) => {
//     return apiRequest('/api/inbox', {
//       method: 'GET',
//       params: { page, limit },
//     })
//   },

//   get: async (emailId: string) => {
//     return apiRequest(`/api/emails/${emailId}`, { method: 'GET' })
//   },

//   delete: async (emailId: string) => {
//     return apiRequest(`/api/emails/${emailId}`, { method: 'DELETE' })
//   },

//   search: async (query: string) => {
//     return apiRequest('/api/search', {
//       method: 'GET',
//       params: { q: query },
//     })
//   },
// }

// /**
//  * Sent emails API endpoints
//  */
// export const sentAPI = {
//   list: async (page = 1, limit = 20) => {
//     return apiRequest('/api/sent', {
//       method: 'GET',
//       params: { page, limit },
//     })
//   },

//   get: async (emailId: string) => {
//     return apiRequest(`/api/emails/${emailId}`, { method: 'GET' })
//   },
// }

// /**
//  * Trash API endpoints
//  */
// export const trashAPI = {
//   list: async (page = 1, limit = 20) => {
//     return apiRequest('/api/trash', {
//       method: 'GET',
//       params: { page, limit },
//     })
//   },

//   delete: async (emailId: string) => {
//     return apiRequest(`/api/emails/${emailId}`, { method: 'DELETE' })
//   },
// }
