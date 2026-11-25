import { requestJson, requestText } from './client'
import type { Conversation, ImageQueryResponse, LoginResponse, QueryResponse, User } from './types'

// API-005
export const signup = (body: { email: string; password: string; name: string }) =>
  requestJson<User>('/api/auth/signup', { method: 'POST', json: body, auth: false })

// API-006
export const login = (body: { email: string; password: string }) =>
  requestJson<LoginResponse>('/api/auth/login', { method: 'POST', json: body, auth: false })

// API-007
export const logout = () => requestJson<void>('/api/auth/logout', { method: 'POST' })

export const getMe = () => requestJson<User>('/api/users/me')

// API-008
export const updateMe = (body: { currentPassword: string; name?: string; newPassword?: string }) =>
  requestJson<User>('/api/users/me', { method: 'PATCH', json: body })

// API-001
export const sendQuery = (body: { query: string; conversationId: string | null; countPerType?: number }, signal?: AbortSignal) =>
  requestJson<QueryResponse>('/api/query', { method: 'POST', json: body, signal })

// API-002
export const sendImageQuery = (file: File, conversationId: string | null, signal?: AbortSignal) => {
  const form = new FormData()
  form.append('file', file)
  if (conversationId) form.append('conversationId', conversationId)
  return requestJson<ImageQueryResponse>('/api/image-query', { method: 'POST', form, signal })
}

// API-003
export const getHistory = (limit = 50, offset = 0) =>
  requestJson<Conversation[]>(`/api/history?limit=${limit}&offset=${offset}`)

// API-004
export const exportConversation = (conversationId: string) =>
  requestText(`/api/history/${encodeURIComponent(conversationId)}/export`)
