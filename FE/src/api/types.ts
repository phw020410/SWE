// 백엔드(BE/app/routers, BE/app/schemas.py) 응답 형식에 맞춘 타입

export type Role = 'USER' | 'ADMIN'

export interface User {
  userId: string
  email: string
  name: string
  role: Role
}

export interface LoginResponse {
  accessToken: string
  tokenType: string
  expiresIn: number // 초 단위
  user: User
}

export type ItemType = 'TRAINING' | 'JOB'
export type ItemSource = 'WORK24' | 'YOUTH_JOB'

/** 추천 항목. /api/query 응답의 items[] 와 /api/history 의 messages[].items[] 가 같은 필드를 쓴다. */
export interface RecommendedItem {
  id?: string
  message_id?: string
  item_type: ItemType
  source: ItemSource
  external_id: string
  title: string
  organization: string
  url: string | null
  region?: string
  published_at?: string | null
  starts_at?: string | null
  ends_at?: string | null
  raw_data?: Record<string, unknown>
  terms_url?: string
  date_basis?: string
}

export interface Source {
  source: ItemSource | 'UPLOAD'
  title: string
  url: string | null
}

export type QueryStatus = 'ok' | 'out_of_scope' | 'needs_clarification' | 'no_results' | string

export interface QueryResponse {
  conversationId: string
  messageId: string
  answer: string
  sources: Source[]
  status: QueryStatus
  items: RecommendedItem[]
  notices: string[]
}

export type ImageType = 'JOB_POSTING' | 'TRAINING'

export interface ImageQueryResponse {
  conversationId: string
  messageId: string
  imageType: ImageType
  extracted: Record<string, unknown>
  answer: string
  sources: Source[]
}

export interface HistoryMessage {
  messageId: string
  role: 'USER' | 'ASSISTANT'
  messageType: 'TEXT' | 'IMAGE'
  content: string
  createdAt: string
  items: RecommendedItem[]
  imageAnalysis: Record<string, unknown> | null
}

export interface Conversation {
  conversationId: string
  title: string | null
  createdAt: string
  updatedAt: string
  messages: HistoryMessage[]
}

export interface ApiErrorBody {
  code: string
  message: string
  requestId?: string
}
