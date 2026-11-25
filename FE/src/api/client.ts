import type { ApiErrorBody } from './types'

/** Vercel 환경변수 VITE_API_BASE_URL (예: https://swe-fastapi.onrender.com). 비밀 키는 FE에 두지 않는다. */
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'https://swe-towu.onrender.com').replace(/\/+$/, '')

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly requestId?: string

  constructor(status: number, code: string, message: string, requestId?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.requestId = requestId
  }
}

let accessToken: string | null = null
let unauthorizedHandler: (() => void) | null = null

export function setAccessToken(token: string | null) {
  accessToken = token
}

/** 보호 API에서 401이 오면 호출된다(토큰 만료·로그아웃된 토큰). */
export function setUnauthorizedHandler(handler: (() => void) | null) {
  unauthorizedHandler = handler
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  json?: unknown
  form?: FormData
  auth?: boolean
  signal?: AbortSignal
}

const FALLBACK_MESSAGES: Record<number, string> = {
  0: '서버에 연결할 수 없습니다. 인터넷 연결을 확인하거나 잠시 후 다시 시도해 주세요.',
  413: 'JPG, PNG(5MB 이하)만 가능합니다.',
  415: 'JPG, PNG(5MB 이하)만 가능합니다.',
  502: '교육·채용 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.',
  503: 'AI 요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.',
  504: '처리시간을 초과했습니다. 다시 시도해 주세요.',
}

async function send(path: string, options: RequestOptions): Promise<Response> {
  const { method = 'GET', json, form, auth = true, signal } = options
  const headers: Record<string, string> = {}
  if (json !== undefined) headers['Content-Type'] = 'application/json'
  if (auth && accessToken) headers.Authorization = `Bearer ${accessToken}`

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: form ?? (json !== undefined ? JSON.stringify(json) : undefined),
      signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError(0, 'NETWORK_ERROR', FALLBACK_MESSAGES[0])
  }

  if (!response.ok) {
    let body: Partial<ApiErrorBody> = {}
    try {
      body = await response.json()
    } catch {
      // 본문이 JSON이 아닌 경우(프록시 오류 등)
    }
    const error = new ApiError(
      response.status,
      body.code ?? `HTTP_${response.status}`,
      body.message ?? FALLBACK_MESSAGES[response.status] ?? '요청을 처리하지 못했습니다. 다시 시도해 주세요.',
      body.requestId ?? response.headers.get('X-Request-ID') ?? undefined,
    )
    if (response.status === 401 && auth && accessToken) unauthorizedHandler?.()
    throw error
  }
  return response
}

export async function requestJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await send(path, options)
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export async function requestText(path: string, options: RequestOptions = {}): Promise<{ text: string; filename: string | null }> {
  const response = await send(path, options)
  const disposition = response.headers.get('Content-Disposition') ?? ''
  const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposition)
  return { text: await response.text(), filename: match ? decodeURIComponent(match[1]) : null }
}
